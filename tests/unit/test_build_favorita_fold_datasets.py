from __future__ import annotations

import json
from dataclasses import replace
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
    MODELING_TARGET_END,
    MODELING_TARGET_START,
    TemporalValidationFold,
    derive_target_window,
)
from pipelines.features import build_favorita_fold_datasets as builder
from pipelines.features.favorita_model_ready import (
    TRAINING_OUTPUT_COLUMNS,
    _fixture_source_frame,
)

EXPECTED_ORIGINS = (
    "2017-02-28",
    "2017-04-14",
    "2017-05-31",
    "2017-07-14",
)


def test_exactly_four_canonical_fold_output_definitions(tmp_path: Path) -> None:
    paths = builder.approved_fold_artifact_paths(tmp_path / "folds")

    assert len(paths) == 4
    assert tuple(fold.fold_id for fold in paths) == tuple(range(1, 5))
    assert tuple(origin.isoformat() for origin in APPROVED_FOLD_ORIGINS) == (
        EXPECTED_ORIGINS
    )
    assert tuple(path.directory.name for path in paths) == tuple(
        f"fold_{fold_id:02d}" for fold_id in range(1, 5)
    )
    assert all(path.training.name == "training.parquet" for path in paths)
    assert all(path.validation.name == "validation.parquet" for path in paths)
    assert all(path.manifest.name == "manifest.json" for path in paths)
    assert APPROVED_FOLDS[-1].validation_end == MODELING_TARGET_END
    assert all(
        fold.validation_end < FINAL_HOLDOUT.holdout_start
        for fold in APPROVED_FOLDS
    )


def test_canonical_subset_is_exactly_folds_1_through_4() -> None:
    selected = builder.selected_approved_folds()

    assert len(APPROVED_FOLDS) == 4
    assert builder.CANONICAL_FOLD_IDS == (1, 2, 3, 4)
    assert tuple(fold.fold_id for fold in selected) == (1, 2, 3, 4)
    args = builder._argument_parser().parse_args([
        "--feature-profile", "time-aware", "--folds", "1", "2", "3", "4"
    ])
    assert args.folds == [1, 2, 3, 4]


def test_invalid_or_duplicate_fold_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown approved fold IDs"):
        builder.selected_approved_folds((1, 9))
    with pytest.raises(ValueError, match="must be unique"):
        builder.selected_approved_folds((1, 1))


def test_all_store_no_item_cap_configuration_is_locked() -> None:
    config = builder.FoldDatasetBuildConfig(feature_profile="time-aware")

    assert builder.ALL_FAVORITA_STORES == tuple(range(1, 55))
    assert config.output_dir == Path(
        "artifacts/features/favorita_2017_four_fold_time_aware"
    )
    assert config.store_batches == tuple((store,) for store in range(1, 55))
    assert config.max_items_per_store is None


@pytest.mark.parametrize("fold", APPROVED_FOLDS)
def test_training_origins_are_daily_and_end_before_fold_origin(
    fold: TemporalValidationFold,
) -> None:
    source_start = MODELING_TARGET_START - timedelta(days=35)

    origins = builder.derive_training_origins(source_start, fold)

    assert origins[0] == MODELING_TARGET_START - timedelta(days=1)
    assert origins[-1] == fold.forecast_origin - timedelta(days=1)
    assert len(origins) == (fold.forecast_origin - MODELING_TARGET_START).days + 1


