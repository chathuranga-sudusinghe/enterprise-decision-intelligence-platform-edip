"""Run one existing full-history Favorita LightGBM validation fold."""

from __future__ import annotations

import argparse
import json
import os
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import pyarrow.parquet as pq

from pipelines.evaluation.favorita_metrics import FavoritaMetricAccumulator
from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
    MODELING_TARGET_START,
    TemporalValidationFold,
    validate_approved_contract,
)
from pipelines.evaluation.run_favorita_lightgbm_evaluation import (
    _ValidationKeyTracker,
    _validate_validation_batch,
    iter_model_ready_validation_batches,
)
from pipelines.features.build_favorita_fold_datasets import (
    ALL_FAVORITA_STORES,
    CANONICAL_FOLD_IDS,
    CANONICAL_VALIDATION_DESIGN,
    DEFAULT_OUTPUT_DIR as DEFAULT_FOLD_OUTPUT_DIR,
    EXECUTION_SCOPE,
    FoldArtifactPaths,
    approved_fold_artifact_paths,
    canonical_training_origins,
    validate_canonical_fold_output_dir,
)
from pipelines.features.favorita_model_ready import (
    OUTPUT_ARROW_SCHEMA,
    TRAINING_OUTPUT_COLUMNS,
    write_json_atomic,
)
from pipelines.models.favorita_lightgbm import FavoritaLightGBMAdapter

DEFAULT_OUTPUT_DIR = Path("artifacts/evaluation/favorita_lightgbm")
EXPERIMENT_RESULTS_FILENAME = "experiment_results.json"
MARKDOWN_SUMMARY_FILENAME = "lightgbm_evaluation_summary.md"
EXPERIMENT_NAME = "Favorita SCRUM-15 canonical four-fold expanding-window evaluation"
MODEL_NAME = "LightGBM"
SUPPORTED_FOLD_IDS: tuple[int, ...] = CANONICAL_FOLD_IDS
METRIC_NAMES: tuple[str, ...] = (
    "mae",
    "rmse",
    "wape",
    "bias",
    "rmsle",
    "nwrmsle",
)


@dataclass(frozen=True, slots=True)
class SingleFoldEvaluationConfig:
    """Inputs for one consumption-only fold evaluation."""

    fold_id: int
    fold_output_dir: Path = DEFAULT_FOLD_OUTPUT_DIR
    output_dir: Path = DEFAULT_OUTPUT_DIR
    validation_batch_size: int = 65_536


@dataclass(frozen=True, slots=True)
class SingleFoldResultPaths:
    """The only two durable outputs maintained by this runner."""

    experiment_results: Path
    markdown_summary: Path


@dataclass(frozen=True, slots=True)
class ValidatedFoldArtifacts:
    """Read-only evidence required before training one existing fold."""

    fold: TemporalValidationFold
    paths: FoldArtifactPaths
    manifest: Mapping[str, Any]
    training_rows: int
    validation_rows: int


def _result_paths(output_dir: Path) -> SingleFoldResultPaths:
    return SingleFoldResultPaths(
        experiment_results=output_dir / EXPERIMENT_RESULTS_FILENAME,
        markdown_summary=output_dir / MARKDOWN_SUMMARY_FILENAME,
    )


def _resolve_fold(fold_id: int) -> TemporalValidationFold:
    if isinstance(fold_id, bool) or fold_id not in SUPPORTED_FOLD_IDS:
        supported = ", ".join(str(value) for value in SUPPORTED_FOLD_IDS)
        raise ValueError(
            f"Unsupported fold {fold_id!r}; supported folds are {supported}"
        )
    return next(fold for fold in APPROVED_FOLDS if fold.fold_id == fold_id)


def _fold_artifact_paths(fold_id: int, output_dir: Path) -> FoldArtifactPaths:
    paths_by_id = {
        paths.fold_id: paths for paths in approved_fold_artifact_paths(output_dir)
    }
    return paths_by_id[fold_id]


def _require_existing_artifacts(paths: FoldArtifactPaths) -> None:
    missing = tuple(
        path
        for path in (paths.training, paths.validation, paths.manifest)
        if not path.is_file()
    )
    if missing:
        formatted = ", ".join(path.as_posix() for path in missing)
        raise FileNotFoundError(
            f"Fold {paths.fold_id} requires existing artifacts: {formatted}. "
            "This runner never builds fold artifacts."
        )


def _read_json_object(path: Path, *, description: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{description} is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{description} must contain a JSON object: {path}")
    return payload


def _positive_row_count(manifest: Mapping[str, Any], key: str) -> int:
    value = manifest.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"Fold manifest {key} must be a positive integer")
    return value


