"""Run the one-time SCRUM-19 final Favorita holdout evaluation."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pandas as pd

from pipelines.evaluation.favorita_metrics import (
    FavoritaMetricAccumulator,
    ForecastMetricResults,
)
from pipelines.evaluation.favorita_temporal_validation import (
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
    MODELING_TARGET_START,
    TemporalValidationFold,
    validate_holdout_contract,
)
from pipelines.evaluation.run_favorita_lightgbm_evaluation import (
    DEFAULT_SOURCE_PATH,
    _stream_fold_validation,
    _StreamingPredictionWriter,
    _validate_direct_horizon_batch,
    _ValidationKeyTracker,
    validate_evaluation_result_output_dir,
)
from pipelines.features.build_favorita_fold_datasets import (
    ALL_STORE_BATCHES,
    _artifact_footer_validation,
    derive_training_origins,
)
from pipelines.features.favorita_model_ready import (
    FeatureBuildConfig,
    materialize_feature_dataset,
    source_footer,
    write_json_atomic,
)
from pipelines.models.favorita_lightgbm import (
    LIGHTGBM_PARAMETERS,
    FavoritaLightGBMAdapter,
    resolve_feature_contract,
)

JIRA_ID = "SCRUM-19"
EXPERIMENT_NAME = "Final forecasting research evidence"
PARAMETER_SOURCE = "SCRUM-59 Trial 0 frozen configuration"
DEFAULT_OUTPUT_DIR = Path(
    "artifacts/evaluation/favorita_scrum_19_final_holdout"
)
JSON_FILENAME = "scrum_19_final_holdout.json"
MARKDOWN_FILENAME = "scrum_19_final_holdout.md"
ARMS: tuple[str, ...] = ("contextual", "time-aware")
METRIC_NAMES: tuple[str, ...] = (
    "mae",
    "rmse",
    "wape",
    "bias",
    "rmsle",
    "nwrmsle",
)
FROZEN_MODEL_PARAMETERS: Mapping[str, object] = MappingProxyType(
    {
        "learning_rate": 0.02757359293934948,
        "num_leaves": 123,
        "min_data_in_leaf": 89,
        "feature_fraction": 0.8394633936788146,
    }
)
FROZEN_NUM_BOOST_ROUND = 150
FINAL_HOLDOUT_WINDOW = TemporalValidationFold(
    fold_id=5,
    forecast_origin=FINAL_HOLDOUT.forecast_origin,
    validation_start=FINAL_HOLDOUT.holdout_start,
    validation_end=FINAL_HOLDOUT.holdout_end,
)


@dataclass(frozen=True, slots=True)
class FinalHoldoutRunConfig:
    source_path: Path = DEFAULT_SOURCE_PATH
    output_dir: Path = DEFAULT_OUTPUT_DIR
    overwrite: bool = False


@dataclass(frozen=True, slots=True)
class FinalHoldoutArtifactPaths:
    json: Path
    markdown: Path


@dataclass(frozen=True, slots=True)
class ArmDatasetPaths:
    training: Path
    validation: Path


Materializer = Callable[..., dict[str, Any]]
BoundaryReader = Callable[..., dict[str, Any]]
AdapterFactory = Callable[..., FavoritaLightGBMAdapter]
StreamEvaluator = Callable[..., Any]


def _artifact_paths(output_dir: Path) -> FinalHoldoutArtifactPaths:
    return FinalHoldoutArtifactPaths(
        json=output_dir / JSON_FILENAME,
        markdown=output_dir / MARKDOWN_FILENAME,
    )


def _source_state(path: Path) -> dict[str, object]:
    state = path.stat()
    return {
        "path": path.resolve().as_posix(),
        "size_bytes": state.st_size,
        "mtime_ns": state.st_mtime_ns,
    }


def validate_final_holdout_config(config: FinalHoldoutRunConfig) -> None:
    validate_holdout_contract()
    validate_evaluation_result_output_dir(config.output_dir)
    if not config.source_path.is_file():
        raise FileNotFoundError(config.source_path)
    if config.source_path.resolve() == config.output_dir.resolve():
        raise ValueError("source_path and output_dir must be distinct")
    if FINAL_HOLDOUT_WINDOW.forecast_origin != date(2017, 7, 30):
        raise ValueError("SCRUM-19 forecast origin must be 2017-07-30")
    if FINAL_HOLDOUT_WINDOW.validation_start != date(2017, 7, 31):
        raise ValueError("SCRUM-19 holdout must start on 2017-07-31")
    if FINAL_HOLDOUT_WINDOW.validation_end != date(2017, 8, 15):
        raise ValueError("SCRUM-19 holdout must end on 2017-08-15")
    if FORECAST_HORIZONS != tuple(range(1, 17)):
        raise ValueError("SCRUM-19 horizons must be exactly 1 through 16")
    if tuple(FROZEN_MODEL_PARAMETERS) != (
        "learning_rate",
        "num_leaves",
        "min_data_in_leaf",
        "feature_fraction",
    ) or FROZEN_NUM_BOOST_ROUND != 150:
        raise ValueError("SCRUM-19 frozen Trial 0 parameters changed")
    if not config.overwrite:
        for path in asdict(_artifact_paths(config.output_dir)).values():
            candidate = Path(path)
            if candidate.exists():
                raise FileExistsError(candidate)


def _training_origins() -> tuple[date, ...]:
    origins = derive_training_origins(
        MODELING_TARGET_START - timedelta(days=1),
        FINAL_HOLDOUT_WINDOW,
    )
    if not origins or max(origins) >= FINAL_HOLDOUT.forecast_origin:
        raise ValueError("All training origins must precede the final holdout origin")
    return origins


def _build_config(
    config: FinalHoldoutRunConfig,
    *,
    feature_profile: str,
    output_path: Path,
    forecast_origins: tuple[date, ...],
) -> FeatureBuildConfig:
    return FeatureBuildConfig(
        source_path=config.source_path,
        output_path=output_path,
        manifest_path=output_path.with_suffix(".manifest.json"),
        forecast_origins=forecast_origins,
        store_batches=ALL_STORE_BATCHES,
        feature_profile=feature_profile,
        max_items_per_store=None,
        allow_assumed_future_promotion=False,
        allow_assumed_future_holidays=False,
        overwrite=False,
    )


def _materialize_arm(
    config: FinalHoldoutRunConfig,
    *,
    arm: str,
    root: Path,
    materializer: Materializer,
    boundary_reader: BoundaryReader,
) -> tuple[ArmDatasetPaths, dict[str, Any]]:
    arm_root = root / arm
    paths = ArmDatasetPaths(
        training=arm_root / "training.parquet",
        validation=arm_root / "validation.parquet",
    )
    training = materializer(
        _build_config(
            config,
            feature_profile=arm,
            output_path=paths.training,
            forecast_origins=_training_origins(),
        ),
        forecast_date_cutoff=FINAL_HOLDOUT.forecast_origin,
        drop_targets_without_origin_history=True,
        bounded_memory_validation=True,
        reuse_source_across_origins=True,
        progress_prefix=f"[{arm}]",
        progress_phase="training",
    )
    validation = materializer(
        _build_config(
            config,
            feature_profile=arm,
            output_path=paths.validation,
            forecast_origins=(FINAL_HOLDOUT.forecast_origin,),
        ),
        drop_targets_without_origin_history=True,
        bounded_memory_validation=True,
        reuse_source_across_origins=True,
        progress_prefix=f"[{arm}]",
        progress_phase="holdout",
    )
    evidence = {
        "training": {
            "artifact_validation": training["artifact_validation"],
            "footer_boundaries": boundary_reader(
                paths.training,
                feature_profile=arm,
            ),
        },
        "validation": {
            "artifact_validation": validation["artifact_validation"],
            "footer_boundaries": boundary_reader(
                paths.validation,
                feature_profile=arm,
            ),
        },
    }
    _validate_materialized_boundaries(evidence)
    return paths, evidence


def _validate_materialized_boundaries(evidence: Mapping[str, Any]) -> None:
    training_artifact = evidence["training"]["artifact_validation"]
    training = evidence["training"]["footer_boundaries"]
    validation_artifact = evidence["validation"]["artifact_validation"]
    validation = evidence["validation"]["footer_boundaries"]
    for artifact, boundaries, partition in (
        (training_artifact, training, "Training"),
        (validation_artifact, validation, "Holdout validation"),
    ):
        if artifact["rows"] != boundaries["rows"]:
            raise ValueError(f"{partition} row counts differ between validations")
        for key in ("forecast_date_min", "forecast_date_max", "horizons"):
            if artifact[key] != boundaries[key]:
                raise ValueError(
                    f"{partition} {key} differs between artifact and footer evidence"
                )
    if training["forecast_date_max"] != FINAL_HOLDOUT.forecast_origin.isoformat():
        raise ValueError("Training targets must end at 2017-07-30")
    if training["forecast_origin_max"] >= FINAL_HOLDOUT.forecast_origin.isoformat():
        raise ValueError("Training origins must precede 2017-07-30")
    expected_validation = {
        "forecast_origin_min": FINAL_HOLDOUT.forecast_origin.isoformat(),
        "forecast_origin_max": FINAL_HOLDOUT.forecast_origin.isoformat(),
        "forecast_date_min": FINAL_HOLDOUT.holdout_start.isoformat(),
        "forecast_date_max": FINAL_HOLDOUT.holdout_end.isoformat(),
        "horizons": list(FORECAST_HORIZONS),
    }
    for key, expected in expected_validation.items():
        if validation.get(key) != expected:
            raise ValueError(f"Holdout validation {key} must equal {expected!r}")


def _verify_cross_arm_rows(dataset_evidence: Mapping[str, Mapping[str, Any]]) -> str:
    digests = {
        arm: evidence["validation"]["artifact_validation"][
            "row_key_target_sha256"
        ]
        for arm, evidence in dataset_evidence.items()
    }
    if len(set(digests.values())) != 1:
        raise ValueError(
            "Contextual and Time-Aware holdout row/target digests must match"
        )
    return next(iter(digests.values()))


def _validate_final_holdout_batch(
    fold: TemporalValidationFold,
    frame: pd.DataFrame,
    key_tracker: _ValidationKeyTracker,
    *,
    feature_profile: str,
) -> None:
    if fold != FINAL_HOLDOUT_WINDOW:
        raise ValueError("SCRUM-19 may score only the exact final holdout window")
    _validate_direct_horizon_batch(
        fold,
        frame,
        key_tracker,
        feature_profile=feature_profile,
    )


def _metric_record(metrics: ForecastMetricResults) -> dict[str, float]:
    values = asdict(metrics)
    return {name: float(values[name]) for name in METRIC_NAMES}


def _evaluate_arm(
    *,
    arm: str,
    paths: ArmDatasetPaths,
    root: Path,
    adapter_factory: AdapterFactory,
    stream_evaluator: StreamEvaluator,
) -> dict[str, Any]:
    model = adapter_factory(
        feature_columns=resolve_feature_contract(arm),
        model_parameters=FROZEN_MODEL_PARAMETERS,
        num_boost_round=FROZEN_NUM_BOOST_ROUND,
    )
    model.fit_parquet(paths.training)
    writer = _StreamingPredictionWriter(root / arm / "predictions.parquet")
    overall = FavoritaMetricAccumulator()
    horizons = {
        horizon: FavoritaMetricAccumulator() for horizon in FORECAST_HORIZONS
    }
    try:
        result = stream_evaluator(
            fold=FINAL_HOLDOUT_WINDOW,
            training_path=paths.training,
            validation_path=paths.validation,
            model=model,
            prediction_writer=writer,
            overall_accumulator=overall,
            horizon_accumulators=horizons,
            validation_batch_validator=_validate_final_holdout_batch,
        )
        writer.close()
    except Exception:
        writer.abort()
        raise
    model_evidence = dict(result.model_evidence)
    model_evidence.pop("training_artifact", None)
    model_evidence.pop("validation_artifact", None)
    model_evidence["temporary_evaluation_artifacts_retained"] = False
    return {
        "feature_contract": arm,
        "row_count": result.row_count,
        "overall_metrics": _metric_record(overall.finalize()),
        "horizon_metrics": [
            {
                "forecast_horizon": horizon,
                "row_count": horizons[horizon].count,
                **_metric_record(horizons[horizon].finalize()),
            }
            for horizon in FORECAST_HORIZONS
        ],
        "model_evidence": model_evidence,
    }


def _metric_comparison(arms: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    comparison: dict[str, Any] = {}
    for metric in METRIC_NAMES:
        contextual = float(arms["contextual"]["overall_metrics"][metric])
        time_aware = float(arms["time-aware"]["overall_metrics"][metric])
        contextual_score = abs(contextual) if metric == "bias" else contextual
        time_aware_score = abs(time_aware) if metric == "bias" else time_aware
        if contextual_score == time_aware_score:
            better_arm = "tie"
        elif contextual_score < time_aware_score:
            better_arm = "contextual"
        else:
            better_arm = "time-aware"
        comparison[metric] = {
            "contextual": contextual,
            "time_aware": time_aware,
            "contextual_minus_time_aware": contextual - time_aware,
            "comparison_basis": (
                "closer to zero" if metric == "bias" else "lower is better"
            ),
            "better_arm": better_arm,
        }
    return comparison


def render_markdown(evidence: Mapping[str, Any]) -> str:
    lines = [
        "# SCRUM-19 Final Forecasting Research Evidence",
        "",
        "## Final Holdout Contract",
        "",
        f"- Forecast origin: `{evidence['holdout_contract']['forecast_origin']}`",
        f"- Holdout dates: `{evidence['holdout_contract']['holdout_start']}` through `{evidence['holdout_contract']['holdout_end']}`",
        "- Horizons: 1 through 16",
        "- This is the final protected-holdout evaluation.",
        "",
        "## Frozen Model Configuration",
        "",
        f"- Source: {evidence['parameter_source']}",
        f"- Parameters: `{json.dumps(evidence['frozen_model_configuration']['model_parameters'], sort_keys=True)}`",
        f"- Boost rounds: {evidence['frozen_model_configuration']['num_boost_round']}",
        "- Tuning performed: No",
        "- Optuna invoked: No",
        "",
        "## Overall Metrics",
        "",
        "| Arm | Rows | MAE | RMSE | WAPE | Bias | RMSLE | NWRMSLE |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, label in (("contextual", "Contextual"), ("time-aware", "Time-Aware")):
        result = evidence["arms"][arm]
        metrics = result["overall_metrics"]
        lines.append(
            f"| {label} | {result['row_count']} | "
            + " | ".join(f"{metrics[name]:.12g}" for name in METRIC_NAMES)
            + " |"
        )
    lines.extend(
        [
            "",
            "## Metric-by-Metric Comparison",
            "",
            "| Metric | Contextual | Time-Aware | Better arm | Basis |",
            "|---|---:|---:|---|---|",
        ]
    )
    for metric in METRIC_NAMES:
        record = evidence["metric_comparison"][metric]
        lines.append(
            f"| {metric.upper()} | {record['contextual']:.12g} | "
            f"{record['time_aware']:.12g} | {record['better_arm']} | "
            f"{record['comparison_basis']} |"
        )
    lines.extend(
        [
            "",
            "## Research Interpretation",
            "",
            "This report summarizes final holdout evidence but does not automatically conclude H0 or H1. Final interpretation belongs to the SCRUM-19 research review.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_text_atomic(text: str, path: Path, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def run_final_holdout(
    config: FinalHoldoutRunConfig,
    *,
    materializer: Materializer = materialize_feature_dataset,
    boundary_reader: BoundaryReader = _artifact_footer_validation,
    adapter_factory: AdapterFactory = FavoritaLightGBMAdapter,
    stream_evaluator: StreamEvaluator = _stream_fold_validation,
) -> FinalHoldoutArtifactPaths:
    """Materialize, evaluate, and publish the frozen two-arm final holdout once."""

    validate_final_holdout_config(config)
    source_before = _source_state(config.source_path)
    footer_before = source_footer(config.source_path)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".scrum-19-final-holdout-", dir=config.output_dir
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        dataset_paths: dict[str, ArmDatasetPaths] = {}
        dataset_evidence: dict[str, dict[str, Any]] = {}
        for arm in ARMS:
            dataset_paths[arm], dataset_evidence[arm] = _materialize_arm(
                config,
                arm=arm,
                root=temporary_root,
                materializer=materializer,
                boundary_reader=boundary_reader,
            )
        shared_digest = _verify_cross_arm_rows(dataset_evidence)
        arm_results = {
            arm: _evaluate_arm(
                arm=arm,
                paths=dataset_paths[arm],
                root=temporary_root,
                adapter_factory=adapter_factory,
                stream_evaluator=stream_evaluator,
            )
            for arm in ARMS
        }
        effective_parameters = {
            arm: arm_results[arm]["model_evidence"]["model_parameters"]
            for arm in ARMS
        }
        effective_rounds = {
            arm: arm_results[arm]["model_evidence"]["num_boost_round"]
            for arm in ARMS
        }
        expected_effective_parameters = dict(LIGHTGBM_PARAMETERS)
        expected_effective_parameters.update(FROZEN_MODEL_PARAMETERS)
        if any(
            parameters != expected_effective_parameters
            for parameters in effective_parameters.values()
        ):
            raise ValueError(
                "Effective model parameters must match the frozen Trial 0 contract"
            )
        if set(effective_rounds.values()) != {FROZEN_NUM_BOOST_ROUND}:
            raise ValueError("Effective num_boost_round differs across final arms")

    source_after = _source_state(config.source_path)
    footer_after = source_footer(config.source_path)
    if source_after != source_before or footer_after != footer_before:
        raise AssertionError("Cleaned source changed during final holdout evaluation")
    evidence = {
        "jira_id": JIRA_ID,
        "experiment_name": EXPERIMENT_NAME,
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_scope": "final protected holdout",
        "holdout_contract": {
            "forecast_origin": FINAL_HOLDOUT.forecast_origin.isoformat(),
            "holdout_start": FINAL_HOLDOUT.holdout_start.isoformat(),
            "holdout_end": FINAL_HOLDOUT.holdout_end.isoformat(),
            "horizons": list(FORECAST_HORIZONS),
        },
        "parameter_source": PARAMETER_SOURCE,
        "frozen_model_configuration": {
            "model_parameters": dict(FROZEN_MODEL_PARAMETERS),
            "num_boost_round": FROZEN_NUM_BOOST_ROUND,
        },
        "tuning_performed": False,
        "optuna_invoked": False,
        "additional_trials": 0,
        "same_effective_model_parameters_verified": True,
        "same_num_boost_round_verified": True,
        "cross_arm_validation_row_target_digest_verified": True,
        "cross_arm_validation_row_target_sha256": shared_digest,
        "source_integrity": {
            "before": source_before,
            "after": source_after,
            "footer_before": footer_before,
            "footer_after": footer_after,
            "unchanged": True,
        },
        "dataset_evidence": dataset_evidence,
        "arms": arm_results,
        "metric_comparison": _metric_comparison(arm_results),
        "hypothesis_conclusion": None,
        "hypothesis_note": "H0/H1 interpretation belongs to SCRUM-19 research review.",
    }
    paths = _artifact_paths(config.output_dir)
    write_json_atomic(evidence, paths.json, overwrite=config.overwrite)
    _write_text_atomic(
        render_markdown(evidence), paths.markdown, overwrite=config.overwrite
    )
    return paths


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-path", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    paths = run_final_holdout(
        FinalHoldoutRunConfig(
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
