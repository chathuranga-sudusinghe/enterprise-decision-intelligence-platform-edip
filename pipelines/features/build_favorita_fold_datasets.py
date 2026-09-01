"""Build the four canonical Favorita fold datasets without fitting a model."""

from __future__ import annotations

import argparse
import json
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
    MODELING_TARGET_END,
    MODELING_TARGET_START,
    TemporalValidationFold,
    validate_approved_contract,
)
from pipelines.features.favorita_model_ready import (
    OUTPUT_ARROW_SCHEMA,
    TRAINING_OUTPUT_COLUMNS,
    FeatureBuildConfig,
    materialize_feature_dataset,
    write_json_atomic,
)

DEFAULT_SOURCE_PATH = Path(
    "data/processed/favorita_cleaned/favorita_cleaned.parquet"
)
DEFAULT_OUTPUT_DIR = Path("artifacts/features/favorita_2017_four_fold")
SUPERSEDED_FOUR_FOLD_OUTPUT_DIR = Path("artifacts/features/favorita_four_fold")
HISTORICAL_OUTPUT_DIR = Path("artifacts/features/favorita_folds")
INCOMPATIBLE_OUTPUT_DIRS: tuple[Path, ...] = (
    SUPERSEDED_FOUR_FOLD_OUTPUT_DIR,
    HISTORICAL_OUTPUT_DIR,
)
ALL_FAVORITA_STORES: tuple[int, ...] = tuple(range(1, 55))
ALL_STORE_BATCHES: tuple[tuple[int, ...], ...] = tuple(
    (store_nbr,) for store_nbr in ALL_FAVORITA_STORES
)
CANONICAL_FOLD_IDS: tuple[int, ...] = (1, 2, 3, 4)
EXECUTION_SCOPE = "canonical_2017_four_fold"
CANONICAL_VALIDATION_DESIGN = "four_fold_expanding_window"
COMPUTE_CONSTRAINT_REASON = (
    "Fold 4 materialization and existing-adapter training succeeded on the "
    "approved 64 GB CPU machine without swap."
)


@dataclass(frozen=True, slots=True)
class FoldDatasetBuildConfig:
    """Inputs for the approved fold-wise model-ready artifact build."""

    source_path: Path = DEFAULT_SOURCE_PATH
    output_dir: Path = DEFAULT_OUTPUT_DIR
    store_batches: tuple[tuple[int, ...], ...] = ALL_STORE_BATCHES
    max_items_per_store: int | None = None
    overwrite: bool = False
    canonical_contract: bool = True


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
    """Return the exact ordered four-fold output definition."""

    validate_approved_contract()
    return tuple(
        FoldArtifactPaths(
            fold_id=fold.fold_id,
            directory=output_dir / f"fold_{fold.fold_id:02d}",
            training=output_dir / f"fold_{fold.fold_id:02d}" / "training.parquet",
            validation=output_dir / f"fold_{fold.fold_id:02d}" / "validation.parquet",
            manifest=output_dir / f"fold_{fold.fold_id:02d}" / "manifest.json",
        )
        for fold in APPROVED_FOLDS
    )


def validate_canonical_fold_output_dir(output_dir: Path) -> None:
    """Reject incompatible historical roots and anything nested beneath them."""

    resolved = output_dir.resolve()
    for incompatible_output_dir in INCOMPATIBLE_OUTPUT_DIRS:
        incompatible = incompatible_output_dir.resolve()
        if resolved == incompatible or incompatible in resolved.parents:
            raise ValueError(
                "Redesigned canonical artifacts must not use an incompatible "
                f"artifact root: {incompatible_output_dir.as_posix()}"
            )