def _bounded_fold_fixture(tmp_path: Path) -> tuple[
    builder.FoldDatasetBuildConfig,
    TemporalValidationFold,
    builder.FoldArtifactPaths,
    tuple,
    bytes,
]:
    fixture, origin = _fixture_source_frame()
    canonical_origin = pd.Timestamp(APPROVED_FOLDS[0].forecast_origin)
    early_fixture = fixture.copy()
    early_origin = pd.Timestamp(MODELING_TARGET_START) - pd.Timedelta(days=1)
    early_fixture["date"] = early_fixture["date"] + (early_origin - origin)
    fixture["date"] = fixture["date"] + (canonical_origin - origin)
    fixture = pd.concat((early_fixture, fixture), ignore_index=True)
    origin = canonical_origin
    fixture.loc[fixture["date"] == origin, "unit_sales"] = -2.75
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
        feature_profile="time-aware",
        source_path=source_path,
        output_dir=tmp_path / "folds",
        store_batches=((1,),),
        max_items_per_store=None,
        canonical_contract=False,
    )
    paths = builder.FoldArtifactPaths(
        fold_id=1,
        directory=config.output_dir / "fold_01",
        training=config.output_dir / "fold_01" / "training.parquet",
        validation=config.output_dir / "fold_01" / "validation.parquet",
        manifest=config.output_dir / "fold_01" / "manifest.json",
    )
    training_origins = (
        MODELING_TARGET_START - timedelta(days=1),
        origin.date() - timedelta(days=1),
    )
    return config, fold, paths, training_origins, source_bytes


