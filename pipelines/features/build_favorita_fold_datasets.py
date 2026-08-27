"""Build the eight approved Favorita fold datasets without fitting a model."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pyarrow.compute as pc
import pyarrow.parquet as pq

from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
    TemporalValidationFold,
    validate_approved_contract,
)
from pipelines.features.favorita_model_ready import (
    TRAINING_OUTPUT_COLUMNS,
    FeatureBuildConfig,
    materialize_feature_dataset,
    write_json_atomic,
)

DEFAULT_SOURCE_PATH = Path(
    "data/processed/favorita_cleaned/favorita_cleaned.parquet"
)
DEFAULT_OUTPUT_DIR = Path("artifacts/features/favorita_folds")
ALL_FAVORITA_STORES: tuple[int, ...] = tuple(range(1, 55))
ALL_STORE_BATCHES: tuple[tuple[int, ...], ...] = tuple(
    (store_nbr,) for store_nbr in ALL_FAVORITA_STORES
)


@dataclass(frozen=True, slots=True)
class FoldDatasetBuildConfig:
    """Inputs for the approved fold-wise model-ready artifact build."""

    source_path: Path = DEFAULT_SOURCE_PATH
    output_dir: Path = DEFAULT_OUTPUT_DIR
    store_batches: tuple[tuple[int, ...], ...] = ALL_STORE_BATCHES
    max_items_per_store: int | None = None
    overwrite: bool = False


@dataclass(frozen=True, slots=True)
class FoldArtifactPaths:
    """The three artifacts owned by one approved fold."""

    fold_id: int
    directory: Path
    training: Path
    validation: Path
    manifest: Path


def approved_fold_artifact_paths(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> tuple[FoldArtifactPaths, ...]:
    """Return the exact ordered eight-fold output definition."""

    validate_approved_contract()
    return tuple(
        FoldArtifactPaths(
            fold_id=fold.fold_id,
            directory=output_dir / f"fold_{fold.fold_id:02d}",
            training=output_dir / f"fold_{fold.fold_id:02d}" / "training.parquet",
            validation=output_dir
            / f"fold_{fold.fold_id:02d}"
            / "validation.parquet",
            manifest=output_dir / f"fold_{fold.fold_id:02d}" / "manifest.json",
        )
        for fold in APPROVED_FOLDS
    )


def _source_date_bounds(source_path: Path) -> tuple[date, date]:
    """Read only Parquet date batches to establish the historical origin range."""

    parquet_file = pq.ParquetFile(source_path)
    try:
        minimum: date | None = None
        maximum: date | None = None
        for batch in parquet_file.iter_batches(
            batch_size=131_072,
            columns=["date"],
        ):
            bounds = pc.min_max(batch.column(0))
            current_min = bounds["min"].as_py()
            current_max = bounds["max"].as_py()
            if hasattr(current_min, "date"):
                current_min = current_min.date()
            if hasattr(current_max, "date"):
                current_max = current_max.date()
            minimum = current_min if minimum is None else min(minimum, current_min)
            maximum = current_max if maximum is None else max(maximum, current_max)
        if minimum is None or maximum is None:
            raise ValueError("Cleaned source contains no dated rows")
        return minimum, maximum
    finally:
        parquet_file.close()


def derive_training_origins(
    source_start: date,
    fold: TemporalValidationFold,
) -> tuple[date, ...]:
    """Return every historical origin with at least a t+1 label by the fold cutoff."""

    last_origin = fold.forecast_origin - timedelta(days=min(FORECAST_HORIZONS))
    if source_start > last_origin:
        raise ValueError(f"Fold {fold.fold_id} has no eligible historical origins")
    return tuple(
        source_start + timedelta(days=offset)
        for offset in range((last_origin - source_start).days + 1)
    )


def _source_state(path: Path) -> tuple[int, int]:
    state = path.stat()
    return state.st_size, state.st_mtime_ns


def _configured_stores(config: FoldDatasetBuildConfig) -> tuple[int, ...]:
    stores = tuple(store for batch in config.store_batches for store in batch)
    if not stores or len(stores) != len(set(stores)):
        raise ValueError("store_batches must contain unique non-empty stores")
    return stores


def _require_available_outputs(
    paths: Sequence[FoldArtifactPaths],
    *,
    overwrite: bool,
) -> None:
    if overwrite:
        return
    for fold_paths in paths:
        for path in (
            fold_paths.training,
            fold_paths.validation,
            fold_paths.manifest,
        ):
            if path.exists():
                raise FileExistsError(path)


def _entity_sets(path: Path) -> tuple[set[int], set[int]]:
    stores: set[int] = set()
    items: set[int] = set()
    parquet_file = pq.ParquetFile(path)
    try:
        for batch in parquet_file.iter_batches(
            batch_size=131_072,
            columns=["store_nbr", "item_nbr"],
        ):
            stores.update(int(value) for value in batch.column(0).unique().to_pylist())
            items.update(int(value) for value in batch.column(1).unique().to_pylist())
    finally:
        parquet_file.close()
    return stores, items


def _partition_config(
    config: FoldDatasetBuildConfig,
    *,
    output_path: Path,
    manifest_path: Path,
    origins: tuple[date, ...],
) -> FeatureBuildConfig:
    return FeatureBuildConfig(
        source_path=config.source_path,
        output_path=output_path,
        manifest_path=manifest_path,
        forecast_origins=origins,
        store_batches=config.store_batches,
        max_items_per_store=config.max_items_per_store,
        allow_assumed_future_promotion=False,
        allow_assumed_future_holidays=False,
        overwrite=config.overwrite,
    )


def build_one_fold_dataset(
    config: FoldDatasetBuildConfig,
    fold: TemporalValidationFold,
    paths: FoldArtifactPaths,
    *,
    training_origins: tuple[date, ...] | None = None,
) -> dict[str, Any]:
    """Build one fold completely before the caller advances to the next fold."""

    if config.max_items_per_store is not None:
        raise ValueError("Approved fold builds require max_items_per_store=None")
    configured_stores = _configured_stores(config)
    if training_origins is None:
        source_start, _ = _source_date_bounds(config.source_path)
        training_origins = derive_training_origins(source_start, fold)
    if not training_origins:
        raise ValueError("At least one historical training origin is required")
    if max(training_origins) >= fold.forecast_origin:
        raise ValueError("Training origins must precede the fold forecast origin")

    _require_available_outputs((paths,), overwrite=config.overwrite)
    source_before = _source_state(config.source_path)
    training_config = _partition_config(
        config,
        output_path=paths.training,
        manifest_path=paths.manifest,
        origins=training_origins,
    )
    training_result = materialize_feature_dataset(
        training_config,
        forecast_date_cutoff=fold.forecast_origin,
        drop_targets_without_origin_history=True,
        bounded_memory_validation=True,
    )
    validation_config = _partition_config(
        config,
        output_path=paths.validation,
        manifest_path=paths.manifest,
        origins=(fold.forecast_origin,),
    )
    validation_result = materialize_feature_dataset(
        validation_config,
        drop_targets_without_origin_history=True,
        bounded_memory_validation=True,
    )

    training_validation = training_result["artifact_validation"]
    validation_validation = validation_result["artifact_validation"]
    if training_validation["forecast_date_max"] > fold.forecast_origin.isoformat():
        raise AssertionError("Training labels extend beyond the fold origin")
    if validation_validation["forecast_date_min"] != fold.validation_start.isoformat():
        raise AssertionError("Validation does not start at canonical O+1")
    if validation_validation["forecast_date_max"] != fold.validation_end.isoformat():
        raise AssertionError("Validation does not end at canonical O+16")
    if validation_validation["horizons"] != list(FORECAST_HORIZONS):
        raise AssertionError("Validation horizons must be exactly 1 through 16")
    if fold.validation_end >= FINAL_HOLDOUT.holdout_start:
        raise AssertionError("Final holdout would be exposed")

    training_stores, training_items = _entity_sets(paths.training)
    validation_stores, validation_items = _entity_sets(paths.validation)
    observed_stores = training_stores | validation_stores
    if observed_stores != set(configured_stores):
        raise AssertionError("Fold artifacts do not preserve configured store coverage")
    source_after = _source_state(config.source_path)
    if source_after != source_before:
        raise AssertionError("Cleaned source changed during fold materialization")

    manifest: dict[str, Any] = {
        "fold_id": fold.fold_id,
        "forecast_origin": fold.forecast_origin.isoformat(),
        "validation_start": fold.validation_start.isoformat(),
        "validation_end": fold.validation_end.isoformat(),
        "training_row_count": training_validation["rows"],
        "validation_row_count": validation_validation["rows"],
        "store_count": len(observed_stores),
        "item_count": len(training_items | validation_items),
        "horizons": list(FORECAST_HORIZONS),
        "max_items_per_store": config.max_items_per_store,
        "source_path": config.source_path.as_posix(),
        "source_not_mutated": True,
        "final_holdout_excluded": True,
        "ordered_schema": list(TRAINING_OUTPUT_COLUMNS),
        "training_origin_count": len(training_origins),
        "training_origin_start": min(training_origins).isoformat(),
        "training_origin_end": max(training_origins).isoformat(),
        "direct_horizon_aware": True,
        "recursive_feedback": False,
        "future_actual_leakage": False,
        "sparse_observed_rows_only": True,
        "negative_and_fractional_unit_sales_preserved": True,
        "configured_stores": list(configured_stores),
        "artifacts": {
            "training": paths.training.as_posix(),
            "validation": paths.validation.as_posix(),
        },
    }
    write_json_atomic(manifest, paths.manifest, overwrite=config.overwrite)
    return manifest


def build_approved_fold_datasets(
    config: FoldDatasetBuildConfig,
) -> tuple[dict[str, Any], ...]:
    """Build the approved folds serially, retaining only manifest metadata."""

    validate_approved_contract()
    if not config.source_path.is_file():
        raise FileNotFoundError(config.source_path)
    paths = approved_fold_artifact_paths(config.output_dir)
    _require_available_outputs(paths, overwrite=config.overwrite)
    source_start, _ = _source_date_bounds(config.source_path)
    manifests: list[dict[str, Any]] = []
    for fold, fold_paths in zip(APPROVED_FOLDS, paths, strict=True):
        manifests.append(
            build_one_fold_dataset(
                config,
                fold,
                fold_paths,
                training_origins=derive_training_origins(source_start, fold),
            )
        )
    return tuple(manifests)


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build model-ready training and validation Parquet per approved fold."
        )
    )
    parser.add_argument("--source-path", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    manifests = build_approved_fold_datasets(
        FoldDatasetBuildConfig(
            source_path=args.source_path,
            output_dir=args.output_dir,
            overwrite=args.overwrite,
        )
    )
    for manifest in manifests:
        print(
            (args.output_dir / f"fold_{manifest['fold_id']:02d}" / "manifest.json")
            .as_posix()
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
