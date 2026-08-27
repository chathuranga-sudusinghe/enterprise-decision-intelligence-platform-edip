"""Serial fold-wise Favorita LightGBM evaluation orchestration."""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
import uuid
from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pipelines.evaluation.favorita_backtesting import (
    BacktestExample,
    BacktestResult,
    EvaluationEvidence,
    FoldBacktestResult,
    aggregate_fold_backtest_results,
)
from pipelines.evaluation.favorita_metrics import (
    ForecastMetricResults,
    FavoritaMetricAccumulator,
    evaluate_favorita_forecasts,
)
from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
    TemporalValidationFold,
    validate_approved_contract,
)
from pipelines.features.favorita_model_ready import (
    MODEL_FEATURE_COLUMNS,
    PARQUET_ROW_GROUP_SIZE,
    TRAINING_OUTPUT_COLUMNS,
    write_json_atomic,
)
from pipelines.features.build_favorita_fold_datasets import (
    ALL_STORE_BATCHES,
    DEFAULT_OUTPUT_DIR as DEFAULT_FOLD_OUTPUT_DIR,
    FoldDatasetBuildConfig,
    approved_fold_artifact_paths,
    build_approved_fold_datasets,
)
from pipelines.models.favorita_lightgbm import (
    FavoritaLightGBMAdapter,
    LIGHTGBM_PARAMETERS,
    NUM_BOOST_ROUND,
)

DEFAULT_SOURCE_PATH = Path("data/processed/favorita_cleaned/favorita_cleaned.parquet")
DEFAULT_OUTPUT_DIR = Path("artifacts/evaluation/favorita_lightgbm")
ALL_FAVORITA_STORES: tuple[int, ...] = tuple(range(1, 55))
_FEATURE_MAPPING_COLUMNS: tuple[str, ...] = tuple(
    column
    for column in MODEL_FEATURE_COLUMNS
    if column not in {"store_nbr", "item_nbr"}
)
_METRIC_NAMES: tuple[str, ...] = (
    "mae",
    "rmse",
    "wape",
    "bias",
    "rmsle",
    "nwrmsle",
)
PREDICTION_COLUMNS: tuple[str, ...] = (
    "fold_id",
    "forecast_origin",
    "forecast_date",
    "forecast_horizon",
    "store_nbr",
    "item_nbr",
    "actual_unit_sales",
    "prediction",
    "perishable",
)
PREDICTION_ARROW_SCHEMA = pa.schema(
    [
        pa.field("fold_id", pa.int8(), nullable=False),
        pa.field("forecast_origin", pa.timestamp("us"), nullable=False),
        pa.field("forecast_date", pa.timestamp("us"), nullable=False),
        pa.field("forecast_horizon", pa.int8(), nullable=False),
        pa.field("store_nbr", pa.int16(), nullable=False),
        pa.field("item_nbr", pa.int32(), nullable=False),
        pa.field("actual_unit_sales", pa.float64(), nullable=False),
        pa.field("prediction", pa.float64(), nullable=False),
        pa.field("perishable", pa.int8(), nullable=False),
    ]
)


@dataclass(frozen=True, slots=True)
class FavoritaEvaluationRunConfig:
    """Explicit inputs for one approved full-coverage evaluation run."""

    source_path: Path
    output_dir: Path
    fold_output_dir: Path = DEFAULT_FOLD_OUTPUT_DIR
    overwrite: bool = False


@dataclass(frozen=True, slots=True)
class EvaluationArtifactPaths:
    """Files written by a completed evaluation run."""

    overall_metrics: Path
    fold_metrics: Path
    horizon_metrics: Path
    predictions: Path
    run_manifest: Path


@dataclass(frozen=True, slots=True)
class StreamingFoldMetricRecord:
    fold_id: int
    forecast_origin: date
    validation_start: date
    validation_end: date
    metrics: ForecastMetricResults
    row_count: int


@dataclass(frozen=True, slots=True)
class StreamingHorizonMetricRecord:
    forecast_horizon: int
    metrics: ForecastMetricResults
    row_count: int


@dataclass(frozen=True, slots=True)
class StreamingEvaluationSummary:
    overall_metrics: ForecastMetricResults
    fold_metrics: tuple[StreamingFoldMetricRecord, ...]
    horizon_metrics: tuple[StreamingHorizonMetricRecord, ...]
    prediction_row_count: int


