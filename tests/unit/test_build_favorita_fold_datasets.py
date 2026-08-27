from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest

from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLD_ORIGINS,
    APPROVED_FOLDS,
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
    TemporalValidationFold,
    derive_target_window,
)
from pipelines.features import build_favorita_fold_datasets as builder
from pipelines.features.favorita_model_ready import (
    TRAINING_OUTPUT_COLUMNS,
    _fixture_source_frame,
)


EXPECTED_ORIGINS = (
    "2015-08-31",
    "2015-12-08",
    "2016-04-15",
    "2016-06-30",
    "2016-08-31",
    "2016-12-08",
    "2017-04-15",
    "2017-06-30",
)


def test_exactly_eight_canonical_fold_output_definitions(tmp_path: Path) -> None:
    paths = builder.approved_fold_artifact_paths(tmp_path / "folds")

    assert len(paths) == 8
    assert tuple(fold.fold_id for fold in paths) == tuple(range(1, 9))
    assert tuple(origin.isoformat() for origin in APPROVED_FOLD_ORIGINS) == (
        EXPECTED_ORIGINS
    )
    assert tuple(path.directory.name for path in paths) == tuple(
        f"fold_{fold_id:02d}" for fold_id in range(1, 9)
    )
    assert all(path.training.name == "training.parquet" for path in paths)
    assert all(path.validation.name == "validation.parquet" for path in paths)
    assert all(path.manifest.name == "manifest.json" for path in paths)


def test_all_store_no_item_cap_configuration_is_locked() -> None:
    config = builder.FoldDatasetBuildConfig()

    assert builder.ALL_FAVORITA_STORES == tuple(range(1, 55))
    assert config.store_batches == tuple((store,) for store in range(1, 55))
    assert config.max_items_per_store is None


def test_training_origins_are_daily_and_end_before_fold_origin() -> None:
    fold = APPROVED_FOLDS[0]
    source_start = fold.forecast_origin - timedelta(days=3)

    origins = builder.derive_training_origins(source_start, fold)

    assert origins == (
        fold.forecast_origin - timedelta(days=3),
        fold.forecast_origin - timedelta(days=2),
        fold.forecast_origin - timedelta(days=1),
    )


def _bounded_fold_fixture(tmp_path: Path) -> tuple[
    builder.FoldDatasetBuildConfig,
    TemporalValidationFold,
    builder.FoldArtifactPaths,
    tuple,
    bytes,
]:
    fixture, origin = _fixture_source_frame()
    canonical_origin = pd.Timestamp(APPROVED_FOLDS[0].forecast_origin)
    fixture["date"] = fixture["date"] + (canonical_origin - origin)
    origin = canonical_origin
    fixture.loc[
        fixture["date"] == origin - pd.Timedelta(days=1), "unit_sales"
    ] = -2.75
    source_path = tmp_path / "cleaned.parquet"
    fixture.to_parquet(source_path, index=False, row_group_size=37)
    source_bytes = source_path.read_bytes()
    validation_start, validation_end = derive_target_window(origin.date())
    fold = TemporalValidationFold(
        fold_id=1,
        forecast_origin=origin.date(),
        validation_start=validation_start,
        validation_end=validation_end,
    )
    config = builder.FoldDatasetBuildConfig(
        source_path=source_path,
        output_dir=tmp_path / "folds",
        store_batches=((1,),),
        max_items_per_store=None,
    )
    paths = builder.FoldArtifactPaths(
        fold_id=1,
        directory=config.output_dir / "fold_01",
        training=config.output_dir / "fold_01" / "training.parquet",
        validation=config.output_dir / "fold_01" / "validation.parquet",
        manifest=config.output_dir / "fold_01" / "manifest.json",
    )
    training_origins = (
        origin.date() - timedelta(days=2),
        origin.date() - timedelta(days=1),
    )
    return config, fold, paths, training_origins, source_bytes


