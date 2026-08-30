"""Finalize one canonical Favorita manifest from existing Parquet artifacts only."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FORECAST_HORIZONS,
)
from pipelines.features.build_favorita_fold_datasets import (
    ALL_FAVORITA_STORES,
    CANONICAL_FOLD_IDS,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SOURCE_PATH,
    FoldDatasetBuildConfig,
    _artifact_footer_validation,
    _entity_sets,
    _source_state,
    _validate_fold_artifact_boundaries,
    approved_fold_artifact_paths,
    canonical_training_origins,
    fold_manifest_payload,
    selected_approved_folds,
    validate_canonical_fold_output_dir,
)
from pipelines.features.favorita_model_ready import write_json_atomic

PROCESSED_STORE_EVIDENCE = (
    "operator_confirmed_original_canonical_materialization"
)


def _normalise_date(value: Any, *, column: str) -> date:
    if value is None:
        raise AssertionError(f"{column} contains null values")
    if hasattr(value, "date"):
        value = value.date()
    if not isinstance(value, date):
        raise AssertionError(f"{column} contains a non-date value")
    return value


def _unique_dates(path: Path, column: str) -> set[date]:
    values: set[date] = set()
    parquet_file = pq.ParquetFile(path)
    try:
        for batch in parquet_file.iter_batches(
            batch_size=131_072,
            columns=[column],
        ):
            values.update(
                _normalise_date(value, column=column)
                for value in batch.column(0).unique().to_pylist()
            )
    finally:
        parquet_file.close()
    return values


def _unique_integers(path: Path, column: str) -> set[int]:
    values: set[int] = set()
    parquet_file = pq.ParquetFile(path)
    try:
        for batch in parquet_file.iter_batches(
            batch_size=131_072,
            columns=[column],
        ):
            unique_values = batch.column(0).unique().to_pylist()
            if any(value is None for value in unique_values):
                raise AssertionError(f"{column} contains null values")
            values.update(int(value) for value in unique_values)
    finally:
        parquet_file.close()
    return values


def finalize_existing_fold_manifest(
    fold_id: int,
    *,
    source_path: Path = DEFAULT_SOURCE_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    confirm_all_stores_processed: bool = False,
    log_progress: bool = False,
) -> dict[str, Any]:
    """Validate existing canonical Parquets and create only their missing manifest."""

    validate_canonical_fold_output_dir(output_dir)
    fold = selected_approved_folds((fold_id,))[0]
    if not confirm_all_stores_processed:
        raise ValueError(
            "Manifest recovery requires explicit confirmation that the original "
            "canonical materialization processed all stores 1 through 54"
        )
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    paths_by_id = {
        paths.fold_id: paths
        for paths in approved_fold_artifact_paths(output_dir)
    }
    paths = paths_by_id[fold.fold_id]
    if paths.manifest.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing fold manifest: {paths.manifest}"
        )
    for artifact_path in (paths.training, paths.validation):
        if not artifact_path.is_file():
            raise FileNotFoundError(artifact_path)

    progress_prefix = f"[Fold {fold.fold_id}/{len(APPROVED_FOLDS)}]"

    def progress(message: str) -> None:
        if log_progress:
            print(f"{progress_prefix} {message}", flush=True)

    immutable_paths = (source_path, paths.training, paths.validation)
    state_before = {path: _source_state(path) for path in immutable_paths}

    progress("validating Parquet schemas, row counts, and boundaries...")
    training_validation = _artifact_footer_validation(paths.training)
    validation_validation = _artifact_footer_validation(paths.validation)
    _validate_fold_artifact_boundaries(
        training_validation,
        validation_validation,
        fold,
    )

    progress("validating the complete daily training-origin sequence...")
    expected_training_origins = canonical_training_origins(fold)
    actual_training_origins = _unique_dates(
        paths.training,
        "forecast_origin",
    )
    if actual_training_origins != set(expected_training_origins):
        missing = sorted(set(expected_training_origins) - actual_training_origins)
        unexpected = sorted(actual_training_origins - set(expected_training_origins))
        raise AssertionError(
            "Training origins are not the complete canonical daily sequence; "
            f"missing={missing[:5]}, unexpected={unexpected[:5]}"
        )

    progress("validating validation origin, dates, and horizons...")
    if _unique_dates(paths.validation, "forecast_origin") != {
        fold.forecast_origin
    }:
        raise AssertionError("Validation forecast origins are not canonical")
    expected_validation_dates = {
        fold.validation_start + timedelta(days=offset)
        for offset in range(len(FORECAST_HORIZONS))
    }
    if _unique_dates(paths.validation, "forecast_date") != expected_validation_dates:
        raise AssertionError("Validation dates are not the complete O+1 through O+16")
    if _unique_integers(paths.validation, "forecast_horizon") != set(
        FORECAST_HORIZONS
    ):
        raise AssertionError("Validation horizons are not exactly 1 through 16")

    progress("validating observed store and item evidence...")
    training_stores, training_items = _entity_sets(paths.training)
    validation_stores, validation_items = _entity_sets(paths.validation)
    observed_stores = training_stores | validation_stores
    observed_items = training_items | validation_items
    if not observed_stores:
        raise AssertionError("Fold artifacts contain no observed stores")
    if not observed_items:
        raise AssertionError("Fold artifacts contain no observed items")
    if not observed_stores.issubset(set(ALL_FAVORITA_STORES)):
        raise AssertionError("Fold artifacts contain a store outside 1 through 54")

    if {
        path: _source_state(path) for path in immutable_paths
    } != state_before:
        raise AssertionError("Source or existing Parquet artifacts changed during validation")

    config = FoldDatasetBuildConfig(
        source_path=source_path,
        output_dir=output_dir,
        overwrite=False,
        canonical_contract=True,
    )
    manifest = fold_manifest_payload(
        config=config,
        fold=fold,
        paths=paths,
        training_origins=expected_training_origins,
        experiment_subset=CANONICAL_FOLD_IDS,
        configured_stores=ALL_FAVORITA_STORES,
        observed_stores=observed_stores,
        item_count=len(observed_items),
        training_validation=training_validation,
        validation_validation=validation_validation,
        processed_store_evidence=PROCESSED_STORE_EVIDENCE,
    )
    manifest["manifest_finalization"] = {
        "mode": "existing_parquets_only",
        "operator_confirmed_all_configured_stores_processed": True,
        "parquet_files_not_modified": True,
        "complete_training_origins_validated": True,
        "validation_dates_and_horizons_validated": True,
    }

    progress("writing manifest.json only...")
    write_json_atomic(manifest, paths.manifest, overwrite=False)
    progress(f"manifest written: {paths.manifest.as_posix()}")
    if log_progress:
        print(
            f"{progress_prefix} training rows: {manifest['training_row_count']}",
            flush=True,
        )
        print(
            f"{progress_prefix} validation rows: {manifest['validation_row_count']}",
            flush=True,
        )
        print(
            f"{progress_prefix} observed stores: "
            f"{manifest['observed_store_count']} of 54",
            flush=True,
        )
    return manifest


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate existing canonical Favorita fold Parquets and create only "
            "their missing manifest.json. This command cannot build fold artifacts."
        )
    )
    parser.add_argument(
        "--fold",
        type=int,
        choices=CANONICAL_FOLD_IDS,
        required=True,
    )
    parser.add_argument("--source-path", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--confirm-all-stores-processed",
        action="store_true",
        required=True,
        help=(
            "Confirm that the original canonical materialization processed "
            "stores 1 through 54, including stores with zero observed rows."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    finalize_existing_fold_manifest(
        args.fold,
        source_path=args.source_path,
        output_dir=args.output_dir,
        confirm_all_stores_processed=args.confirm_all_stores_processed,
        log_progress=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