def test_bounded_fold_build_enforces_temporal_and_artifact_contract(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config, fold, paths, training_origins, source_bytes = _bounded_fold_fixture(
        tmp_path
    )

    manifest = builder.build_one_fold_dataset(
        config,
        fold,
        paths,
        training_origins=training_origins,
        log_progress=True,
    )

    training = pq.read_table(paths.training).to_pandas()
    validation = pq.read_table(paths.validation).to_pandas()
    assert tuple(training.columns) == TRAINING_OUTPUT_COLUMNS
    assert tuple(validation.columns) == TRAINING_OUTPUT_COLUMNS
    assert training["forecast_date"].min().date() == MODELING_TARGET_START
    assert training["forecast_date"].max().date() == fold.forecast_origin
    assert validation["forecast_origin"].dt.date.unique().tolist() == [
        fold.forecast_origin
    ]
    assert validation["forecast_date"].min().date() == fold.validation_start
    assert validation["forecast_date"].max().date() == fold.validation_end
    assert sorted(validation["forecast_horizon"].unique()) == list(FORECAST_HORIZONS)
    assert validation["forecast_date"].max().date() < FINAL_HOLDOUT.holdout_start
    assert (training["unit_sales"] == -2.75).any()
    assert config.source_path.read_bytes() == source_bytes
    assert manifest["source_not_mutated"] is True
    assert manifest["final_holdout_excluded"] is True
    assert manifest["store_count"] == 1
    assert manifest["canonical_fold_id"] == 1
    assert manifest["canonical_fold_count"] == 4
    assert manifest["canonical_contract_enforced"] is False
    assert manifest["experiment_subset"] == [1, 2, 3, 4]
    assert manifest["execution_scope"] == "synthetic_test_fixture"
    assert manifest["canonical_validation_design"] == ("four_fold_expanding_window")
    assert manifest["artifact_root"] == config.output_dir.as_posix()
    assert manifest["modeling_target_start"] == "2017-01-01"
    assert manifest["modeling_target_end"] == "2017-07-30"
    assert manifest["training_target_start"] == "2017-01-01"
    assert manifest["training_target_end"] == "2017-02-28"
    assert manifest["configured_store_count"] == 1
    assert manifest["observed_store_count"] == 1
    assert manifest["processed_stores"] == [1]
    assert manifest["max_items_per_store"] is None
    assert manifest["ordered_schema"] == list(TRAINING_OUTPUT_COLUMNS)
    assert json.loads(paths.manifest.read_text(encoding="utf-8")) == manifest
    assert capsys.readouterr().out.splitlines() == [
        "[Fold 1/4] training origins: 2",
        "[Fold 1/4] building training.parquet...",
        "[Fold 1/4] training store 1/1",
        f"[Fold 1/4] training rows: {manifest['training_row_count']}",
        "[Fold 1/4] building validation.parquet...",
        "[Fold 1/4] validation store 1/1",
        f"[Fold 1/4] validation rows: {manifest['validation_row_count']}",
        "[Fold 1/4] completed",
    ]


def test_build_rejects_item_cap(tmp_path: Path) -> None:
    config, fold, paths, training_origins, _ = _bounded_fold_fixture(tmp_path)
    capped = builder.FoldDatasetBuildConfig(
        feature_profile="time-aware",
        source_path=config.source_path,
        output_dir=config.output_dir,
        store_batches=config.store_batches,
        max_items_per_store=1,
        canonical_contract=False,
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
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_path = tmp_path / "source.parquet"
    source_path.write_bytes(b"fixture")
    config = builder.FoldDatasetBuildConfig(
        feature_profile="time-aware",
        source_path=source_path,
        output_dir=tmp_path / "folds",
    )
    active = 0
    completed: list[int] = []
    expected_fold_ids = list(builder.CANONICAL_FOLD_IDS)

    def fake_build(
        received_config: builder.FoldDatasetBuildConfig,
        fold: TemporalValidationFold,
        paths: builder.FoldArtifactPaths,
        *,
        training_origins: tuple | None = None,
        log_progress: bool = False,
        experiment_subset: tuple[int, ...] = (),
    ) -> dict[str, int]:
        nonlocal active
        assert received_config is config
        assert training_origins
        assert log_progress is True
        assert experiment_subset == builder.CANONICAL_FOLD_IDS
        assert active == 0
        fold_index = expected_fold_ids.index(fold.fold_id)
        assert completed == expected_fold_ids[:fold_index]
        active += 1
        completed.append(paths.fold_id)
        active -= 1
        return {"fold_id": fold.fold_id}

    monkeypatch.setattr(builder, "build_one_fold_dataset", fake_build)
    monkeypatch.setattr(
        builder,
        "_source_date_bounds",
        lambda _path: (
            MODELING_TARGET_START - timedelta(days=35),
            APPROVED_FOLDS[-1].validation_end,
        ),
    )

    manifests = builder.build_approved_fold_datasets(config)

    assert completed == expected_fold_ids
    assert tuple(item["fold_id"] for item in manifests) == tuple(expected_fold_ids)
    output_lines = capsys.readouterr().out.splitlines()
    assert output_lines == [
        *[
            f"[Fold {fold_id}/4] deriving training origins..."
            for fold_id in expected_fold_ids
        ],
        f"Artifact directory: {config.output_dir.as_posix()}",
    ]


def test_complete_fold_is_validated_and_reused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config, fold, paths, training_origins, source_bytes = _bounded_fold_fixture(
        tmp_path
    )
    first_manifest = builder.build_one_fold_dataset(
        config,
        fold,
        paths,
        training_origins=training_origins,
    )
    capsys.readouterr()

    def fail_materialization(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("valid fold must not be rebuilt")

    monkeypatch.setattr(
        builder,
        "materialize_feature_dataset",
        fail_materialization,
    )
    reused_manifest = builder.build_one_fold_dataset(
        config,
        fold,
        paths,
        training_origins=training_origins,
        log_progress=True,
    )

    assert reused_manifest == first_manifest
    assert config.source_path.read_bytes() == source_bytes
    assert capsys.readouterr().out.splitlines() == [
        "[Fold 1/4] training origins: 2",
        "[Fold 1/4] validated existing artifacts — reusing",
    ]


def test_sparse_zero_row_store_is_allowed_without_synthetic_rows(
    tmp_path: Path,
) -> None:
    base_config, fold, paths, training_origins, source_bytes = _bounded_fold_fixture(
        tmp_path
    )
    config = builder.FoldDatasetBuildConfig(
        feature_profile="time-aware",
        source_path=base_config.source_path,
        output_dir=base_config.output_dir,
        store_batches=((1,), (2,)),
        max_items_per_store=None,
        canonical_contract=False,
    )

    manifest = builder.build_one_fold_dataset(
        config,
        fold,
        paths,
        training_origins=training_origins,
    )

    source = pq.read_table(config.source_path).to_pandas()
    observed_targets = {
        (row.date, int(row.store_nbr), int(row.item_nbr))
        for row in source[["date", "store_nbr", "item_nbr"]].itertuples(index=False)
    }
    for artifact_path in (paths.training, paths.validation):
        artifact = pq.read_table(
            artifact_path,
            columns=["forecast_date", "store_nbr", "item_nbr"],
        ).to_pandas()
        artifact_targets = {
            (row.forecast_date, int(row.store_nbr), int(row.item_nbr))
            for row in artifact.itertuples(index=False)
        }
        assert artifact_targets.issubset(observed_targets)
        assert set(artifact["store_nbr"]) == {1}

    assert manifest["configured_store_count"] == 2
    assert manifest["processed_store_count"] == 2
    assert manifest["processed_stores"] == [1, 2]
    assert manifest["observed_store_count"] == 1
    assert manifest["observed_stores"] == [1]
    assert manifest["sparse_observed_rows_only"] is True
    assert config.source_path.read_bytes() == source_bytes


def test_canonical_fold_allows_configured_stores_without_observed_rows(
    tmp_path: Path,
) -> None:
    base_config, fold, paths, _, source_bytes = _bounded_fold_fixture(tmp_path)
    config = builder.FoldDatasetBuildConfig(
        feature_profile="time-aware",
        source_path=base_config.source_path,
        output_dir=base_config.output_dir,
    )

    manifest = builder.build_one_fold_dataset(
        config,
        fold,
        paths,
        training_origins=builder.canonical_training_origins(fold),
    )

    assert manifest["configured_stores"] == list(builder.ALL_FAVORITA_STORES)
    assert manifest["processed_stores"] == list(builder.ALL_FAVORITA_STORES)
    assert manifest["configured_store_count"] == 54
    assert manifest["processed_store_count"] == 54
    assert manifest["observed_stores"] == [1]
    assert manifest["observed_store_count"] == 1
    assert manifest["store_count"] == 1
    assert 52 in manifest["configured_stores"]
    assert 52 in manifest["processed_stores"]
    assert 52 not in manifest["observed_stores"]
    assert config.source_path.read_bytes() == source_bytes


def test_skipped_configured_store_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_config, fold, paths, training_origins, _ = _bounded_fold_fixture(tmp_path)
    config = builder.FoldDatasetBuildConfig(
        feature_profile="time-aware",
        source_path=base_config.source_path,
        output_dir=base_config.output_dir,
        store_batches=((1,), (2,)),
        max_items_per_store=None,
        canonical_contract=False,
    )
    original_materialize = builder.materialize_feature_dataset

    def skip_store(*args: object, **kwargs: object) -> dict[str, object]:
        result = original_materialize(*args, **kwargs)
        result["processed_stores"] = [1]
        return result

    monkeypatch.setattr(builder, "materialize_feature_dataset", skip_store)

    with pytest.raises(
        AssertionError,
        match="materialization skipped configured stores",
    ):
        builder.build_one_fold_dataset(
            config,
            fold,
            paths,
            training_origins=training_origins,
        )

    assert not paths.manifest.exists()


def test_invalid_existing_artifact_requires_overwrite(
    tmp_path: Path,
) -> None:
    config, fold, paths, training_origins, _ = _bounded_fold_fixture(tmp_path)
    paths.validation.parent.mkdir(parents=True)
    paths.validation.write_bytes(b"do-not-overwrite")

    with pytest.raises(ValueError, match="artifacts are incomplete"):
        builder.build_one_fold_dataset(
            config,
            fold,
            paths,
            training_origins=training_origins,
        )

    assert paths.validation.read_bytes() == b"do-not-overwrite"


def test_canonical_build_rejects_incomplete_or_non_daily_origins(
    tmp_path: Path,
) -> None:
    base_config, fold, paths, _, _ = _bounded_fold_fixture(tmp_path)
    config = builder.FoldDatasetBuildConfig(
        feature_profile="time-aware",
        source_path=base_config.source_path,
        output_dir=base_config.output_dir,
    )
    canonical_origins = builder.canonical_training_origins(fold)

    for invalid_origins in (
        canonical_origins[:-1],
        canonical_origins[:10] + canonical_origins[11:],
    ):
        with pytest.raises(ValueError, match="complete daily sequence"):
            builder.build_one_fold_dataset(
                config,
                fold,
                paths,
                training_origins=invalid_origins,
            )

    assert not paths.training.exists()
    assert not paths.validation.exists()
    assert not paths.manifest.exists()


def test_canonical_build_rejects_partial_store_scope(tmp_path: Path) -> None:
    config, fold, paths, _, _ = _bounded_fold_fixture(tmp_path)
    canonical_config = builder.FoldDatasetBuildConfig(
        feature_profile="time-aware",
        source_path=config.source_path,
        output_dir=config.output_dir,
        store_batches=((1,),),
    )

    with pytest.raises(ValueError, match="exactly stores 1 through 54"):
        builder.build_one_fold_dataset(
            canonical_config,
            fold,
            paths,
            training_origins=builder.canonical_training_origins(fold),
        )


@pytest.mark.parametrize("output_dir", builder.INCOMPATIBLE_OUTPUT_DIRS)
def test_incompatible_historical_artifact_roots_are_rejected(
    output_dir: Path,
) -> None:
    with pytest.raises(ValueError, match="incompatible artifact root"):
        builder.validate_canonical_fold_output_dir(output_dir)
    with pytest.raises(ValueError, match="incompatible artifact root"):
        builder.validate_canonical_fold_output_dir(output_dir / "fold_01")


@pytest.mark.parametrize(
    ("mismatch_key", "mismatch_value"),
    (
        ("execution_scope", "mismatched_scope"),
        ("artifact_root", "artifacts/features/favorita_four_fold"),
    ),
)
def test_manifest_mismatch_fails_closed_without_rewriting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mismatch_key: str,
    mismatch_value: str,
) -> None:
    config, fold, paths, training_origins, _ = _bounded_fold_fixture(tmp_path)
    builder.build_one_fold_dataset(
        config,
        fold,
        paths,
        training_origins=training_origins,
    )
    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    manifest[mismatch_key] = mismatch_value
    paths.manifest.write_text(json.dumps(manifest), encoding="utf-8")
    manifest_before = paths.manifest.read_bytes()

    def fail_materialization(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("mismatching artifacts must not be rebuilt")

    monkeypatch.setattr(builder, "materialize_feature_dataset", fail_materialization)

    with pytest.raises(ValueError, match="manifest does not match"):
        builder.build_one_fold_dataset(
            config,
            fold,
            paths,
            training_origins=training_origins,
        )

    assert paths.manifest.read_bytes() == manifest_before


def test_profile_root_contract_rejects_wrong_approved_root() -> None:
    config = builder.FoldDatasetBuildConfig(
        feature_profile="contextual",
        output_dir=builder.TIME_AWARE_OUTPUT_DIR,
    )
    with pytest.raises(ValueError, match="requires canonical artifact root"):
        builder._require_canonical_build_config(config)


def test_bounded_dual_profile_folds_have_identical_row_digests(
    tmp_path: Path,
) -> None:
    time_config, fold, _, training_origins, _ = _bounded_fold_fixture(tmp_path)
    time_config = replace(
        time_config,
        output_dir=tmp_path / "time-aware",
        feature_profile="time-aware",
    )
    contextual_config = replace(
        time_config,
        output_dir=tmp_path / "contextual",
        feature_profile="contextual",
    )
    time_paths = builder.approved_fold_artifact_paths(time_config.output_dir)[0]
    contextual_paths = builder.approved_fold_artifact_paths(
        contextual_config.output_dir
    )[0]
    time_manifest = builder.build_one_fold_dataset(
        time_config,
        fold,
        time_paths,
        training_origins=training_origins,
    )
    contextual_manifest = builder.build_one_fold_dataset(
        contextual_config,
        fold,
        contextual_paths,
        training_origins=training_origins,
    )
    assert time_manifest["feature_profile"] == "time-aware"
    assert contextual_manifest["feature_profile"] == "contextual"
    assert len(time_manifest["ordered_schema"]) == 43
    assert len(contextual_manifest["ordered_schema"]) == 25
    for field in (
        "training_row_count",
        "validation_row_count",
        "training_row_key_target_sha256",
        "validation_row_key_target_sha256",
        "training_store_cardinality",
        "training_item_cardinality",
        "validation_store_cardinality",
        "validation_item_cardinality",
    ):
        assert contextual_manifest[field] == time_manifest[field]
    assert contextual_manifest["historical_feature_groups_enabled"] is False
    assert time_manifest["historical_feature_groups_enabled"] is True