def _validate_manifest(
    manifest: Mapping[str, Any],
    fold: TemporalValidationFold,
) -> tuple[int, int]:
    training_origins = canonical_training_origins(fold)
    expected: tuple[tuple[str, object], ...] = (
        ("fold_id", fold.fold_id),
        ("canonical_fold_id", fold.fold_id),
        ("canonical_fold_count", len(APPROVED_FOLDS)),
        ("canonical_validation_design", CANONICAL_VALIDATION_DESIGN),
        ("execution_scope", EXECUTION_SCOPE),
        ("experiment_subset", list(SUPPORTED_FOLD_IDS)),
        ("canonical_contract_enforced", True),
        ("forecast_origin", fold.forecast_origin.isoformat()),
        ("validation_start", fold.validation_start.isoformat()),
        ("validation_end", fold.validation_end.isoformat()),
        ("modeling_target_start", MODELING_TARGET_START.isoformat()),
        ("training_target_start", MODELING_TARGET_START.isoformat()),
        ("training_target_end", fold.forecast_origin.isoformat()),
        ("max_items_per_store", None),
        ("training_origin_count", len(training_origins)),
        ("training_origin_start", training_origins[0].isoformat()),
        ("training_origin_end", training_origins[-1].isoformat()),
        ("store_count", len(ALL_FAVORITA_STORES)),
        ("configured_store_count", len(ALL_FAVORITA_STORES)),
        ("observed_store_count", len(ALL_FAVORITA_STORES)),
        ("processed_store_count", len(ALL_FAVORITA_STORES)),
        ("configured_stores", list(ALL_FAVORITA_STORES)),
        ("processed_stores", list(ALL_FAVORITA_STORES)),
        ("ordered_schema", list(TRAINING_OUTPUT_COLUMNS)),
    )
    for key, value in expected:
        if manifest.get(key) != value:
            raise ValueError(f"Fold {fold.fold_id} manifest {key} must equal {value!r}")
    if manifest.get("final_holdout_excluded") is not True:
        raise ValueError(
            f"Fold {fold.fold_id} manifest final_holdout_excluded must equal True"
        )
    if manifest.get("future_actual_leakage") is not False:
        raise ValueError(
            f"Fold {fold.fold_id} manifest future_actual_leakage must equal False"
        )
    if fold.validation_end >= FINAL_HOLDOUT.holdout_start:
        raise ValueError(
            "Selected validation window enters the protected final holdout"
        )
    return (
        _positive_row_count(manifest, "training_row_count"),
        _positive_row_count(manifest, "validation_row_count"),
    )


def _validate_parquet_footer(
    path: Path,
    *,
    partition: str,
    expected_rows: int,
    fold: TemporalValidationFold,
) -> None:
    parquet_file = pq.ParquetFile(path)
    try:
        if not parquet_file.schema_arrow.equals(OUTPUT_ARROW_SCHEMA):
            raise ValueError(
                f"{partition} Parquet must match the ordered model-ready schema"
            )
        if tuple(parquet_file.schema_arrow.names) != TRAINING_OUTPUT_COLUMNS:
            raise ValueError(
                f"{partition} Parquet must match the ordered training columns"
            )
        bounds: dict[str, tuple[Any, Any]] = {}
        for column in (
            "forecast_origin",
            "forecast_date",
            "forecast_horizon",
        ):
            column_index = parquet_file.schema_arrow.get_field_index(column)
            minima: list[Any] = []
            maxima: list[Any] = []
            for row_group_index in range(parquet_file.metadata.num_row_groups):
                statistics = (
                    parquet_file.metadata.row_group(row_group_index)
                    .column(column_index)
                    .statistics
                )
                if statistics is None or not statistics.has_min_max:
                    raise ValueError(
                        f"{partition} Parquet lacks {column} footer statistics"
                    )
                if statistics.null_count:
                    raise ValueError(f"{partition} Parquet has null {column} values")
                minima.append(statistics.min)
                maxima.append(statistics.max)
            bounds[column] = (min(minima), max(maxima))

        def as_date(value: Any):
            return value.date() if hasattr(value, "date") else value

        origin_min, origin_max = map(as_date, bounds["forecast_origin"])
        target_min, target_max = map(as_date, bounds["forecast_date"])
        horizon_min, horizon_max = bounds["forecast_horizon"]
        if (int(horizon_min), int(horizon_max)) != (
            min(FORECAST_HORIZONS),
            max(FORECAST_HORIZONS),
        ):
            raise ValueError(f"{partition} Parquet horizons must span 1 through 16")
        if partition == "Training":
            if (
                target_min != MODELING_TARGET_START
                or target_max != fold.forecast_origin
            ):
                raise ValueError(
                    "Training Parquet target dates must span the canonical fold range"
                )
            if origin_max >= fold.forecast_origin:
                raise ValueError(
                    "Training Parquet origins must precede the fold origin"
                )
        else:
            if (origin_min, origin_max) != (
                fold.forecast_origin,
                fold.forecast_origin,
            ):
                raise ValueError("Validation Parquet forecast origin is not canonical")
            if (target_min, target_max) != (
                fold.validation_start,
                fold.validation_end,
            ):
                raise ValueError("Validation Parquet dates are not canonical")
        if parquet_file.metadata.num_rows != expected_rows:
            raise ValueError(
                f"{partition} Parquet row count does not match its fold manifest"
            )
    finally:
        parquet_file.close()