def test_bounded_fold_build_enforces_temporal_and_artifact_contract(
    tmp_path: Path,
) -> None:
    config, fold, paths, training_origins, source_bytes = _bounded_fold_fixture(
        tmp_path
    )

    manifest = builder.build_one_fold_dataset(
        config,
        fold,
        paths,
        training_origins=training_origins,
    )

    training = pq.read_table(paths.training).to_pandas()
    validation = pq.read_table(paths.validation).to_pandas()
    assert tuple(training.columns) == TRAINING_OUTPUT_COLUMNS
    assert tuple(validation.columns) == TRAINING_OUTPUT_COLUMNS
    assert training["forecast_date"].max().date() <= fold.forecast_origin
    assert validation["forecast_origin"].dt.date.unique().tolist() == [
        fold.forecast_origin
    ]
    assert validation["forecast_date"].min().date() == fold.validation_start
    assert validation["forecast_date"].max().date() == fold.validation_end
    assert sorted(validation["forecast_horizon"].unique()) == list(
        FORECAST_HORIZONS
    )
    assert validation["forecast_date"].max().date() < FINAL_HOLDOUT.holdout_start
    assert (training["unit_sales"] == -2.75).any()
    assert config.source_path.read_bytes() == source_bytes
    assert manifest["source_not_mutated"] is True
    assert manifest["final_holdout_excluded"] is True
    assert manifest["store_count"] == 1
    assert manifest["max_items_per_store"] is None
    assert manifest["ordered_schema"] == list(TRAINING_OUTPUT_COLUMNS)
    assert json.loads(paths.manifest.read_text(encoding="utf-8")) == manifest


def test_build_rejects_item_cap(tmp_path: Path) -> None:
    config, fold, paths, training_origins, _ = _bounded_fold_fixture(tmp_path)
    capped = builder.FoldDatasetBuildConfig(
        source_path=config.source_path,
        output_dir=config.output_dir,
        store_batches=config.store_batches,
        max_items_per_store=1,
    )

    with pytest.raises(ValueError, match="max_items_per_store=None"):
        builder.build_one_fold_dataset(
            capped,
            fold,
            paths,
            training_origins=training_origins,
        )


def test_orchestration_completes_one_fold_before_next(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "source.parquet"
    source_path.write_bytes(b"fixture")
    config = builder.FoldDatasetBuildConfig(
        source_path=source_path,
        output_dir=tmp_path / "folds",
    )
    active = 0
    completed: list[int] = []

    def fake_build(
        received_config: builder.FoldDatasetBuildConfig,
        fold: TemporalValidationFold,
        paths: builder.FoldArtifactPaths,
        *,
        training_origins: tuple | None = None,
    ) -> dict[str, int]:
        nonlocal active
        assert received_config is config
        assert training_origins
        assert active == 0
        assert completed == list(range(1, fold.fold_id))
        active += 1
        completed.append(paths.fold_id)
        active -= 1
        return {"fold_id": fold.fold_id}

    monkeypatch.setattr(builder, "build_one_fold_dataset", fake_build)
    monkeypatch.setattr(
        builder,
        "_source_date_bounds",
        lambda _path: (
            APPROVED_FOLDS[0].forecast_origin - timedelta(days=2),
            APPROVED_FOLDS[-1].validation_end,
        ),
    )

    manifests = builder.build_approved_fold_datasets(config)

    assert completed == list(range(1, 9))
    assert tuple(item["fold_id"] for item in manifests) == tuple(range(1, 9))


def test_overwrite_protection_preflights_all_folds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "source.parquet"
    source_path.write_bytes(b"fixture")
    config = builder.FoldDatasetBuildConfig(
        source_path=source_path,
        output_dir=tmp_path / "folds",
    )
    occupied = config.output_dir / "fold_08" / "validation.parquet"
    occupied.parent.mkdir(parents=True)
    occupied.write_bytes(b"do-not-overwrite")
    called = False

    def fake_build(*args: object, **kwargs: object) -> dict[str, int]:
        nonlocal called
        called = True
        return {"fold_id": 1}

    monkeypatch.setattr(builder, "build_one_fold_dataset", fake_build)

    with pytest.raises(FileExistsError, match="validation.parquet"):
        builder.build_approved_fold_datasets(config)

    assert called is False
    assert occupied.read_bytes() == b"do-not-overwrite"
