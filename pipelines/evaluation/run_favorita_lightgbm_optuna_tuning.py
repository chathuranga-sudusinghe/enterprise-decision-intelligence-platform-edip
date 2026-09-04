"""Manual WSL runner for the SCRUM-59 paired LightGBM Optuna study."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import optuna

from pipelines.evaluation.favorita_lightgbm_optuna import (
    EXPERIMENT_NAME,
    EXPERIMENT_VERSION,
    JIRA_ID,
    METRIC_NAMES,
    OPTUNA_SEED,
    SEARCH_SPACE,
    TRIAL_BUDGET,
    ComputeModeResolution,
    PairedTrialParameters,
    resolve_compute_mode,
    shared_trial_mae,
    suggest_parameters,
    validate_metric_profile,
    validate_paired_parameters,
    validate_tuning_contract,
)
from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
)
from pipelines.evaluation.run_favorita_lightgbm_evaluation import (
    FavoritaEvaluationRunConfig,
    run_evaluation,
    validate_evaluation_result_output_dir,
)
from pipelines.features.favorita_model_ready import resolve_feature_profile
from pipelines.runtime_paths import (
    artifact_path,
    favorita_source_path,
    resolve_cli_path,
)

DEFAULT_OUTPUT_DIR = Path("artifacts/tuning/favorita_scrum_59_lightgbm_optuna")
JSON_FILENAME = "scrum_59_lightgbm_optuna_tuning.json"
MARKDOWN_FILENAME = "scrum_59_lightgbm_optuna_tuning.md"
ARMS: tuple[str, ...] = ("contextual", "time-aware")


@dataclass(frozen=True, slots=True)
class TuningRunConfig:
    source_path: Path = field(default_factory=favorita_source_path)
    output_dir: Path = field(
        default_factory=lambda: artifact_path(
            "tuning/favorita_scrum_59_lightgbm_optuna"
        )
    )
    overwrite: bool = False


@dataclass(frozen=True, slots=True)
class TuningArtifactPaths:
    json: Path
    markdown: Path


ArmEvaluator = Callable[
    [str, PairedTrialParameters, ComputeModeResolution, Path], Mapping[str, Any]
]


def _artifact_paths(output_dir: Path) -> TuningArtifactPaths:
    return TuningArtifactPaths(
        json=output_dir / JSON_FILENAME,
        markdown=output_dir / MARKDOWN_FILENAME,
    )


def validate_tuning_config(config: TuningRunConfig) -> None:
    validate_tuning_contract()
    validate_evaluation_result_output_dir(config.output_dir)
    if not config.source_path.is_file():
        raise FileNotFoundError(config.source_path)
    if config.source_path.resolve() == config.output_dir.resolve():
        raise ValueError("source_path and output_dir must be distinct")
    paths = _artifact_paths(config.output_dir)
    if not config.overwrite:
        existing = [path for path in asdict(paths).values() if path.exists()]
        if existing:
            raise FileExistsError(existing[0])


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _default_arm_evaluator(
    feature_contract: str,
    parameters: PairedTrialParameters,
    compute: ComputeModeResolution,
    output_dir: Path,
    *,
    source_path: Path,
    overwrite: bool,
) -> Mapping[str, Any]:
    model_parameters = dict(parameters.model_parameters())
    model_parameters.update(compute.model_parameters)
    paths = run_evaluation(
        FavoritaEvaluationRunConfig(
            source_path=source_path,
            output_dir=output_dir,
            feature_contract=feature_contract,
            fold_output_dir=resolve_feature_profile(
                feature_contract
            ).canonical_artifact_root,
            model_parameters=model_parameters,
            num_boost_round=parameters.num_boost_round,
            overwrite=overwrite,
        )
    )
    manifest = _read_json(paths.run_manifest)
    return {
        "overall_metrics": _read_json(paths.overall_metrics),
        "fold_metrics": _read_json(paths.fold_metrics),
        "horizon_metrics": _read_json(paths.horizon_metrics),
        "evaluation_provenance": {
            "source": manifest["source"],
            "configuration": manifest["configuration"],
            "final_holdout": manifest["final_holdout"],
            "fold_artifact_root": manifest["namespace"]["fold_artifact_root"],
        },
    }


def _validate_arm_result(result: Mapping[str, Any]) -> None:
    overall = result.get("overall_metrics")
    folds = result.get("fold_metrics")
    horizons = result.get("horizon_metrics")
    if not isinstance(overall, Mapping):
        raise ValueError("Arm result must contain overall_metrics")
    validate_metric_profile(overall)
    if not isinstance(folds, list) or len(folds) != len(APPROVED_FOLDS):
        raise ValueError("Arm result must retain all four fold metric records")
    if not isinstance(horizons, list) or len(horizons) != len(FORECAST_HORIZONS):
        raise ValueError("Arm result must retain all 16 horizon metric records")
    for record in (*folds, *horizons):
        if not isinstance(record, Mapping):
            raise ValueError("Fold and horizon records must be mappings")
        validate_metric_profile({name: record[name] for name in METRIC_NAMES})


def _canonical_contract() -> dict[str, Any]:
    return {
        "target": "unit_sales",
        "validation": "four expanding-window folds; direct horizon-aware forecasts",
        "folds": [
            {
                "fold_id": fold.fold_id,
                "forecast_origin": fold.forecast_origin.isoformat(),
                "validation_start": fold.validation_start.isoformat(),
                "validation_end": fold.validation_end.isoformat(),
            }
            for fold in APPROVED_FOLDS
        ],
        "horizons": list(FORECAST_HORIZONS),
        "recursive_prediction_feedback": False,
        "random_split": False,
        "protected_holdout": {
            "forecast_origin": FINAL_HOLDOUT.forecast_origin.isoformat(),
            "holdout_start": FINAL_HOLDOUT.holdout_start.isoformat(),
            "holdout_end": FINAL_HOLDOUT.holdout_end.isoformat(),
            "touched": False,
            "statement": "The protected holdout was not loaded, scored, or selected against.",
        },
    }


def _jsonable_search_space() -> dict[str, dict[str, object]]:
    return {name: dict(specification) for name, specification in SEARCH_SPACE.items()}


def render_markdown(evidence: Mapping[str, Any]) -> str:
    """Generate human-readable evidence solely from the structured result."""

    trials = evidence["trials"]
    best = evidence["best_optuna_trial_by_shared_mae"]
    lines = [
        "# SCRUM-59 Shared LightGBM Optuna Tuning",
        "",
        "## Experiment Contract",
        "",
        f"- Trials: {evidence['trial_budget']} paired trials",
        "- Target: `unit_sales`",
        "- Validation: four canonical expanding-window folds, horizons 1 through 16",
        "- Objective: mean of Contextual overall MAE and Time-Aware overall MAE",
        "",
        "## Compute Mode",
        "",
        f"- Frozen mode: `{evidence['compute_mode']['mode']}`",
        f"- GPU smoke check: {evidence['compute_mode']['detail']}",
        "",
        "## Search Space",
        "",
        "```json",
        json.dumps(evidence["search_space"], indent=2, sort_keys=True),
        "```",
        "",
        "## Trial Results",
        "",
        "Optuna ranks trials only by shared MAE. All six overall metrics remain required evidence.",
        "",
        "| Trial | Arm | MAE | RMSE | WAPE | Bias | RMSLE | NWRMSLE | Shared MAE |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for trial in trials:
        for arm_label, arm_key in (
            ("Contextual", "contextual"),
            ("Time-Aware", "time_aware"),
        ):
            metrics = trial[arm_key]["overall_metrics"]
            lines.append(
                f"| {trial['trial_number']} | {arm_label} | "
                + " | ".join(f"{metrics[name]:.12g}" for name in METRIC_NAMES)
                + f" | {trial['shared_objective_mae']:.12g} |"
            )
    lines.extend(
        [
            "",
            "## Best Optuna Trial by Shared MAE",
            "",
            f"- Trial: {best['trial_number']}",
            f"- Shared MAE: {best['shared_objective_mae']:.12g}",
            f"- Primary-objective parameter configuration: `{json.dumps(best['parameters'], sort_keys=True)}`",
            "- This is the Optuna shared-MAE winner, not a final complete-profile model selection.",
        ]
    )
    for title, key in (
        ("Contextual Metric Profile", "contextual"),
        ("Time-Aware Metric Profile", "time_aware"),
    ):
        metrics = best[key]["overall_metrics"]
        lines.extend(
            [
                "",
                f"## {title}",
                "",
                "| Metric | Value |",
                "|---|---:|",
                *[f"| {name} | {metrics[name]:.12g} |" for name in METRIC_NAMES],
            ]
        )
    lines.extend(
        [
            "",
            "## Bias Evidence",
            "",
            "Bias is retained as signed mean prediction minus actual; closer to zero is better.",
            "",
            "## Research Interpretation",
            "",
            "Optuna identifies the primary-objective winner by shared MAE. MAE, RMSE, WAPE, RMSLE, NWRMSLE, and signed Bias must all be reviewed before final model-selection or research conclusions. SCRUM-19 performs the final research interpretation.",
            "",
            "## Protected Holdout",
            "",
            evidence["research_contract"]["protected_holdout"]["statement"],
            "",
            "## Limitations",
            "",
            "Only six paired trials and the five approved dimensions were evaluated. Results remain conditional on the canonical folds and frozen compute mode.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_artifacts(
    evidence: Mapping[str, Any], paths: TuningArtifactPaths, *, overwrite: bool
) -> None:
    paths.json.parent.mkdir(parents=True, exist_ok=True)
    payloads = {
        paths.json: json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        paths.markdown: render_markdown(evidence),
    }
    for path, content in payloads.items():
        if path.exists() and not overwrite:
            raise FileExistsError(path)
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            temporary.write_text(content, encoding="utf-8")
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def run_tuning(
    config: TuningRunConfig,
    *,
    evaluator: ArmEvaluator | None = None,
    compute_resolver: Callable[[], ComputeModeResolution] = resolve_compute_mode,
) -> TuningArtifactPaths:
    """Run exactly six serial paired trials after freezing compute once."""

    validate_tuning_config(config)
    compute = compute_resolver()
    evaluate = evaluator or (
        lambda arm, parameters, mode, output: _default_arm_evaluator(
            arm,
            parameters,
            mode,
            output,
            source_path=config.source_path,
            overwrite=config.overwrite,
        )
    )
    trial_records: list[dict[str, Any]] = []
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=OPTUNA_SEED),
    )

    def objective(trial: optuna.Trial) -> float:
        parameters = suggest_parameters(trial)
        validate_paired_parameters(parameters)
        results: dict[str, Mapping[str, Any]] = {}
        for arm in ARMS:
            config.output_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(
                prefix=f".trial-{trial.number}-{arm}-",
                dir=config.output_dir,
            ) as temporary_directory:
                results[arm] = evaluate(
                    arm,
                    parameters,
                    compute,
                    Path(temporary_directory),
                )
                _validate_arm_result(results[arm])
        objective_mae = shared_trial_mae(
            float(results["contextual"]["overall_metrics"]["mae"]),
            float(results["time-aware"]["overall_metrics"]["mae"]),
        )
        trial_records.append(
            {
                "trial_number": trial.number,
                "parameters": parameters.as_dict(),
                "contextual": dict(results["contextual"]),
                "time_aware": dict(results["time-aware"]),
                "shared_objective_mae": objective_mae,
            }
        )
        return objective_mae

    study.optimize(objective, n_trials=TRIAL_BUDGET)
    best_record = next(
        record
        for record in trial_records
        if record["trial_number"] == study.best_trial.number
    )
    evidence = {
        "jira_id": JIRA_ID,
        "experiment_name": EXPERIMENT_NAME,
        "experiment_version": EXPERIMENT_VERSION,
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "trial_budget": TRIAL_BUDGET,
        "seed": OPTUNA_SEED,
        "search_space": _jsonable_search_space(),
        "research_contract": _canonical_contract(),
        "compute_mode": {
            "mode": compute.mode,
            "model_parameters": dict(compute.model_parameters),
            "gpu_smoke_check_succeeded": compute.gpu_smoke_check_succeeded,
            "detail": compute.detail,
            "resolved_once": True,
            "shared_by_both_arms": True,
        },
        "metric_names": list(METRIC_NAMES),
        "trials": trial_records,
        "best_optuna_trial_by_shared_mae": best_record,
        "best_optuna_parameter_configuration_by_shared_mae": best_record[
            "parameters"
        ],
        "holdout_touched": False,
    }
    paths = _artifact_paths(config.output_dir)
    _write_artifacts(evidence, paths, overwrite=config.overwrite)
    return paths


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-path", type=resolve_cli_path, default=favorita_source_path()
    )
    parser.add_argument(
        "--output-dir",
        type=resolve_cli_path,
        default=artifact_path("tuning/favorita_scrum_59_lightgbm_optuna"),
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    paths = run_tuning(
        TuningRunConfig(
            source_path=args.source_path,
            output_dir=args.output_dir,
            overwrite=args.overwrite,
        )
    )
    print(paths.json.as_posix())
    print(paths.markdown.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