def validate_existing_fold(
    config: SingleFoldEvaluationConfig,
) -> ValidatedFoldArtifacts:
    """Validate one existing fold without writing to its artifact directory."""

    validate_approved_contract()
    if config.validation_batch_size <= 0:
        raise ValueError("validation_batch_size must be positive")
    validate_canonical_fold_output_dir(config.fold_output_dir)
    fold = _resolve_fold(config.fold_id)
    paths = _fold_artifact_paths(fold.fold_id, config.fold_output_dir)
    _require_existing_artifacts(paths)
    manifest = _read_json_object(paths.manifest, description="Fold manifest")
    training_rows, validation_rows = _validate_manifest(manifest, fold)
    _validate_parquet_footer(
        paths.training,
        partition="Training",
        expected_rows=training_rows,
        fold=fold,
    )
    _validate_parquet_footer(
        paths.validation,
        partition="Validation",
        expected_rows=validation_rows,
        fold=fold,
    )
    return ValidatedFoldArtifacts(
        fold=fold,
        paths=paths,
        manifest=manifest,
        training_rows=training_rows,
        validation_rows=validation_rows,
    )


def _empty_results() -> dict[str, Any]:
    return {
        "experiment": EXPERIMENT_NAME,
        "model": MODEL_NAME,
        "completed_folds": [],
        "folds": {},
        "final_holdout_scored": False,
    }


