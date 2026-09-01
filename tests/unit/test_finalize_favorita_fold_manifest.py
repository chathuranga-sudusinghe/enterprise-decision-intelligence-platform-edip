from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from pipelines.evaluation import run_favorita_lightgbm_single_fold as runner
from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FORECAST_HORIZONS,
    MODELING_TARGET_START,
)
from pipelines.features import build_favorita_fold_datasets as builder
from pipelines.features import finalize_favorita_fold_manifest as finalizer
from pipelines.features.favorita_model_ready import (
    OUTPUT_ARROW_SCHEMA,
    _fixture_source_frame,
)


def _existing_parquet_fixture(
    tmp_path: Path,
    *,
    omitted_origin: date | None = None,
) -> tuple[Path, Path, builder.FoldArtifactPaths]:
    fixture, fixture_origin = _fixture_source_frame()
    fold = APPROVED_FOLDS[0]
    canonical_origin = pd.Timestamp(fold.forecast_origin)
    early_origin = pd.Timestamp(MODELING_TARGET_START) - pd.Timedelta(days=1)

    early_fixture = fixture.copy()
    early_fixture["date"] += early_origin - fixture_origin
    late_fixture = fixture.copy()
    late_fixture["date"] += canonical_origin - fixture_origin
    source = pd.concat((early_fixture, late_fixture), ignore_index=True)

    source_path = tmp_path / "cleaned.parquet"
    source.to_parquet(source_path, index=False, row_group_size=37)
    output_dir = tmp_path / "favorita_2017_four_fold"
    paths = builder.approved_fold_artifact_paths(output_dir)[0]
    config = builder.FoldDatasetBuildConfig(
        source_path=source_path,
        output_dir=output_dir,
        store_batches=((1,),),
        canonical_contract=False,
    )
    builder.build_one_fold_dataset(
        config,
        fold,
        paths,
        training_origins=(
            MODELING_TARGET_START - timedelta(days=1),
            fold.forecast_origin - timedelta(days=1),
        ),
    )

    training_template = pq.read_table(paths.training).slice(0, 1).to_pandas()
    origins = [
        origin
        for origin in builder.canonical_training_origins(fold)
        if origin != omitted_origin
    ]
    training_rows: list[pd.DataFrame] = []
    for origin in origins:
        for horizon in FORECAST_HORIZONS:
            forecast_date = origin + timedelta(days=horizon)
            if not MODELING_TARGET_START <= forecast_date <= fold.forecast_origin:
                continue
            row = training_template.copy()
            row["forecast_origin"] = pd.Timestamp(origin)
            row["forecast_date"] = pd.Timestamp(forecast_date)
            row["forecast_horizon"] = horizon
            training_rows.append(row)
    canonical_training = pa.Table.from_pandas(
        pd.concat(training_rows, ignore_index=True),
        schema=OUTPUT_ARROW_SCHEMA,
        preserve_index=False,
    )
    pq.write_table(
        canonical_training,
        paths.training,
        row_group_size=37,
    )
    paths.manifest.unlink()
    return source_path, output_dir, paths


def test_finalizer_writes_only_missing_manifest(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_path, output_dir, paths = _existing_parquet_fixture(tmp_path)
    immutable_bytes = {
        path: path.read_bytes()
        for path in (source_path, paths.training, paths.validation)
    }

    manifest = finalizer.finalize_existing_fold_manifest(
        1,
        source_path=source_path,
        output_dir=output_dir,
        confirm_all_stores_processed=True,
        log_progress=True,
    )

    assert paths.manifest.is_file()
    assert json.loads(paths.manifest.read_text(encoding="utf-8")) == manifest
    validated = runner.validate_existing_fold(
        runner.SingleFoldEvaluationConfig(
            fold_id=1,
            fold_output_dir=output_dir,
            output_dir=tmp_path / "results",
        )
    )
    assert validated.manifest == manifest
    assert manifest["canonical_fold_id"] == 1
    assert manifest["artifact_root"] == output_dir.as_posix()
    assert manifest["modeling_target_start"] == "2017-01-01"
    assert manifest["modeling_target_end"] == "2017-07-30"
    assert manifest["configured_stores"] == list(range(1, 55))
    assert manifest["processed_stores"] == list(range(1, 55))
    assert manifest["observed_stores"] == [1]
    assert manifest["processed_store_evidence"] == (
        finalizer.PROCESSED_STORE_EVIDENCE
    )
    assert manifest["training_origin_count"] == len(
        builder.canonical_training_origins(APPROVED_FOLDS[0])
    )
    assert manifest["manifest_finalization"] == {
        "mode": "existing_parquets_only",
        "operator_confirmed_all_configured_stores_processed": True,
        "parquet_files_not_modified": True,
        "complete_training_origins_validated": True,
        "validation_dates_and_horizons_validated": True,
    }
    assert {
        path: path.read_bytes()
        for path in (source_path, paths.training, paths.validation)
    } == immutable_bytes
    assert "writing manifest.json only" in capsys.readouterr().out


def test_finalizer_refuses_missing_confirmation_and_existing_manifest(
    tmp_path: Path,
) -> None:
    source_path, output_dir, paths = _existing_parquet_fixture(tmp_path)

    with pytest.raises(ValueError, match="explicit confirmation"):
        finalizer.finalize_existing_fold_manifest(
            1,
            source_path=source_path,
            output_dir=output_dir,
        )
    assert not paths.manifest.exists()

    paths.manifest.write_text("{}\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        finalizer.finalize_existing_fold_manifest(
            1,
            source_path=source_path,
            output_dir=output_dir,
            confirm_all_stores_processed=True,
        )
    assert paths.manifest.read_text(encoding="utf-8") == "{}\n"


def test_finalizer_fails_closed_on_missing_intermediate_training_origin(
    tmp_path: Path,
) -> None:
    missing_origin = builder.canonical_training_origins(APPROVED_FOLDS[0])[50]
    source_path, output_dir, paths = _existing_parquet_fixture(
        tmp_path,
        omitted_origin=missing_origin,
    )
    training_bytes = paths.training.read_bytes()

    with pytest.raises(AssertionError, match="complete canonical daily sequence"):
        finalizer.finalize_existing_fold_manifest(
            1,
            source_path=source_path,
            output_dir=output_dir,
            confirm_all_stores_processed=True,
        )

    assert not paths.manifest.exists()
    assert paths.training.read_bytes() == training_bytes


def test_finalizer_cli_has_no_build_or_overwrite_path() -> None:
    args = finalizer._argument_parser().parse_args(
        ["--fold", "1", "--confirm-all-stores-processed"]
    )

    assert args.fold == 1
    assert not hasattr(args, "overwrite")
    assert not hasattr(args, "build")
    assert not hasattr(finalizer, "materialize_feature_dataset")

    with pytest.raises(SystemExit):
        finalizer._argument_parser().parse_args(["--fold", "1"])
    with pytest.raises(SystemExit):
        finalizer._argument_parser().parse_args(
            ["--fold", "5", "--confirm-all-stores-processed"]
        )