def _artifact_paths(output_dir: Path) -> EvaluationArtifactPaths:
    return EvaluationArtifactPaths(
        overall_metrics=output_dir / "overall_metrics.json",
        fold_metrics=output_dir / "fold_metrics.csv",
        horizon_metrics=output_dir / "horizon_metrics.csv",
        predictions=output_dir / "predictions.parquet",
        run_manifest=output_dir / "run_manifest.json",
    )


def validate_evaluation_config(config: FavoritaEvaluationRunConfig) -> None:
    """Reject ambiguous origins, unsafe paths, and any holdout exposure."""

    validate_approved_contract()
    if not config.source_path.is_file():
        raise FileNotFoundError(config.source_path)
    resolved_paths = {
        config.source_path.resolve(),
        config.output_dir.resolve(),
        config.fold_output_dir.resolve(),
    }
    if len(resolved_paths) != 3:
        raise ValueError(
            "source_path, output_dir, and fold_output_dir must be distinct"
        )


def _python_value(value: object) -> object:
    return None if pd.isna(value) else value


def feature_frame_to_backtest_examples(
    frame: pd.DataFrame,
) -> tuple[BacktestExample, ...]:
    """Bridge one model-ready frame to the existing immutable row contract."""

    if tuple(frame.columns) != TRAINING_OUTPUT_COLUMNS:
        raise ValueError("Feature frame must match the ordered training schema")
    examples: list[BacktestExample] = []
    for values in frame.itertuples(index=False, name=None):
        row = dict(zip(TRAINING_OUTPUT_COLUMNS, values, strict=True))
        features = {
            column: _python_value(row[column]) for column in _FEATURE_MAPPING_COLUMNS
        }
        examples.append(
            BacktestExample(
                forecast_origin=pd.Timestamp(row["forecast_origin"]).date(),
                forecast_date=pd.Timestamp(row["forecast_date"]).date(),
                forecast_horizon=int(row["forecast_horizon"]),
                store_nbr=int(row["store_nbr"]),
                item_nbr=int(row["item_nbr"]),
                unit_sales=float(row["unit_sales"]),
                perishable=int(row["perishable"]),
                features=features,
            )
        )
    return tuple(examples)


def load_backtest_examples(feature_path: Path) -> tuple[BacktestExample, ...]:
    """Read the materialized feature artifact in batches without dropping rows."""

    parquet_file = pq.ParquetFile(feature_path)
    materialized: list[BacktestExample] = []
    try:
        for batch in parquet_file.iter_batches(
            batch_size=131_072,
            columns=list(TRAINING_OUTPUT_COLUMNS),
        ):
            materialized.extend(
                feature_frame_to_backtest_examples(batch.to_pandas())
            )
    finally:
        parquet_file.close()
    examples = tuple(materialized)
    if not examples:
        raise ValueError("Materialized feature artifact contains no examples")
    return examples


def load_model_ready_frame(feature_path: Path) -> pd.DataFrame:
    """Load one bounded validation Parquet as the ordered columnar schema."""

    table = pq.read_table(
        feature_path,
        columns=list(TRAINING_OUTPUT_COLUMNS),
    )
    frame = table.to_pandas()
    if tuple(frame.columns) != TRAINING_OUTPUT_COLUMNS:
        raise ValueError("Feature frame must match the ordered training schema")
    if frame.empty:
        raise ValueError("Materialized validation artifact contains no rows")
    return frame


def iter_model_ready_validation_batches(
    feature_path: Path,
    *,
    batch_size: int = PARQUET_ROW_GROUP_SIZE,
) -> Iterator[pd.DataFrame]:
    """Yield one ordered model-ready validation batch at a time."""

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    parquet_file = pq.ParquetFile(feature_path)
    if tuple(parquet_file.schema_arrow.names) != TRAINING_OUTPUT_COLUMNS:
        parquet_file.close()
        raise ValueError(
            "Validation Parquet must match the ordered training schema"
        )
    yielded_rows = 0
    try:
        for batch in parquet_file.iter_batches(
            batch_size=batch_size,
            columns=list(TRAINING_OUTPUT_COLUMNS),
        ):
            frame = batch.to_pandas()
            if tuple(frame.columns) != TRAINING_OUTPUT_COLUMNS:
                raise ValueError(
                    "Validation batch must match the ordered training schema"
                )
            if frame.empty:
                continue
            yielded_rows += len(frame)
            yield frame
    finally:
        parquet_file.close()
    if yielded_rows == 0:
        raise ValueError("Materialized validation artifact contains no rows")