def selected_approved_folds(
    fold_ids: Sequence[int] = CANONICAL_FOLD_IDS,
) -> tuple[TemporalValidationFold, ...]:
    """Resolve an explicit execution subset without changing APPROVED_FOLDS."""

    validate_approved_contract()
    requested_ids = tuple(fold_ids)
    if not requested_ids:
        raise ValueError("At least one approved fold ID must be selected")
    if len(requested_ids) != len(set(requested_ids)):
        raise ValueError("Requested fold IDs must be unique")
    approved_by_id = {fold.fold_id: fold for fold in APPROVED_FOLDS}
    invalid_ids = sorted(set(requested_ids) - approved_by_id.keys())
    if invalid_ids:
        raise ValueError(f"Unknown approved fold IDs: {invalid_ids}")
    return tuple(approved_by_id[fold_id] for fold_id in requested_ids)


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
    """Return daily origins whose targets start at the canonical scope boundary."""

    first_origin = MODELING_TARGET_START - timedelta(days=min(FORECAST_HORIZONS))
    last_origin = fold.forecast_origin - timedelta(days=min(FORECAST_HORIZONS))
    if source_start > first_origin:
        raise ValueError(
            "Cleaned source must begin before the first canonical training origin"
        )
    return tuple(
        first_origin + timedelta(days=offset)
        for offset in range((last_origin - first_origin).days + 1)
    )


def _source_state(path: Path) -> tuple[int, int]:
    state = path.stat()
    return state.st_size, state.st_mtime_ns


def _configured_stores(config: FoldDatasetBuildConfig) -> tuple[int, ...]:
    stores = tuple(store for batch in config.store_batches for store in batch)
    if not stores or len(stores) != len(set(stores)):
        raise ValueError("store_batches must contain unique non-empty stores")
    return stores


def canonical_training_origins(
    fold: TemporalValidationFold,
) -> tuple[date, ...]:
    """Return the exact complete daily origin sequence for one canonical fold."""

    return derive_training_origins(
        MODELING_TARGET_START - timedelta(days=min(FORECAST_HORIZONS)),
        fold,
    )


def _require_canonical_build_config(config: FoldDatasetBuildConfig) -> None:
    validate_canonical_fold_output_dir(config.output_dir)
    if not config.canonical_contract:
        return
    if _configured_stores(config) != ALL_FAVORITA_STORES:
        raise ValueError("Canonical fold builds require exactly stores 1 through 54")
    if config.max_items_per_store is not None:
        raise ValueError("Canonical fold builds require max_items_per_store=None")


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


def _artifact_footer_validation(path: Path) -> dict[str, Any]:
    """Validate reusable artifact structure from Parquet footer metadata only."""

    parquet_file = pq.ParquetFile(path)
    try:
        if not parquet_file.schema_arrow.equals(OUTPUT_ARROW_SCHEMA):
            raise AssertionError("Output Arrow schema differs from declared contract")
        if parquet_file.metadata.num_rows <= 0:
            raise AssertionError("Feature artifact contains no rows")

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
                    raise AssertionError(
                        f"Reusable artifact lacks {column} footer statistics"
                    )
                if statistics.null_count:
                    raise AssertionError(f"Reusable artifact has null {column} values")
                minima.append(statistics.min)
                maxima.append(statistics.max)
            bounds[column] = (min(minima), max(maxima))

        def iso_date(value: Any) -> str:
            if hasattr(value, "date"):
                value = value.date()
            return value.isoformat()

        minimum_horizon, maximum_horizon = bounds["forecast_horizon"]
        return {
            "rows": parquet_file.metadata.num_rows,
            "forecast_origin_min": iso_date(bounds["forecast_origin"][0]),
            "forecast_origin_max": iso_date(bounds["forecast_origin"][1]),
            "forecast_date_min": iso_date(bounds["forecast_date"][0]),
            "forecast_date_max": iso_date(bounds["forecast_date"][1]),
            "horizons": list(range(int(minimum_horizon), int(maximum_horizon) + 1)),
            "schema": {
                field.name: str(field.type) for field in parquet_file.schema_arrow
            },
        }
    finally:
        parquet_file.close()


def _existing_artifact_result(
    path: Path,
    *,
    processed_stores: Sequence[int],
) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return {
        "creation_status": "reused",
        "processed_stores": list(processed_stores),
        "artifact_validation": _artifact_footer_validation(path),
    }