def _load_existing_results(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _empty_results()
    payload = _read_json_object(path, description="Experiment results")
    if payload.get("experiment") != EXPERIMENT_NAME:
        raise ValueError("Existing experiment results use a different experiment")
    if payload.get("model") != MODEL_NAME:
        raise ValueError("Existing experiment results use a different model")
    if payload.get("final_holdout_scored") is not False:
        raise ValueError("Existing results must preserve final_holdout_scored=false")
    folds = payload.get("folds")
    if not isinstance(folds, dict):
        raise ValueError("Existing experiment results folds must be a JSON object")
    for key, record in folds.items():
        if key not in {str(value) for value in SUPPORTED_FOLD_IDS}:
            raise ValueError(
                f"Existing experiment results contain unsupported fold {key}"
            )
        if not isinstance(record, dict) or record.get("status") != "completed":
            raise ValueError(f"Existing fold {key} is not a completed result")
    return payload


def _merge_fold_result(
    existing: Mapping[str, Any],
    *,
    fold: TemporalValidationFold,
    runtime_seconds: float,
    training_rows: int,
    validation_rows: int,
    metrics: Mapping[str, float],
) -> dict[str, Any]:
    folds = dict(existing["folds"])
    folds[str(fold.fold_id)] = {
        "status": "completed",
        "forecast_origin": fold.forecast_origin.isoformat(),
        "validation_start": fold.validation_start.isoformat(),
        "validation_end": fold.validation_end.isoformat(),
        "runtime_seconds": float(runtime_seconds),
        "training_rows": training_rows,
        "validation_rows": validation_rows,
        "metrics": {name: float(metrics[name]) for name in METRIC_NAMES},
    }
    ordered_folds = {
        key: folds[key] for key in sorted(folds, key=lambda value: int(value))
    }
    return {
        "experiment": EXPERIMENT_NAME,
        "model": MODEL_NAME,
        "completed_folds": [int(key) for key in ordered_folds],
        "folds": ordered_folds,
        "final_holdout_scored": False,
    }


def render_markdown_summary(results: Mapping[str, Any]) -> str:
    """Render the human-readable summary only from canonical JSON content."""

    completed = results.get("completed_folds")
    folds = results.get("folds")
    if not isinstance(completed, list) or not isinstance(folds, Mapping):
        raise ValueError("Canonical results are missing completed fold evidence")
    if results.get("final_holdout_scored") is not False:
        raise ValueError("Canonical results must preserve final_holdout_scored=false")
    completed_text = ", ".join(str(value) for value in completed) or "None"
    lines = [
        "# Favorita LightGBM Evaluation Summary",
        "",
        f"- Experiment: {results['experiment']}",
        f"- Model: {results['model']}",
        f"- Completed folds: {completed_text}",
        "- Final holdout scored: "
        + ("Yes" if results["final_holdout_scored"] else "No"),
        "",
        (
            "| Fold | Training Rows | Validation Rows | MAE | RMSE | WAPE | "
            "Bias | RMSLE | NWRMSLE | Runtime |"
        ),
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for fold_id in completed:
        record = folds[str(fold_id)]
        metrics = record["metrics"]
        lines.append(
            "| "
            + " | ".join(
                (
                    str(fold_id),
                    f"{record['training_rows']:,}",
                    f"{record['validation_rows']:,}",
                    f"{metrics['mae']:.6f}",
                    f"{metrics['rmse']:.6f}",
                    f"{metrics['wape']:.6f}",
                    f"{metrics['bias']:.6f}",
                    f"{metrics['rmsle']:.6f}",
                    f"{metrics['nwrmsle']:.6f}",
                    f"{record['runtime_seconds']:.3f} s",
                )
            )
            + " |"
        )
    lines.extend(
        (
            "",
            "The protected final holdout was not loaded or scored.",
            "",
        )
    )
    return "\n".join(lines)


def _write_text_atomic(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temp_path.write_text(text, encoding="utf-8")
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _restore_bytes(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
        return
    temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.restore")
    try:
        temp_path.write_bytes(previous)
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _publish_results(
    results: dict[str, Any],
    paths: SingleFoldResultPaths,
) -> None:
    previous_json = (
        paths.experiment_results.read_bytes()
        if paths.experiment_results.exists()
        else None
    )
    previous_markdown = (
        paths.markdown_summary.read_bytes() if paths.markdown_summary.exists() else None
    )
    write_json_atomic(
        results,
        paths.experiment_results,
        overwrite=paths.experiment_results.exists(),
    )
    try:
        canonical = _read_json_object(
            paths.experiment_results,
            description="Experiment results",
        )
        _write_text_atomic(render_markdown_summary(canonical), paths.markdown_summary)
    except Exception:
        _restore_bytes(paths.experiment_results, previous_json)
        _restore_bytes(paths.markdown_summary, previous_markdown)
        raise


def run_single_fold(
    config: SingleFoldEvaluationConfig,
) -> SingleFoldResultPaths:
    """Train and stream-evaluate exactly one existing canonical fold."""

    validated = validate_existing_fold(config)
    started = perf_counter()
    model = FavoritaLightGBMAdapter()
    model.fit_parquet(validated.paths.training)
    accumulator = FavoritaMetricAccumulator()
    key_tracker = _ValidationKeyTracker()
    observed_horizons: set[int] = set()
    for frame in iter_model_ready_validation_batches(
        validated.paths.validation,
        batch_size=config.validation_batch_size,
    ):
        _validate_validation_batch(validated.fold, frame, key_tracker)
        predictions = np.asarray(model.predict_frame(frame), dtype="float64")
        if predictions.ndim != 1 or len(predictions) != len(frame):
            raise ValueError(
                f"Fold {validated.fold.fold_id} prediction count must match "
                "validation rows"
            )
        if not np.isfinite(predictions).all():
            raise ValueError("Predictions must contain only finite values")
        actual = frame["unit_sales"].to_numpy(dtype="float64", copy=False)
        perishable = frame["perishable"].to_numpy(copy=False)
        accumulator.update(actual, predictions, perishable)
        observed_horizons.update(
            int(value) for value in frame["forecast_horizon"].unique()
        )
        del frame, predictions, actual, perishable
    if tuple(sorted(observed_horizons)) != FORECAST_HORIZONS:
        raise ValueError(
            f"Fold {validated.fold.fold_id} validation must cover horizons 1 through 16"
        )
    metrics = accumulator.finalize()
    if accumulator.count != validated.validation_rows:
        raise ValueError("Validated prediction count differs from manifest row count")
    runtime_seconds = perf_counter() - started

    paths = _result_paths(config.output_dir)
    existing = _load_existing_results(paths.experiment_results)
    merged = _merge_fold_result(
        existing,
        fold=validated.fold,
        runtime_seconds=runtime_seconds,
        training_rows=validated.training_rows,
        validation_rows=validated.validation_rows,
        metrics=asdict(metrics),
    )
    _publish_results(merged, paths)
    return paths


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one existing Favorita LightGBM validation fold."
    )
    parser.add_argument(
        "--fold",
        type=int,
        required=True,
        choices=SUPPORTED_FOLD_IDS,
        help="Canonical existing fold to evaluate (1, 2, 3, or 4).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    paths = run_single_fold(SingleFoldEvaluationConfig(fold_id=args.fold))
    print(paths.experiment_results.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