@dataclass(slots=True)
class _ValidationKeyTracker:
    """Validate contiguous ordered store blocks with state bounded by store count."""

    current_store: int | None = None
    last_key: tuple[pd.Timestamp, int] | None = None
    completed_stores: set[int] | None = None

    def __post_init__(self) -> None:
        if self.completed_stores is None:
            self.completed_stores = set()

    def update(self, frame: pd.DataFrame, fold_id: int) -> None:
        assert self.completed_stores is not None
        for forecast_date, store_nbr, item_nbr in frame[
            ["forecast_date", "store_nbr", "item_nbr"]
        ].itertuples(index=False, name=None):
            store = int(store_nbr)
            if store != self.current_store:
                if self.current_store is not None:
                    self.completed_stores.add(self.current_store)
                if store in self.completed_stores:
                    raise ValueError(
                        f"Fold {fold_id} validation store blocks must be contiguous"
                    )
                self.current_store = store
                self.last_key = None
            key = (pd.Timestamp(forecast_date), int(item_nbr))
            if self.last_key is not None and key <= self.last_key:
                raise ValueError(
                    f"Fold {fold_id} validation keys must be unique and ordered"
                )
            self.last_key = key


class _StreamingPredictionWriter:
    """Append bounded row-level evidence batches to one staged Parquet file."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.writer = pq.ParquetWriter(
            path,
            PREDICTION_ARROW_SCHEMA,
            compression="zstd",
        )
        self.rows_written = 0
        self.write_count = 0

    def write(
        self,
        fold: TemporalValidationFold,
        frame: pd.DataFrame,
        predictions: np.ndarray,
    ) -> None:
        table = pa.Table.from_pydict(
            {
                "fold_id": np.full(len(frame), fold.fold_id, dtype="int8"),
                "forecast_origin": frame["forecast_origin"],
                "forecast_date": frame["forecast_date"],
                "forecast_horizon": frame["forecast_horizon"],
                "store_nbr": frame["store_nbr"],
                "item_nbr": frame["item_nbr"],
                "actual_unit_sales": frame["unit_sales"],
                "prediction": predictions,
                "perishable": frame["perishable"],
            },
            schema=PREDICTION_ARROW_SCHEMA,
        )
        self.writer.write_table(table, row_group_size=PARQUET_ROW_GROUP_SIZE)
        self.rows_written += table.num_rows
        self.write_count += 1

    def close(self) -> None:
        if self.writer is not None:
            self.writer.close()
            self.writer = None
        if self.rows_written == 0:
            raise RuntimeError("No prediction evidence was written")

    def abort(self) -> None:
        if self.writer is not None:
            self.writer.close()
            self.writer = None
        self.path.unlink(missing_ok=True)


def _validate_validation_batch(
    fold: TemporalValidationFold,
    frame: pd.DataFrame,
    key_tracker: _ValidationKeyTracker,
) -> None:
    if tuple(frame.columns) != TRAINING_OUTPUT_COLUMNS:
        raise ValueError("Validation batch must match the ordered training schema")
    origins = pd.to_datetime(frame["forecast_origin"])
    forecast_dates = pd.to_datetime(frame["forecast_date"])
    horizons = frame["forecast_horizon"]
    if not origins.dt.date.eq(fold.forecast_origin).all():
        raise ValueError(
            f"Fold {fold.fold_id} validation origin differs from the contract"
        )
    if not horizons.isin(FORECAST_HORIZONS).all():
        raise ValueError("Validation forecast_horizon must be within 1 through 16")
    expected_dates = origins + pd.to_timedelta(horizons, unit="D")
    if not forecast_dates.eq(expected_dates).all():
        raise ValueError("Validation forecast_date must equal origin plus horizon")
    if not forecast_dates.dt.date.between(
        fold.validation_start,
        fold.validation_end,
    ).all():
        raise ValueError(
            f"Fold {fold.fold_id} validation rows are outside O+1..O+16"
        )
    if not (forecast_dates.dt.date < FINAL_HOLDOUT.holdout_start).all():
        raise ValueError("Final holdout rows must not be evaluated")
    actual = frame["unit_sales"].to_numpy(dtype="float64", copy=False)
    if not np.isfinite(actual).all():
        raise ValueError("Validation unit_sales must contain only finite values")
    if not frame["perishable"].isin((0, 1, False, True)).all():
        raise ValueError("Validation perishable must contain only binary values")
    key_tracker.update(frame, fold.fold_id)


def _stream_fold_validation(
    *,
    fold: TemporalValidationFold,
    validation_path: Path,
    model: FavoritaLightGBMAdapter,
    prediction_writer: _StreamingPredictionWriter,
    overall_accumulator: FavoritaMetricAccumulator,
    horizon_accumulators: dict[int, FavoritaMetricAccumulator],
) -> StreamingFoldMetricRecord:
    fold_accumulator = FavoritaMetricAccumulator()
    key_tracker = _ValidationKeyTracker()
    observed_horizons: set[int] = set()
    for frame in iter_model_ready_validation_batches(validation_path):
        _validate_validation_batch(fold, frame, key_tracker)
        predictions = np.asarray(model.predict_frame(frame), dtype="float64")
        if predictions.ndim != 1 or len(predictions) != len(frame):
            raise ValueError(
                f"Fold {fold.fold_id} prediction row count must match validation rows"
            )
        if not np.isfinite(predictions).all():
            raise ValueError("Predictions must contain only finite values")
        actual = frame["unit_sales"].to_numpy(dtype="float64", copy=False)
        perishable = frame["perishable"].to_numpy(copy=False)
        fold_accumulator.update(actual, predictions, perishable)
        overall_accumulator.update(actual, predictions, perishable)
        batch_horizons = sorted(
            int(value) for value in frame["forecast_horizon"].unique()
        )
        for horizon in batch_horizons:
            mask = frame["forecast_horizon"].to_numpy(copy=False) == horizon
            horizon_accumulators[horizon].update(
                actual[mask],
                predictions[mask],
                perishable[mask],
            )
            observed_horizons.add(horizon)
        prediction_writer.write(fold, frame, predictions)
        del frame, predictions, actual, perishable
    if tuple(sorted(observed_horizons)) != FORECAST_HORIZONS:
        raise ValueError(
            f"Fold {fold.fold_id} validation must cover horizons 1 through 16"
        )
    return StreamingFoldMetricRecord(
        fold_id=fold.fold_id,
        forecast_origin=fold.forecast_origin,
        validation_start=fold.validation_start,
        validation_end=fold.validation_end,
        metrics=fold_accumulator.finalize(),
        row_count=fold_accumulator.count,
    )


def _fold_result_from_frame(
    fold: TemporalValidationFold,
    validation_frame: pd.DataFrame,
    predictions: Sequence[float],
) -> FoldBacktestResult:
    values = tuple(float(value) for value in predictions)
    if len(values) != len(validation_frame):
        raise ValueError(
            f"Fold {fold.fold_id} prediction row count must match validation rows"
        )
    if not all(pd.notna(value) and np.isfinite(value) for value in values):
        raise ValueError("Predictions must contain only finite values")
    origins = pd.to_datetime(validation_frame["forecast_origin"]).dt.date
    forecast_dates = pd.to_datetime(validation_frame["forecast_date"]).dt.date
    horizons = validation_frame["forecast_horizon"].astype(int)
    if not origins.eq(fold.forecast_origin).all():
        raise ValueError(
            f"Fold {fold.fold_id} validation origin differs from the contract"
        )
    if not forecast_dates.between(
        fold.validation_start,
        fold.validation_end,
    ).all():
        raise ValueError(
            f"Fold {fold.fold_id} validation rows are outside O+1..O+16"
        )
    if tuple(sorted(horizons.unique())) != FORECAST_HORIZONS:
        raise ValueError(
            f"Fold {fold.fold_id} validation must cover horizons 1 through 16"
        )
    expected_dates = pd.to_datetime(origins) + pd.to_timedelta(
        horizons,
        unit="D",
    )
    if not (
        pd.to_datetime(validation_frame["forecast_date"])
        == pd.to_datetime(expected_dates)
    ).all():
        raise ValueError("Validation forecast_date must equal origin plus horizon")
    key_columns = [
        "forecast_origin",
        "forecast_date",
        "store_nbr",
        "item_nbr",
    ]
    if validation_frame.duplicated(key_columns).any():
        raise ValueError(f"Fold {fold.fold_id} validation keys must be unique")

    evidence = tuple(
        EvaluationEvidence(
            fold_id=fold.fold_id,
            forecast_origin=origin,
            forecast_date=forecast_date,
            forecast_horizon=int(horizon),
            store_nbr=int(store),
            item_nbr=int(item),
            actual_unit_sales=float(actual),
            prediction=prediction,
            perishable=int(perishable),
        )
        for (
            origin,
            forecast_date,
            horizon,
            store,
            item,
            actual,
            perishable,
            prediction,
        ) in zip(
            origins,
            forecast_dates,
            horizons,
            validation_frame["store_nbr"],
            validation_frame["item_nbr"],
            validation_frame["unit_sales"],
            validation_frame["perishable"],
            values,
            strict=True,
        )
    )
    metrics = evaluate_favorita_forecasts(
        actual=(row.actual_unit_sales for row in evidence),
        prediction=(row.prediction for row in evidence),
        perishable=(row.perishable for row in evidence),
    )
    return FoldBacktestResult(
        fold_id=fold.fold_id,
        forecast_origin=fold.forecast_origin,
        validation_start=fold.validation_start,
        validation_end=fold.validation_end,
        metrics=metrics,
        predictions=evidence,
    )


def _metrics_record(metrics: ForecastMetricResults) -> dict[str, float]:
    values = asdict(metrics)
    return {name: float(values[name]) for name in _METRIC_NAMES}


def _fold_metrics_frame(result: StreamingEvaluationSummary) -> pd.DataFrame:
    return pd.DataFrame.from_records(
        {
            "fold_id": fold.fold_id,
            "forecast_origin": fold.forecast_origin.isoformat(),
            "validation_start": fold.validation_start.isoformat(),
            "validation_end": fold.validation_end.isoformat(),
            "validation_rows": fold.row_count,
            **_metrics_record(fold.metrics),
        }
        for fold in result.fold_metrics
    )


def _horizon_metrics_frame(result: StreamingEvaluationSummary) -> pd.DataFrame:
    return pd.DataFrame.from_records(
        {
            "forecast_horizon": horizon.forecast_horizon,
            "validation_rows": horizon.row_count,
            **_metrics_record(horizon.metrics),
        }
        for horizon in result.horizon_metrics
    )


def _predictions_frame(result: BacktestResult) -> pd.DataFrame:
    return pd.DataFrame.from_records(asdict(row) for row in result.predictions)


def _write_frame_atomic(
    frame: pd.DataFrame,
    path: Path,
    *,
    overwrite: bool,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        if path.suffix == ".csv":
            frame.to_csv(temp_path, index=False)
        elif path.suffix == ".parquet":
            frame.to_parquet(temp_path, index=False, compression="zstd")
        else:
            raise ValueError(f"Unsupported dataframe artifact format: {path.suffix}")
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _require_available_paths(
    paths: EvaluationArtifactPaths,
    *,
    overwrite: bool,
) -> None:
    if overwrite:
        return
    for path in asdict(paths).values():
        candidate = Path(path)
        if candidate.exists():
            raise FileExistsError(candidate)


def _path_values(paths: EvaluationArtifactPaths) -> tuple[Path, ...]:
    return tuple(Path(value) for value in asdict(paths).values())


def _source_state(path: Path) -> dict[str, int]:
    stat = path.stat()
    return {"size_bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def _manifest(
    *,
    config: FavoritaEvaluationRunConfig,
    paths: EvaluationArtifactPaths,
    build_result: dict[str, Any],
    result: StreamingEvaluationSummary,
    started_at: datetime,
    completed_at: datetime,
    source_state: dict[str, int],
) -> dict[str, Any]:
    return {
        "run": {
            "status": "completed",
            "started_at_utc": started_at.isoformat(),
            "completed_at_utc": completed_at.isoformat(),
            "model": "FavoritaLightGBMAdapter",
            "evaluation_method": "eight-fold expanding-window backtesting",
        },
        "source": {
            "path": config.source_path.as_posix(),
            **source_state,
            "mutated": False,
        },
        "configuration": {
            "stores": list(ALL_FAVORITA_STORES),
            "store_count": len(ALL_FAVORITA_STORES),
            "max_items_per_store": None,
            "forecast_horizons": list(FORECAST_HORIZONS),
            "direct_horizon_aware": True,
            "recursive_feedback": False,
            "future_promotion_assumption": False,
            "future_holiday_assumption": False,
            "model_parameters": dict(LIGHTGBM_PARAMETERS),
            "num_boost_round": NUM_BOOST_ROUND,
            "hyperparameter_tuning": False,
            "early_stopping": False,
        },
        "folds": [
            {
                "fold_id": fold.fold_id,
                "forecast_origin": fold.forecast_origin.isoformat(),
                "validation_start": fold.validation_start.isoformat(),
                "validation_end": fold.validation_end.isoformat(),
            }
            for fold in APPROVED_FOLDS
        ],
        "final_holdout": {
            "forecast_origin": FINAL_HOLDOUT.forecast_origin.isoformat(),
            "holdout_start": FINAL_HOLDOUT.holdout_start.isoformat(),
            "holdout_end": FINAL_HOLDOUT.holdout_end.isoformat(),
            "scored": False,
            "materialized": False,
        },
        "feature_materialization": build_result,
        "training_memory": {
            "training_input": "Parquet row-group LightGBM Sequence",
            "python_backtest_examples_materialized": False,
            "full_fold_pandas_frame_materialized": False,
            "target_storage": "temporary float64 disk memmap",
            "lightgbm_native_dataset_in_memory": True,
            "true_external_memory_training": False,
        },
        "evaluation": {
            "metric_names": list(_METRIC_NAMES),
            "prediction_rows": result.prediction_row_count,
            "fold_count": len(result.fold_metrics),
            "horizon_count": len(result.horizon_metrics),
        },
        "validation_memory": {
            "validation_input": "Parquet batches",
            "full_fold_validation_frame_materialized": False,
            "evaluation_evidence_python_objects_materialized": False,
            "predictions_written_incrementally": True,
            "metrics_computed_incrementally": True,
        },
        "artifacts": {
            key: Path(value).as_posix() for key, value in asdict(paths).items()
        },
    }


def _publish_completed_artifacts(
    *,
    paths: EvaluationArtifactPaths,
    stage_paths: EvaluationArtifactPaths,
    result: StreamingEvaluationSummary,
    manifest: dict[str, Any],
) -> None:
    """Finish staged summaries, then publish the completed manifest last."""

    write_json_atomic(
        _metrics_record(result.overall_metrics),
        stage_paths.overall_metrics,
        overwrite=False,
    )
    _write_frame_atomic(
        _fold_metrics_frame(result),
        stage_paths.fold_metrics,
        overwrite=False,
    )
    _write_frame_atomic(
        _horizon_metrics_frame(result),
        stage_paths.horizon_metrics,
        overwrite=False,
    )
    if not stage_paths.predictions.is_file():
        raise FileNotFoundError(stage_paths.predictions)
    write_json_atomic(manifest, stage_paths.run_manifest, overwrite=False)

    paths.run_manifest.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = stage_paths.run_manifest.parent / "backups"
    backups: dict[Path, Path] = {}
    published: list[Path] = []
    try:
        for staged, destination in zip(
            _path_values(stage_paths),
            _path_values(paths),
            strict=True,
        ):
            if destination.exists():
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup = backup_dir / destination.name
                os.replace(destination, backup)
                backups[destination] = backup
            os.replace(staged, destination)
            published.append(destination)
    except Exception:
        for destination in reversed(published):
            destination.unlink(missing_ok=True)
        for destination, backup in backups.items():
            if backup.exists():
                os.replace(backup, destination)
        raise
    finally:
        shutil.rmtree(backup_dir, ignore_errors=True)


def run_evaluation(
    config: FavoritaEvaluationRunConfig,
) -> EvaluationArtifactPaths:
    """Build, fit, and stream-score each approved fold serially."""

    validate_evaluation_config(config)
    paths = _artifact_paths(config.output_dir)
    _require_available_paths(paths, overwrite=config.overwrite)
    source_state = _source_state(config.source_path)
    started_at = datetime.now(timezone.utc)

    fold_build_manifests = build_approved_fold_datasets(
        FoldDatasetBuildConfig(
            source_path=config.source_path,
            output_dir=config.fold_output_dir,
            store_batches=ALL_STORE_BATCHES,
            max_items_per_store=None,
            overwrite=config.overwrite,
        )
    )
    if len(fold_build_manifests) != len(APPROVED_FOLDS):
        raise ValueError("Fold materialization must return exactly 8 manifests")

    paths.run_manifest.parent.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{paths.run_manifest.parent.name}.",
        dir=paths.run_manifest.parent.parent,
    ) as temporary_directory:
        stage_paths = _artifact_paths(Path(temporary_directory))
        prediction_writer = _StreamingPredictionWriter(stage_paths.predictions)
        overall_accumulator = FavoritaMetricAccumulator()
        horizon_accumulators = {
            horizon: FavoritaMetricAccumulator() for horizon in FORECAST_HORIZONS
        }
        fold_metrics: list[StreamingFoldMetricRecord] = []
        try:
            fold_paths = approved_fold_artifact_paths(config.fold_output_dir)
            for fold, artifact_paths in zip(
                APPROVED_FOLDS,
                fold_paths,
                strict=True,
            ):
                model = FavoritaLightGBMAdapter()
                model.fit_parquet(artifact_paths.training)
                fold_metrics.append(
                    _stream_fold_validation(
                        fold=fold,
                        validation_path=artifact_paths.validation,
                        model=model,
                        prediction_writer=prediction_writer,
                        overall_accumulator=overall_accumulator,
                        horizon_accumulators=horizon_accumulators,
                    )
                )
                del model
            prediction_writer.close()
        except Exception:
            prediction_writer.abort()
            raise

        result = StreamingEvaluationSummary(
            overall_metrics=overall_accumulator.finalize(),
            fold_metrics=tuple(fold_metrics),
            horizon_metrics=tuple(
                StreamingHorizonMetricRecord(
                    forecast_horizon=horizon,
                    metrics=horizon_accumulators[horizon].finalize(),
                    row_count=horizon_accumulators[horizon].count,
                )
                for horizon in FORECAST_HORIZONS
            ),
            prediction_row_count=prediction_writer.rows_written,
        )
        if sum(fold.row_count for fold in result.fold_metrics) != (
            result.prediction_row_count
        ):
            raise AssertionError("Fold row counts do not match prediction evidence")
        if sum(horizon.row_count for horizon in result.horizon_metrics) != (
            result.prediction_row_count
        ):
            raise AssertionError("Horizon row counts do not match prediction evidence")
        completed_at = datetime.now(timezone.utc)
        if _source_state(config.source_path) != source_state:
            raise AssertionError("Cleaned source changed during evaluation")
        build_result = {
            "output_dir": config.fold_output_dir.as_posix(),
            "fold_count": len(fold_build_manifests),
            "folds": list(fold_build_manifests),
            "consumed_serially": True,
        }
        manifest = _manifest(
            config=config,
            paths=paths,
            build_result=build_result,
            result=result,
            started_at=started_at,
            completed_at=completed_at,
            source_state=source_state,
        )
        _publish_completed_artifacts(
            paths=paths,
            stage_paths=stage_paths,
            result=result,
            manifest=manifest,
        )
    if _source_state(config.source_path) != source_state:
        paths.run_manifest.unlink(missing_ok=True)
        raise AssertionError("Cleaned source changed during artifact publication")
    return paths


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the approved serial Favorita eight-fold LightGBM evaluation."
        )
    )
    parser.add_argument("--source-path", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--fold-output-dir",
        type=Path,
        default=DEFAULT_FOLD_OUTPUT_DIR,
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    paths = run_evaluation(
        FavoritaEvaluationRunConfig(
            source_path=args.source_path,
            output_dir=args.output_dir,
            fold_output_dir=args.fold_output_dir,
            overwrite=args.overwrite,
        )
    )
    print(paths.run_manifest.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
