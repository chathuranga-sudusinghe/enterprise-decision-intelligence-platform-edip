"""Evaluate empirical uncertainty using retained frozen-candidate predictions."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path
from typing import Any, cast

import pandas as pd

from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
)
from pipelines.evaluation.favorita_uncertainty import (
    NOMINAL_COVERAGE,
    PREDICTION_KEYS,
    interval_metrics,
    sequential_intervals,
)
from pipelines.evaluation.run_favorita_selected_candidate_backtesting import (
    CANDIDATE_ID,
    ISSUE_NUMBER,
    PROVENANCE_SOURCE_PATHS,
    RUNTIME_PACKAGES,
    code_provenance,
    frozen_parameters,
    runtime_versions,
    sha256_file,
    write_json,
)
from pipelines.models.favorita_lightgbm import resolve_feature_contract
from pipelines.models.favorita_model_bundle import FROZEN_NUM_BOOST_ROUND
from pipelines.runtime_paths import artifact_path, resolve_cli_path


def _validate_producer_provenance(selected: dict[str, Any]) -> None:
    """Validate saved producer identity, without substituting current code hashes."""
    code = selected["code"]
    versions = selected["runtime_versions"]
    if not isinstance(code, dict) or not isinstance(versions, dict):
        raise ValueError("Malformed producer provenance")
    commit = code["git_commit"]
    hashes = code["source_sha256"]
    if (
        not isinstance(commit, str)
        or re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", commit) is None
        or type(code["working_tree_dirty"]) is not bool
        or not isinstance(hashes, dict)
    ):
        raise ValueError("Malformed producer code provenance")
    for name in PROVENANCE_SOURCE_PATHS:
        digest = hashes[name]
        if not isinstance(digest, str) or re.fullmatch(r"[a-f0-9]{64}", digest) is None:
            raise ValueError("Malformed producer source hash provenance")
    for name in ("python", *RUNTIME_PACKAGES):
        value = versions[name]
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Malformed producer runtime provenance")


def validate_provenance(manifest: dict[str, Any], prediction_path: Path) -> None:
    """Fail closed on incomplete, untuned, contextual, or altered evidence."""
    try:
        selected = manifest["selected_candidate"]
        config = manifest["configuration"]
        if (
            selected["schema_version"] != 2
            or selected["status"] != "completed"
            or selected["candidate_id"] != CANDIDATE_ID
            or selected["issue_number"] != ISSUE_NUMBER
            or selected["retuned"] is not False
            or selected["model_replaced"] is not False
            or selected["prediction_keys"] != list(PREDICTION_KEYS)
        ):
            raise ValueError("Selected candidate provenance mismatch")
        _validate_producer_provenance(selected)
        if manifest["run"]["status"] != "completed":
            raise ValueError("Incomplete selected-candidate run")
        if (
            config["feature_contract"] != "time-aware"
            or config["model_parameters"] != frozen_parameters()
            or config["num_boost_round"] != FROZEN_NUM_BOOST_ROUND
            or config["hyperparameter_tuning"] is not False
            or config["candidate_feature_columns"]
            != list(resolve_feature_contract("time-aware"))
            or config["forecast_horizons"] != list(FORECAST_HORIZONS)
            or config["recursive_feedback"] is not False
            or config["future_promotion_assumption"] is not False
            or config["future_holiday_assumption"] is not False
        ):
            raise ValueError("Frozen model configuration provenance mismatch")
        holdout = manifest["final_holdout"]
        if (
            holdout["scored"] is not False
            or holdout["materialized"] is not False
            or holdout["holdout_start"] != FINAL_HOLDOUT.holdout_start.isoformat()
            or holdout["holdout_end"] != FINAL_HOLDOUT.holdout_end.isoformat()
        ):
            raise ValueError("Protected holdout provenance mismatch")
        consumption = manifest["fold_artifact_consumption"]
        if (
            consumption["mode"] != "consumption-only"
            or consumption["fold_artifacts_mutated"] is not False
        ):
            raise ValueError("Persisted fold consumption provenance mismatch")
        folds = manifest["folds"]
        if len(folds) != len(APPROVED_FOLDS):
            raise ValueError("Four canonical fold manifests are required")
        count = manifest["evaluation"]["prediction_rows"]
        if type(count) is not int or count <= 0:
            raise ValueError("Invalid prediction row count provenance")
        for expected, recorded in zip(APPROVED_FOLDS, folds, strict=True):
            if (
                recorded["fold_id"] != expected.fold_id
                or recorded["forecast_origin"] != expected.forecast_origin.isoformat()
                or recorded["validation_start"] != expected.validation_start.isoformat()
                or recorded["validation_end"] != expected.validation_end.isoformat()
                or recorded["feature_contract"] != "time-aware"
                or recorded["model_parameters"] != frozen_parameters()
                or recorded["num_boost_round"] != FROZEN_NUM_BOOST_ROUND
                or type(recorded["validation_rows"]) is not int
                or recorded["validation_rows"] <= 0
            ):
                raise ValueError("Fold provenance mismatch")
        digest = selected["predictions_sha256"]
        if (
            not isinstance(digest, str)
            or re.fullmatch(r"[a-f0-9]{64}", digest) is None
            or digest != sha256_file(prediction_path)
        ):
            raise ValueError("Prediction checksum provenance mismatch")
    except (KeyError, TypeError) as exc:
        raise ValueError("Missing or malformed selected-candidate provenance") from exc


def _metrics(rows: pd.DataFrame) -> dict[str, Any]:
    return interval_metrics(
        rows["actual_unit_sales"], rows["lower_bound"], rows["upper_bound"]
    )


def run_uncertainty(*, input_dir: Path, output_dir: Path) -> Path:
    input_dir, output_dir = map(resolve_cli_path, (input_dir, output_dir))
    if output_dir.exists():
        raise FileExistsError(f"Refusing existing output directory: {output_dir}")
    if input_dir in output_dir.parents or output_dir in input_dir.parents:
        raise ValueError("Input and output artifact directories must not overlap")
    manifest_path = input_dir / "run_manifest.json"
    prediction_path = input_dir / "predictions.parquet"
    manifest_hash = sha256_file(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_provenance(manifest, prediction_path)
    consumer_code = code_provenance()
    frame = pd.read_parquet(prediction_path)
    intervals, calibration = sequential_intervals(frame)
    if len(frame) != manifest["evaluation"]["prediction_rows"]:
        raise ValueError("Prediction row count provenance mismatch")
    for fold in manifest["folds"]:
        if int(frame["fold_id"].eq(fold["fold_id"]).sum()) != fold["validation_rows"]:
            raise ValueError("Fold row count provenance mismatch")
    if (
        sha256_file(manifest_path) != manifest_hash
        or sha256_file(prediction_path)
        != manifest["selected_candidate"]["predictions_sha256"]
    ):
        raise ValueError("Input artifacts changed while evaluating uncertainty")
    del frame
    overall = _metrics(intervals)
    folds = [
        {"fold_id": int(cast(int, key)), **_metrics(rows)}
        for key, rows in intervals.groupby("fold_id", sort=True)
    ]
    horizons = [
        {"forecast_horizon": int(cast(int, key)), **_metrics(rows)}
        for key, rows in intervals.groupby("forecast_horizon", sort=True)
    ]
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".favorita-uncertainty-", dir=output_dir.parent
    ) as temporary:
        stage = Path(temporary)
        intervals.to_parquet(stage / "predictions.parquet", index=False)
        for filename, payload in (
            ("calibration.json", calibration),
            ("overall_metrics.json", overall),
            ("fold_metrics.json", folds),
            ("horizon_metrics.json", horizons),
        ):
            write_json(stage / filename, payload)
        summary = [
            "# Forecast Uncertainty — GitHub Issue #128",
            "",
            f"Nominal coverage: {NOMINAL_COVERAGE:.0%}; quantile method: linear.",
            "Fold 1 is calibration warm-up only. Evaluation covers folds 2–4.",
            f"Evaluated rows: {overall['row_count']}; PICP: {overall['picp']:.6%}; MPIW: {overall['mpiw']:.8f} sales units.",
            "",
            "| Fold | Rows | PICP | MPIW |",
            "|---|---:|---:|---:|",
            *[
                f"| {r['fold_id']} | {r['row_count']} | {r['picp']:.6%} | {r['mpiw']:.8f} |"
                for r in folds
            ],
            "",
            "| Horizon | Rows | PICP | MPIW |",
            "|---|---:|---:|---:|",
            *[
                f"| {r['forecast_horizon']} | {r['row_count']} | {r['picp']:.6%} | {r['mpiw']:.8f} |"
                for r in horizons
            ],
            "",
            "## Interpretation and limitations",
            "",
            "0.90 denotes nominal coverage, not a categorical confidence rating or guaranteed coverage.",
            "Residuals use max(actual, 0) - max(prediction, 0); both interval bounds are clipped at zero.",
            "Calibration uses only earlier folds; final four-fold calibration is not independently evaluated.",
            "Global pooling masks heterogeneity and relies on temporal stability of errors.",
            "The model was selected using these folds: results are development evidence, not an untouched final assessment.",
            "Observed sales do not reveal unmet demand or stockout-censored demand. Returns are mapped to zero demand.",
            "No protected holdout data were consumed. No risk or replenishment decisions are implemented.",
        ]
        (stage / "evaluation_summary.md").write_text(
            "\n".join(summary) + "\n", encoding="utf-8"
        )
        if code_provenance() != consumer_code:
            raise ValueError(
                "Consumer source code changed during uncertainty evaluation"
            )
        evidence = {
            "schema_version": 1,
            "issue_number": ISSUE_NUMBER,
            "historical_planning_label": "SCRUM-21",
            "status": "completed",
            "candidate_id": CANDIDATE_ID,
            "nominal_coverage": NOMINAL_COVERAGE,
            "quantile_method": "linear",
            "evaluated_folds": [2, 3, 4],
            "warmup_fold": 1,
            "input": {
                "directory": str(input_dir),
                "manifest_sha256": manifest_hash,
                "predictions_sha256": manifest["selected_candidate"][
                    "predictions_sha256"
                ],
                "producer_code": manifest["selected_candidate"]["code"],
                "producer_runtime_versions": manifest["selected_candidate"][
                    "runtime_versions"
                ],
            },
            "frozen_model_parameters": frozen_parameters(),
            "num_boost_round": FROZEN_NUM_BOOST_ROUND,
            "holdout_touched": False,
            "evaluation_rows": len(intervals),
            "calibration_rows": calibration["final_calibration"]["residual_count"],
            "code": consumer_code,
            "runtime_versions": runtime_versions(),
            "artifacts_sha256": {
                p.name: sha256_file(p) for p in sorted(stage.iterdir())
            },
        }
        write_json(stage / "run_manifest.json", evidence)
        # Exclusive reservation also prevents two concurrent runs from publishing
        # over one another. The completion manifest is always published last.
        output_dir.mkdir(exist_ok=False)
        for path in sorted(
            stage.iterdir(), key=lambda p: (p.name == "run_manifest.json", p.name)
        ):
            path.rename(output_dir / path.name)
    return output_dir / "run_manifest.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=resolve_cli_path,
        default=artifact_path("evaluation/favorita_selected_candidate"),
    )
    parser.add_argument(
        "--output-dir",
        type=resolve_cli_path,
        default=artifact_path("evaluation/favorita_uncertainty"),
    )
    args = parser.parse_args(argv)
    print(run_uncertainty(input_dir=args.input_dir, output_dir=args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