def _load_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Fold manifest must contain a JSON object: {path}")
    return payload


def _manifest_matches_reusable_fold(
    manifest: dict[str, Any],
    *,
    fold: TemporalValidationFold,
    config: FoldDatasetBuildConfig,
    training_origins: tuple[date, ...],
    experiment_subset: tuple[int, ...],
    configured_stores: tuple[int, ...],
    observed_stores: tuple[int, ...],
    training_validation: dict[str, Any],
    validation_validation: dict[str, Any],
) -> bool:
    return all(
        (
            manifest.get("canonical_fold_id") == fold.fold_id,
            manifest.get("canonical_fold_count") == len(APPROVED_FOLDS),
            manifest.get("forecast_origin") == fold.forecast_origin.isoformat(),
            manifest.get("validation_start") == fold.validation_start.isoformat(),
            manifest.get("validation_end") == fold.validation_end.isoformat(),
            manifest.get("artifact_root") == config.output_dir.as_posix(),
            manifest.get("modeling_target_start") == MODELING_TARGET_START.isoformat(),
            manifest.get("modeling_target_end") == MODELING_TARGET_END.isoformat(),
            manifest.get("training_target_start") == MODELING_TARGET_START.isoformat(),
            manifest.get("training_target_end") == fold.forecast_origin.isoformat(),
            manifest.get("canonical_contract_enforced") == config.canonical_contract,
            manifest.get("training_row_count") == training_validation["rows"],
            manifest.get("validation_row_count") == validation_validation["rows"],
            manifest.get("experiment_subset") == list(experiment_subset),
            manifest.get("execution_scope")
            == (
                EXECUTION_SCOPE
                if config.canonical_contract
                else "synthetic_test_fixture"
            ),
            manifest.get("canonical_validation_design") == CANONICAL_VALIDATION_DESIGN,
            manifest.get("training_origin_count") == len(training_origins),
            manifest.get("training_origin_start")
            == training_origins[0].isoformat(),
            manifest.get("training_origin_end")
            == training_origins[-1].isoformat(),
            manifest.get("configured_store_count") == len(configured_stores),
            manifest.get("max_items_per_store") is None,
            manifest.get("configured_stores") == list(configured_stores),
            manifest.get("processed_store_count") == len(configured_stores),
            manifest.get("processed_stores") == list(configured_stores),
            manifest.get("store_count") == len(observed_stores),
            manifest.get("observed_store_count") == len(observed_stores),
            manifest.get("observed_stores") == list(observed_stores),
            (
                not config.canonical_contract
                or manifest.get("configured_store_count") == len(ALL_FAVORITA_STORES)
            ),
            (
                not config.canonical_contract
                or manifest.get("processed_store_count") == len(ALL_FAVORITA_STORES)
            ),
            (
                not config.canonical_contract
                or manifest.get("configured_stores") == list(ALL_FAVORITA_STORES)
            ),
            manifest.get("final_holdout_excluded") is True,
            manifest.get("future_actual_leakage") is False,
            manifest.get("ordered_schema") == list(TRAINING_OUTPUT_COLUMNS),
        )
    )


def _validate_fold_artifact_boundaries(
    training_validation: dict[str, Any],
    validation_validation: dict[str, Any],
    fold: TemporalValidationFold,
) -> None:
    if training_validation["forecast_date_min"] != MODELING_TARGET_START.isoformat():
        raise AssertionError(
            "Training labels do not start at "
            f"{MODELING_TARGET_START.isoformat()}"
        )
    if training_validation["forecast_date_max"] != fold.forecast_origin.isoformat():
        raise AssertionError("Training labels do not end at the fold origin")
    if validation_validation.get("forecast_origin_min") not in (
        None,
        fold.forecast_origin.isoformat(),
    ):
        raise AssertionError("Validation forecast origin is not canonical")
    if validation_validation.get("forecast_origin_max") not in (
        None,
        fold.forecast_origin.isoformat(),
    ):
        raise AssertionError("Validation includes a non-canonical forecast origin")
    if validation_validation["forecast_date_min"] != fold.validation_start.isoformat():
        raise AssertionError("Validation does not start at canonical O+1")
    if validation_validation["forecast_date_max"] != fold.validation_end.isoformat():
        raise AssertionError("Validation does not end at canonical O+16")
    if validation_validation["horizons"] != list(FORECAST_HORIZONS):
        raise AssertionError("Validation horizons must be exactly 1 through 16")
    if fold.validation_end >= FINAL_HOLDOUT.holdout_start:
        raise AssertionError("Final holdout would be exposed")


def fold_manifest_payload(
    *,
    config: FoldDatasetBuildConfig,
    fold: TemporalValidationFold,
    paths: FoldArtifactPaths,
    training_origins: tuple[date, ...],
    experiment_subset: tuple[int, ...],
    configured_stores: tuple[int, ...],
    observed_stores: set[int],
    item_count: int,
    training_validation: dict[str, Any],
    validation_validation: dict[str, Any],
    processed_store_evidence: str,
) -> dict[str, Any]:
    """Return the shared canonical fold-manifest structure."""

    return {
        "fold_id": fold.fold_id,
        "canonical_fold_id": fold.fold_id,
        "canonical_fold_count": len(APPROVED_FOLDS),
        "canonical_contract_enforced": config.canonical_contract,
        "experiment_subset": list(experiment_subset),
        "execution_scope": (
            EXECUTION_SCOPE if config.canonical_contract else "synthetic_test_fixture"
        ),
        "artifact_root": config.output_dir.as_posix(),
        "canonical_validation_design": CANONICAL_VALIDATION_DESIGN,
        "compute_constraint_reason": COMPUTE_CONSTRAINT_REASON,
        "forecast_origin": fold.forecast_origin.isoformat(),
        "validation_start": fold.validation_start.isoformat(),
        "validation_end": fold.validation_end.isoformat(),
        "modeling_target_start": MODELING_TARGET_START.isoformat(),
        "modeling_target_end": MODELING_TARGET_END.isoformat(),
        "training_target_start": training_validation["forecast_date_min"],
        "training_target_end": training_validation["forecast_date_max"],
        "training_row_count": training_validation["rows"],
        "validation_row_count": validation_validation["rows"],
        "store_count": len(observed_stores),
        "configured_store_count": len(configured_stores),
        "observed_store_count": len(observed_stores),
        "observed_stores": sorted(observed_stores),
        "processed_store_count": len(configured_stores),
        "processed_stores": list(configured_stores),
        "processed_store_evidence": processed_store_evidence,
        "item_count": item_count,
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
    log_progress: bool = False,
    experiment_subset: tuple[int, ...] = CANONICAL_FOLD_IDS,
) -> dict[str, Any]:
    """Build one fold completely before the caller advances to the next fold."""

    _require_canonical_build_config(config)
    if config.max_items_per_store is not None:
        raise ValueError("Fold builds require max_items_per_store=None")
    configured_stores = _configured_stores(config)
    if training_origins is None:
        source_start, _ = _source_date_bounds(config.source_path)
        training_origins = derive_training_origins(source_start, fold)
    if not training_origins:
        raise ValueError("At least one historical training origin is required")
    if config.canonical_contract and training_origins != canonical_training_origins(
        fold
    ):
        raise ValueError(
            "Canonical fold training_origins must be the complete daily sequence"
        )
    if max(training_origins) >= fold.forecast_origin:
        raise ValueError("Training origins must precede the fold forecast origin")
    if fold.fold_id not in experiment_subset:
        raise ValueError("Fold must belong to the declared experiment subset")

    progress_prefix = f"[Fold {fold.fold_id}/{len(APPROVED_FOLDS)}]"
    if log_progress:
        print(
            f"{progress_prefix} training origins: {len(training_origins)}",
            flush=True,
        )
    source_before = _source_state(config.source_path)
    existing_manifest = _load_manifest(paths.manifest)
    artifact_presence = (
        paths.training.exists(),
        paths.validation.exists(),
        paths.manifest.exists(),
    )
    if any(artifact_presence) and not all(artifact_presence):
        if not config.overwrite:
            raise ValueError(
                "Existing canonical fold artifacts are incomplete; both Parquet "
                "files and manifest.json are required"
            )
        existing_manifest = None
    if existing_manifest is not None:
        reuse_processed_stores = tuple(existing_manifest.get("processed_stores", ()))
    else:
        reuse_processed_stores = ()

    def reusable_result(path: Path) -> dict[str, Any] | None:
        try:
            return _existing_artifact_result(
                path,
                processed_stores=reuse_processed_stores,
            )
        except (OSError, ValueError, AssertionError) as error:
            if not config.overwrite:
                raise ValueError(
                    f"Existing fold artifact is invalid: {path}"
                ) from error
            return None

    training_result = reusable_result(paths.training)
    validation_result = reusable_result(paths.validation)
    if (
        training_result is not None
        and validation_result is not None
        and existing_manifest is not None
    ):
        training_validation = training_result["artifact_validation"]
        validation_validation = validation_result["artifact_validation"]
        try:
            _validate_fold_artifact_boundaries(
                training_validation,
                validation_validation,
                fold,
            )
        except AssertionError as error:
            if not config.overwrite:
                raise ValueError(
                    "Existing fold artifacts do not match canonical boundaries"
                ) from error
            training_result = None
            validation_result = None
        if (
            training_result is not None
            and validation_result is not None
            and existing_manifest is not None
        ):
            training_stores, _ = _entity_sets(paths.training)
            validation_stores, _ = _entity_sets(paths.validation)
            observed_stores = tuple(sorted(training_stores | validation_stores))
            if _manifest_matches_reusable_fold(
                existing_manifest,
                fold=fold,
                config=config,
                training_origins=training_origins,
                experiment_subset=experiment_subset,
                configured_stores=configured_stores,
                observed_stores=observed_stores,
                training_validation=training_validation,
                validation_validation=validation_validation,
            ):
                if _source_state(config.source_path) != source_before:
                    raise AssertionError(
                        "Cleaned source changed during fold validation"
                    )
                if log_progress:
                    print(
                        f"{progress_prefix} validated existing artifacts — reusing",
                        flush=True,
                    )
                return existing_manifest
        if not config.overwrite:
            raise ValueError(
                "Existing fold manifest does not match the complete canonical "
                "four-fold contract"
            )
        training_result = None
        validation_result = None
    elif any(artifact_presence):
        if not config.overwrite:
            raise ValueError(
                "Existing fold artifacts cannot be reused without a matching "
                "canonical manifest"
            )
        training_result = None
        validation_result = None

    if training_result is None:
        training_config = _partition_config(
            config,
            output_path=paths.training,
            manifest_path=paths.manifest,
            origins=training_origins,
        )
        if log_progress:
            print(f"{progress_prefix} building training.parquet...", flush=True)
        training_result = materialize_feature_dataset(
            training_config,
            forecast_date_cutoff=fold.forecast_origin,
            drop_targets_without_origin_history=True,
            bounded_memory_validation=True,
            reuse_source_across_origins=True,
            progress_prefix=progress_prefix if log_progress else None,
            progress_phase="training",
        )
    if log_progress:
        print(
            f"{progress_prefix} training rows: "
            f"{training_result['artifact_validation']['rows']}",
            flush=True,
        )
    if validation_result is None:
        validation_config = _partition_config(
            config,
            output_path=paths.validation,
            manifest_path=paths.manifest,
            origins=(fold.forecast_origin,),
        )
        if log_progress:
            print(f"{progress_prefix} building validation.parquet...", flush=True)
        validation_result = materialize_feature_dataset(
            validation_config,
            drop_targets_without_origin_history=True,
            bounded_memory_validation=True,
            reuse_source_across_origins=True,
            progress_prefix=progress_prefix if log_progress else None,
            progress_phase="validation",
        )
    if log_progress:
        print(
            f"{progress_prefix} validation rows: "
            f"{validation_result['artifact_validation']['rows']}",
            flush=True,
        )

    training_validation = training_result["artifact_validation"]
    validation_validation = validation_result["artifact_validation"]
    _validate_fold_artifact_boundaries(
        training_validation,
        validation_validation,
        fold,
    )

    configured_store_set = set(configured_stores)
    for partition, result in (
        ("Training", training_result),
        ("Validation", validation_result),
    ):
        if set(result["processed_stores"]) != configured_store_set:
            raise AssertionError(
                f"{partition} materialization skipped configured stores"
            )

    training_stores, training_items = _entity_sets(paths.training)
    validation_stores, validation_items = _entity_sets(paths.validation)
    observed_stores = training_stores | validation_stores
    if not observed_stores.issubset(configured_store_set):
        raise AssertionError("Fold artifacts contain an unconfigured store")
    source_after = _source_state(config.source_path)
    if source_after != source_before:
        raise AssertionError("Cleaned source changed during fold materialization")

    manifest = fold_manifest_payload(
        config=config,
        fold=fold,
        paths=paths,
        training_origins=training_origins,
        experiment_subset=experiment_subset,
        configured_stores=configured_stores,
        observed_stores=observed_stores,
        item_count=len(training_items | validation_items),
        training_validation=training_validation,
        validation_validation=validation_validation,
        processed_store_evidence="materializer_processed_stores",
    )
    write_json_atomic(
        manifest,
        paths.manifest,
        overwrite=config.overwrite or paths.manifest.exists(),
    )
    artifacts_reused = (
        training_result["creation_status"] == "reused"
        and validation_result["creation_status"] == "reused"
    )
    if log_progress:
        if artifacts_reused:
            print(
                f"{progress_prefix} validated existing artifacts — reusing",
                flush=True,
            )
        else:
            print(f"{progress_prefix} completed", flush=True)
    return manifest


def build_approved_fold_datasets(
    config: FoldDatasetBuildConfig,
    *,
    fold_ids: Sequence[int] = CANONICAL_FOLD_IDS,
) -> tuple[dict[str, Any], ...]:
    """Build selected canonical folds serially, retaining only manifest metadata."""

    validate_approved_contract()
    if not config.source_path.is_file():
        raise FileNotFoundError(config.source_path)
    selected_folds = selected_approved_folds(fold_ids)
    paths_by_id = {
        paths.fold_id: paths
        for paths in approved_fold_artifact_paths(config.output_dir)
    }
    source_start: date | None = None
    manifests: list[dict[str, Any]] = []
    for fold in selected_folds:
        fold_paths = paths_by_id[fold.fold_id]
        progress_prefix = f"[Fold {fold.fold_id}/{len(APPROVED_FOLDS)}]"
        print(f"{progress_prefix} deriving training origins...", flush=True)
        if source_start is None:
            source_start, _ = _source_date_bounds(config.source_path)
        manifests.append(
            build_one_fold_dataset(
                config,
                fold,
                fold_paths,
                training_origins=derive_training_origins(source_start, fold),
                log_progress=True,
                experiment_subset=CANONICAL_FOLD_IDS,
            )
        )
    print(f"Artifact directory: {config.output_dir.as_posix()}", flush=True)
    return tuple(manifests)


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build model-ready training and validation Parquet per approved fold."
        )
    )
    parser.add_argument("--source-path", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--folds",
        nargs="+",
        type=int,
        default=list(CANONICAL_FOLD_IDS),
        help="Approved canonical fold IDs to materialize or reuse.",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    build_approved_fold_datasets(
        FoldDatasetBuildConfig(
            source_path=args.source_path,
            output_dir=args.output_dir,
            overwrite=args.overwrite,
        ),
        fold_ids=args.folds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
