from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from pipelines.evaluation import run_favorita_lightgbm_evaluation as runner
from pipelines.evaluation.favorita_metrics import (
    ForecastMetricResults,
    evaluate_favorita_forecasts,
)
from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FORECAST_HORIZONS,
)
from pipelines.features.favorita_model_ready import (
    MODEL_FEATURE_COLUMNS,
    _fixture_source_frame,
    build_feature_rows_for_origin,
    to_arrow_table,
)


def _config(tmp_path: Path) -> runner.FavoritaEvaluationRunConfig:
    source_path = tmp_path / "source.parquet"
    source_path.write_bytes(b"unchanged-source")
    return runner.FavoritaEvaluationRunConfig(
        source_path=source_path,
        output_dir=tmp_path / "evaluation",
        fold_output_dir=tmp_path / "folds",
    )


@pytest.mark.parametrize(
    "fold_output_dir",
    (
        Path("artifacts/features/favorita_folds"),
        Path("artifacts/features/favorita_four_fold"),
        runner.EXPERIMENTAL_FEASIBILITY_FOLD_OUTPUT_DIR,
    ),
)
def test_incompatible_fold_artifact_roots_are_rejected(
    tmp_path: Path,
    fold_output_dir: Path,
) -> None:
    config = _config(tmp_path)
    incompatible_config = runner.FavoritaEvaluationRunConfig(
        source_path=config.source_path,
        output_dir=config.output_dir,
        fold_output_dir=fold_output_dir,
    )

    with pytest.raises(ValueError, match="artifact root|feasibility artifact root"):
        runner.validate_evaluation_config(incompatible_config)


def test_historical_result_root_is_rejected(tmp_path: Path) -> None:
    config = _config(tmp_path)
    historical_config = runner.FavoritaEvaluationRunConfig(
        source_path=config.source_path,
        output_dir=runner.HISTORICAL_EVALUATION_OUTPUT_DIR,
        fold_output_dir=config.fold_output_dir,
    )

    with pytest.raises(ValueError, match="historical result root"):
        runner.validate_evaluation_config(historical_config)


def test_full_evaluator_rejects_accumulated_single_fold_results(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    config.output_dir.mkdir(parents=True)
    accumulated = config.output_dir / runner.ACCUMULATED_RESULTS_FILENAME
    accumulated.write_text("{}\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refuses to retrain folds"):
        runner.validate_evaluation_config(config)


def test_default_namespaces_belong_to_the_2017_redesign() -> None:
    assert runner.DEFAULT_FOLD_OUTPUT_DIR == Path(
        "artifacts/features/favorita_2017_four_fold_time_aware"
    )
    assert runner.CONTEXTUAL_OUTPUT_DIR == Path(
        "artifacts/evaluation/favorita_2017_four_fold_lightgbm_contextual"
    )
    assert runner.DEFAULT_OUTPUT_DIR == runner.TIME_AWARE_OUTPUT_DIR == Path(
        "artifacts/evaluation/favorita_2017_four_fold_lightgbm_time_aware"
    )


def _metrics() -> ForecastMetricResults:
    return ForecastMetricResults(
        mae=1.0,
        rmse=2.0,
        wape=0.25,
        bias=-0.5,
        rmsle=0.3,
        nwrmsle=0.4,
    )


def _streaming_summary() -> runner.StreamingEvaluationSummary:
    fold_metrics = tuple(
        runner.StreamingFoldMetricRecord(
            fold_id=fold.fold_id,
            forecast_origin=fold.forecast_origin,
            validation_start=fold.validation_start,
            validation_end=fold.validation_end,
            metrics=_metrics(),
            row_count=16,
            model_evidence={
                "feature_contract": "time-aware",
                "candidate_feature_columns": list(
                    runner.resolve_feature_contract("time-aware")
                ),
                "fitted_feature_columns": list(
                    runner.resolve_feature_contract("time-aware")
                ),
                "excluded_all_null_features": [],
                "categorical_feature_columns": [],
                "model_parameters": dict(runner.LIGHTGBM_PARAMETERS),
                "num_boost_round": runner.NUM_BOOST_ROUND,
                "training_artifact": {"path": "training.parquet"},
                "validation_artifact": {"path": "validation.parquet"},
            },
        )
        for fold in APPROVED_FOLDS
    )
    horizon_metrics = tuple(
        runner.StreamingHorizonMetricRecord(
            forecast_horizon=horizon,
            metrics=_metrics(),
            row_count=len(APPROVED_FOLDS),
        )
        for horizon in FORECAST_HORIZONS
    )
    return runner.StreamingEvaluationSummary(
        overall_metrics=_metrics(),
        fold_metrics=fold_metrics,
        horizon_metrics=horizon_metrics,
        prediction_row_count=len(APPROVED_FOLDS) * len(FORECAST_HORIZONS),
    )


def test_feature_frame_bridge_preserves_rows_target_and_model_schema() -> None:
    source, origin = _fixture_source_frame()
    frame = build_feature_rows_for_origin(
        source,
        forecast_origin=origin,
        allow_assumed_future_promotion=True,
        allow_assumed_future_holidays=True,
    ).iloc[:2]

    examples = runner.feature_frame_to_backtest_examples(frame)

    assert len(examples) == len(frame) == 2
    assert tuple(examples[0].features) == tuple(
        column
        for column in MODEL_FEATURE_COLUMNS
        if column not in {"store_nbr", "item_nbr"}
    )
    assert "unit_sales" not in examples[0].features
    assert examples[0].unit_sales == float(frame.iloc[0]["unit_sales"])
    assert examples[0].perishable == int(frame.iloc[0]["perishable"])


def test_feature_frame_bridge_rejects_noncanonical_schema() -> None:
    source, origin = _fixture_source_frame()
    frame = build_feature_rows_for_origin(source, forecast_origin=origin).drop(
        columns="sales_lag_1"
    )

    with pytest.raises(ValueError, match="ordered training schema"):
        runner.feature_frame_to_backtest_examples(frame)


def test_load_backtest_examples_combines_parquet_batches(tmp_path: Path) -> None:
    source, origin = _fixture_source_frame()
    frame = build_feature_rows_for_origin(
        source,
        forecast_origin=origin,
        allow_assumed_future_promotion=True,
        allow_assumed_future_holidays=True,
    ).iloc[:2]
    feature_path = tmp_path / "features.parquet"
    frame.to_parquet(feature_path, index=False, row_group_size=1)

    examples = runner.load_backtest_examples(feature_path)

    assert isinstance(examples, tuple)
    assert len(examples) == 2
    assert tuple(example.validation_key for example in examples) == tuple(
        (
            pd.Timestamp(row.forecast_origin).date(),
            pd.Timestamp(row.forecast_date).date(),
            int(row.store_nbr),
            int(row.item_nbr),
        )
        for row in frame.itertuples(index=False)
    )


def test_validation_batches_preserve_rows_across_batch_boundaries(
    tmp_path: Path,
) -> None:
    source, origin = _fixture_source_frame()
    frame = build_feature_rows_for_origin(
        source,
        forecast_origin=origin,
        allow_assumed_future_promotion=True,
        allow_assumed_future_holidays=True,
    )
    feature_path = tmp_path / "validation.parquet"
    pq.write_table(to_arrow_table(frame), feature_path, row_group_size=5)

    small_batches = list(
        runner.iter_model_ready_validation_batches(feature_path, batch_size=3)
    )
    large_batches = list(
        runner.iter_model_ready_validation_batches(feature_path, batch_size=100)
    )

    parquet_file = pq.ParquetFile(feature_path)
    try:
        assert parquet_file.metadata.num_row_groups > 1
    finally:
        parquet_file.close()
    assert len(small_batches) > len(large_batches) >= 1
    pd.testing.assert_frame_equal(
        pd.concat(small_batches, ignore_index=True),
        pd.concat(large_batches, ignore_index=True),
    )
    small_metrics = runner.FavoritaMetricAccumulator()
    large_metrics = runner.FavoritaMetricAccumulator()
    for batch in small_batches:
        small_metrics.update(
            batch["unit_sales"],
            np.full(len(batch), 9.5),
            batch["perishable"],
        )
    for batch in large_batches:
        large_metrics.update(
            batch["unit_sales"],
            np.full(len(batch), 9.5),
            batch["perishable"],
        )
    for metric_name in runner._METRIC_NAMES:
        assert getattr(small_metrics.finalize(), metric_name) == pytest.approx(
            getattr(large_metrics.finalize(), metric_name),
            rel=1e-14,
            abs=1e-14,
        )


def test_validation_batch_reader_rejects_empty_or_reordered_artifacts(
    tmp_path: Path,
) -> None:
    source, origin = _fixture_source_frame()
    frame = build_feature_rows_for_origin(source, forecast_origin=origin)
    empty_path = tmp_path / "empty.parquet"
    reordered_path = tmp_path / "reordered.parquet"
    pq.write_table(to_arrow_table(frame.iloc[:0]), empty_path)
    frame.loc[:, list(reversed(frame.columns))].to_parquet(
        reordered_path,
        index=False,
    )

    with pytest.raises(ValueError, match="contains no rows"):
        list(runner.iter_model_ready_validation_batches(empty_path))
    with pytest.raises(ValueError, match="ordered training schema"):
        list(runner.iter_model_ready_validation_batches(reordered_path))


def test_cross_batch_duplicate_validation_key_is_rejected() -> None:
    tracker = runner._ValidationKeyTracker()
    first = pd.DataFrame(
        {
            "forecast_date": pd.to_datetime(["2015-09-01", "2015-09-02"]),
            "store_nbr": [1, 1],
            "item_nbr": [100, 100],
        }
    )
    second = pd.DataFrame(
        {
            "forecast_date": pd.to_datetime(["2015-09-02", "2015-09-03"]),
            "store_nbr": [1, 1],
            "item_nbr": [100, 100],
        }
    )

    tracker.update(first, fold_id=1)
    with pytest.raises(ValueError, match="unique and ordered"):
        tracker.update(second, fold_id=1)


def test_multi_fold_runner_has_no_fold_builder_runtime_dependency() -> None:
    assert not hasattr(runner, "FoldDatasetBuildConfig")
    assert not hasattr(runner, "build_approved_fold_datasets")
    assert not hasattr(runner, "ALL_STORE_BATCHES")


def _install_serial_fakes(
    monkeypatch: pytest.MonkeyPatch,
    config: runner.FavoritaEvaluationRunConfig,
    *,
    fail_fold: int | None = None,
    fail_batch: tuple[int, int] | None = None,
) -> tuple[list[tuple[str, int]], list[object]]:
    events: list[tuple[str, int]] = []
    models: list[object] = []
    evaluation_paths = runner._artifact_paths(config.output_dir)
    source, fixture_origin = _fixture_source_frame()
    base_frame = build_feature_rows_for_origin(
        source,
        forecast_origin=fixture_origin,
        allow_assumed_future_promotion=True,
        allow_assumed_future_holidays=True,
    )
    base_frame = base_frame.loc[base_frame["item_nbr"] == 100].reset_index(
        drop=True
    )
    for fold, paths in zip(
        APPROVED_FOLDS,
        runner.approved_fold_artifact_paths(config.fold_output_dir),
        strict=True,
    ):
        paths.directory.mkdir(parents=True, exist_ok=True)
        training = base_frame.copy()
        training["forecast_origin"] = pd.Timestamp(
            runner.MODELING_TARGET_START
        ) - pd.Timedelta(days=1)
        training["forecast_date"] = training["forecast_origin"] + pd.to_timedelta(
            training["forecast_horizon"], unit="D"
        )
        late = base_frame.loc[base_frame["forecast_horizon"] == 1].copy()
        late["forecast_origin"] = pd.Timestamp(fold.forecast_origin) - pd.Timedelta(
            days=1
        )
        late["forecast_date"] = pd.Timestamp(fold.forecast_origin)
        training = pd.concat((training, late), ignore_index=True)
        validation = base_frame.copy()
        validation["forecast_origin"] = pd.Timestamp(fold.forecast_origin)
        validation["forecast_date"] = validation["forecast_origin"] + pd.to_timedelta(
            validation["forecast_horizon"], unit="D"
        )
        pq.write_table(to_arrow_table(training), paths.training, row_group_size=5)
        pq.write_table(to_arrow_table(validation), paths.validation, row_group_size=5)
        manifest = {
            "fold_id": fold.fold_id,
            "canonical_fold_id": fold.fold_id,
            "canonical_fold_count": len(APPROVED_FOLDS),
            "canonical_validation_design": runner.CANONICAL_VALIDATION_DESIGN,
            "execution_scope": runner.EXECUTION_SCOPE,
            "experiment_subset": list(runner.CANONICAL_FOLD_IDS),
            "canonical_contract_enforced": True,
            "forecast_origin": fold.forecast_origin.isoformat(),
            "validation_start": fold.validation_start.isoformat(),
            "validation_end": fold.validation_end.isoformat(),
            "artifact_root": config.fold_output_dir.as_posix(),
            "modeling_target_start": runner.MODELING_TARGET_START.isoformat(),
            "modeling_target_end": runner.MODELING_TARGET_END.isoformat(),
            "training_target_start": runner.MODELING_TARGET_START.isoformat(),
            "training_target_end": fold.forecast_origin.isoformat(),
            "max_items_per_store": None,
            "feature_profile": config.feature_contract,
            "feature_profile_version": runner.resolve_feature_profile(
                config.feature_contract
            ).version,
            "model_feature_columns": list(
                runner.resolve_feature_profile(
                    config.feature_contract
                ).model_feature_columns
            ),
            "ordered_schema": list(
                runner.resolve_feature_profile(
                    config.feature_contract
                ).output_columns
            ),
            "final_holdout_excluded": True,
            "future_actual_leakage": False,
            "training_row_count": len(training),
            "validation_row_count": len(validation),
            "training_row_key_target_digest_version": (
                runner.ROW_KEY_TARGET_DIGEST_VERSION
            ),
            "training_row_key_target_sha256": "a" * 64,
            "validation_row_key_target_digest_version": (
                runner.ROW_KEY_TARGET_DIGEST_VERSION
            ),
            "validation_row_key_target_sha256": "b" * 64,
            "cross_arm_row_equivalence": {
                "status": "verified",
                "counterpart_feature_profile": "contextual",
            },
        }
        paths.manifest.write_text(json.dumps(manifest), encoding="utf-8")

    original_batch_reader = runner.iter_model_ready_validation_batches

    def tracked_validation_batches(
        path: Path,
        *,
        feature_profile: str = "time-aware",
        batch_size: int = runner.PARQUET_ROW_GROUP_SIZE,
    ):
        fold_id = int(path.parent.name[-2:])
        for frame in original_batch_reader(
            path, feature_profile=feature_profile, batch_size=7
        ):
            events.append(("validation_batch", fold_id))
            yield frame

    class FakeAdapter:
        def __init__(self, *, feature_columns) -> None:
            self.candidate_feature_columns = tuple(feature_columns)
            self.feature_contract_name = config.feature_contract
            self.fitted_feature_columns = tuple(feature_columns)
            self.excluded_all_null_features = ()
            self.categorical_feature_columns = ()
            self.model_parameters = runner.LIGHTGBM_PARAMETERS
            self.num_boost_round = runner.NUM_BOOST_ROUND
            self.fold_id = len(models) + 1
            self.predict_calls = 0
            models.append(self)
            events.append(("model", self.fold_id))

        def fit_parquet(self, path: Path) -> None:
            assert path.parent.name == f"fold_{self.fold_id:02d}"
            assert path.name == "training.parquet"
            events.append(("fit_parquet", self.fold_id))
            if fail_fold == self.fold_id:
                raise RuntimeError(f"fold {self.fold_id} failed")

        def predict_frame(
            self,
            frame: pd.DataFrame,
        ) -> np.ndarray:
            self.predict_calls += 1
            assert not any(
                path.exists() for path in runner._path_values(evaluation_paths)
            )
            events.append(("predict_frame", self.fold_id))
            if fail_batch == (self.fold_id, self.predict_calls):
                raise RuntimeError(
                    f"fold {self.fold_id} batch {self.predict_calls} failed"
                )
            return np.full(len(frame), 9.5, dtype="float64")

    def reject_row_loader(path: Path) -> tuple[runner.BacktestExample, ...]:
        raise AssertionError(f"row-object loader must not be used: {path}")

    monkeypatch.setattr(
        runner,
        "iter_model_ready_validation_batches",
        tracked_validation_batches,
    )
    monkeypatch.setattr(
        runner,
        "load_model_ready_frame",
        lambda path: (_ for _ in ()).throw(
            AssertionError(f"full-frame loader must not be used: {path}")
        ),
    )
    monkeypatch.setattr(runner, "load_backtest_examples", reject_row_loader)
    monkeypatch.setattr(
        runner,
        "_fold_result_from_frame",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("row-level EvaluationEvidence tuple must not be created")
        ),
    )
    monkeypatch.setattr(
        runner,
        "aggregate_fold_backtest_results",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("row-oriented aggregation must not be used")
        ),
    )
    monkeypatch.setattr(runner, "FavoritaLightGBMAdapter", FakeAdapter)
    return events, models


def test_runner_processes_four_fold_artifacts_serially(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    source_before = config.source_path.read_bytes()
    events, models = _install_serial_fakes(monkeypatch, config)
    fold_files = tuple(
        path
        for artifact in runner.approved_fold_artifact_paths(config.fold_output_dir)
        for path in (artifact.training, artifact.validation, artifact.manifest)
    )
    fold_state_before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in fold_files}

    paths = runner.run_evaluation(config)

    assert len(models) == 4
    assert len({id(model) for model in models}) == 4
    cursor = 0
    for fold_id, model in enumerate(models, start=1):
        assert events[cursor : cursor + 2] == [
            ("model", fold_id),
            ("fit_parquet", fold_id),
        ]
        cursor += 2
        assert model.predict_calls > 1
        for _ in range(model.predict_calls):
            assert events[cursor : cursor + 2] == [
                ("validation_batch", fold_id),
                ("predict_frame", fold_id),
            ]
            cursor += 2
    assert cursor == len(events)
    assert all(path.exists() for path in runner._path_values(paths))
    assert not hasattr(paths, "feature_examples")
    assert config.source_path.read_bytes() == source_before
    assert {
        path: (path.read_bytes(), path.stat().st_mtime_ns) for path in fold_files
    } == fold_state_before
    manifest = json.loads(paths.run_manifest.read_text(encoding="utf-8"))
    assert manifest["evaluation"]["fold_count"] == 4
    assert manifest["evaluation"]["horizon_count"] == 16
    assert manifest["fold_artifact_consumption"]["mode"] == "consumption-only"
    assert manifest["fold_artifact_consumption"]["fold_artifacts_mutated"] is False
    for record, artifact in zip(
        manifest["folds"],
        runner.approved_fold_artifact_paths(config.fold_output_dir),
        strict=True,
    ):
        source_manifest = json.loads(artifact.manifest.read_text(encoding="utf-8"))
        assert record["training_rows"] == source_manifest["training_row_count"]
        assert record["validation_rows"] == source_manifest["validation_row_count"]
        assert record["training_artifact"]["path"] == artifact.training.as_posix()
        assert record["validation_artifact"]["path"] == artifact.validation.as_posix()
    assert manifest["final_holdout"]["scored"] is False
    assert manifest["final_holdout"]["materialized"] is False
    assert manifest["run"]["status"] == "completed"
    assert manifest["training_memory"] == {
        "training_input": "Parquet row-group LightGBM Sequence",
        "python_backtest_examples_materialized": False,
        "full_fold_pandas_frame_materialized": False,
        "target_storage": "temporary float64 disk memmap",
        "lightgbm_native_dataset_in_memory": True,
        "true_external_memory_training": False,
    }
    assert manifest["validation_memory"] == {
        "validation_input": "Parquet batches",
        "full_fold_validation_frame_materialized": False,
        "evaluation_evidence_python_objects_materialized": False,
        "predictions_written_incrementally": True,
        "metrics_computed_incrementally": True,
    }
    predictions = pd.read_parquet(paths.predictions)
    prediction_file = pq.ParquetFile(paths.predictions)
    try:
        assert prediction_file.metadata.num_row_groups == sum(
            model.predict_calls for model in models
        )
    finally:
        prediction_file.close()
    assert tuple(predictions.columns) == runner.PREDICTION_COLUMNS
    assert len(predictions) == 4 * len(FORECAST_HORIZONS)
    assert manifest["evaluation"]["prediction_rows"] == len(predictions)
    assert tuple(sorted(predictions["fold_id"].unique())) == tuple(range(1, 5))
    assert tuple(sorted(predictions["forecast_horizon"].unique())) == (
        FORECAST_HORIZONS
    )
    for row in predictions.itertuples(index=False):
        fold = APPROVED_FOLDS[row.fold_id - 1]
        assert pd.Timestamp(row.forecast_origin).date() == fold.forecast_origin
        assert pd.Timestamp(row.forecast_date).date() == (
            fold.forecast_origin + timedelta(days=row.forecast_horizon)
        )
        assert pd.Timestamp(row.forecast_date).date() < (
            runner.FINAL_HOLDOUT.holdout_start
        )
    expected = evaluate_favorita_forecasts(
        predictions["actual_unit_sales"],
        predictions["prediction"],
        predictions["perishable"],
    )
    overall = json.loads(paths.overall_metrics.read_text(encoding="utf-8"))
    for metric_name in runner._METRIC_NAMES:
        assert overall[metric_name] == pytest.approx(
            getattr(expected, metric_name),
            rel=1e-14,
            abs=1e-14,
        )
    fold_metrics = json.loads(paths.fold_metrics.read_text(encoding="utf-8"))
    horizon_metrics = json.loads(paths.horizon_metrics.read_text(encoding="utf-8"))
    assert [record["fold_id"] for record in fold_metrics] == [1, 2, 3, 4]
    assert [record["validation_rows"] for record in fold_metrics] == [16] * 4
    assert [record["forecast_horizon"] for record in horizon_metrics] == list(
        FORECAST_HORIZONS
    )
    assert [record["row_count"] for record in horizon_metrics] == [4] * 16
    assert set(fold_metrics[0]) == {
        "fold_id", "forecast_origin", "validation_start", "validation_end",
        "validation_rows", *runner._METRIC_NAMES,
    }
    assert set(horizon_metrics[0]) == {
        "forecast_horizon", "row_count", *runner._METRIC_NAMES,
    }
    assert not (config.output_dir / "fold_metrics.csv").exists()
    assert not (config.output_dir / "horizon_metrics.csv").exists()
    summary = paths.evaluation_summary.read_text(encoding="utf-8")
    assert "# Favorita LightGBM Evaluation Summary" in summary
    assert "four-fold expanding-window evaluation" in summary
    assert "protected final holdout was not materialized or scored" in summary
    for fold_id, group in predictions.groupby("fold_id", sort=True):
        expected_fold = evaluate_favorita_forecasts(
            group["actual_unit_sales"],
            group["prediction"],
            group["perishable"],
        )
        record = next(item for item in fold_metrics if item["fold_id"] == fold_id)
        for metric_name in runner._METRIC_NAMES:
            assert record[metric_name] == pytest.approx(
                getattr(expected_fold, metric_name),
                rel=1e-14,
                abs=1e-14,
            )
    for horizon, group in predictions.groupby("forecast_horizon", sort=True):
        expected_horizon = evaluate_favorita_forecasts(
            group["actual_unit_sales"],
            group["prediction"],
            group["perishable"],
        )
        record = next(
            item for item in horizon_metrics
            if item["forecast_horizon"] == horizon
        )
        for metric_name in runner._METRIC_NAMES:
            assert record[metric_name] == pytest.approx(
                getattr(expected_horizon, metric_name),
                rel=1e-14,
                abs=1e-14,
            )


def test_progress_messages_are_concise(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = _config(tmp_path)
    _install_serial_fakes(monkeypatch, config)

    runner.run_evaluation(config)

    output = capsys.readouterr().out
    for fold_id in range(1, 5):
        prefix = f"[Fold {fold_id}/4]"
        assert f"{prefix} validating artifacts..." in output
        assert f"{prefix} training LightGBM..." in output
        assert f"{prefix} training completed in " in output
        assert f"{prefix} evaluating validation rows..." in output
        assert f"{prefix} evaluation completed in " in output
        assert f"{prefix} completed" in output
    assert f"Evaluation completed: {config.output_dir.as_posix()}" in output


@pytest.mark.parametrize("status", ("pending-counterpart", "mismatch"))
def test_unverified_cross_arm_evidence_fails_before_model_construction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
) -> None:
    config = _config(tmp_path)
    _, models = _install_serial_fakes(monkeypatch, config)
    first_manifest = runner.approved_fold_artifact_paths(
        config.fold_output_dir
    )[0].manifest
    payload = json.loads(first_manifest.read_text(encoding="utf-8"))
    payload["cross_arm_row_equivalence"]["status"] = status
    first_manifest.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="cross-arm row equivalence must be verified"):
        runner.run_evaluation(config)

    assert models == []
    assert not any(
        path.exists()
        for path in runner._path_values(runner._artifact_paths(config.output_dir))
    )


def test_output_preflight_runs_before_fold_artifact_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    paths = runner._artifact_paths(config.output_dir)
    paths.overall_metrics.parent.mkdir(parents=True)
    paths.overall_metrics.write_text("existing", encoding="utf-8")
    called = False

    def reject_fold_read(output_dir: Path) -> tuple[()]:
        nonlocal called
        called = True
        return ()

    monkeypatch.setattr(runner, "_read_existing_fold_evidence", reject_fold_read)

    with pytest.raises(FileExistsError, match="overall_metrics.json"):
        runner.run_evaluation(config)

    assert called is False
    assert paths.overall_metrics.read_text(encoding="utf-8") == "existing"


def test_fold_failure_writes_no_completed_evaluation_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    source_before = config.source_path.read_bytes()
    events, _ = _install_serial_fakes(monkeypatch, config, fail_fold=4)

    with pytest.raises(RuntimeError, match="fold 4 failed"):
        runner.run_evaluation(config)

    assert events[-1] == ("fit_parquet", 4)
    assert not any(
        path.exists()
        for path in runner._path_values(runner._artifact_paths(config.output_dir))
    )
    assert config.source_path.read_bytes() == source_before


def test_validation_batch_failure_writes_no_completed_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    source_before = config.source_path.read_bytes()
    events, _ = _install_serial_fakes(
        monkeypatch,
        config,
        fail_batch=(3, 2),
    )

    with pytest.raises(RuntimeError, match="fold 3 batch 2 failed"):
        runner.run_evaluation(config)

    assert events[-1] == ("predict_frame", 3)
    assert not any(
        path.exists()
        for path in runner._path_values(runner._artifact_paths(config.output_dir))
    )
    assert config.source_path.read_bytes() == source_before


def test_artifact_staging_failure_publishes_no_completed_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)
    _install_serial_fakes(monkeypatch, config)
    write_json_list_atomic = runner._write_json_list_atomic

    def fail_horizon_write(
        payload: list[dict[str, object]],
        path: Path,
    ) -> None:
        if path.name == "horizon_metrics.json":
            raise RuntimeError("staging failed")
        write_json_list_atomic(payload, path)

    monkeypatch.setattr(runner, "_write_json_list_atomic", fail_horizon_write)

    with pytest.raises(RuntimeError, match="staging failed"):
        runner.run_evaluation(config)

    assert not any(
        path.exists()
        for path in runner._path_values(runner._artifact_paths(config.output_dir))
    )


def test_manifest_configuration_matches_unsampled_contract(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    paths = runner._artifact_paths(config.output_dir)
    timestamp = datetime(2026, 8, 27, tzinfo=timezone.utc)

    manifest = runner._manifest(
        config=config,
        paths=paths,
        fold_artifact_evidence={
            "creation_status": "not_run",
            "folds": [
                {"training_row_count": 32} for _ in APPROVED_FOLDS
            ],
        },
        result=_streaming_summary(),
        started_at=timestamp,
        completed_at=timestamp,
        source_state={"size_bytes": 16, "mtime_ns": 1},
    )

    assert manifest["namespace"] == {
        "execution_scope": runner.EXECUTION_SCOPE,
        "fold_artifact_root": config.fold_output_dir.as_posix(),
        "result_root": config.output_dir.as_posix(),
    }
    assert set(manifest["configuration"]) == {
        "stores",
        "store_count",
        "max_items_per_store",
        "forecast_horizons",
        "direct_horizon_aware",
        "recursive_feedback",
        "future_promotion_assumption",
        "future_holiday_assumption",
        "feature_contract",
        "candidate_feature_columns",
        "model_parameters",
        "num_boost_round",
        "hyperparameter_tuning",
        "early_stopping",
    }
    assert manifest["configuration"]["store_count"] == 54
    assert manifest["configuration"]["max_items_per_store"] is None
    assert manifest["final_holdout"]["scored"] is False
    assert manifest["final_holdout"]["materialized"] is False
    assert manifest["evaluation"]["prediction_rows"] == 64
    assert manifest["validation_memory"]["validation_input"] == "Parquet batches"


def test_cli_exposes_only_execution_options(tmp_path: Path) -> None:
    parser = runner._argument_parser()
    option_strings = {
        option for action in parser._actions for option in action.option_strings
    }

    assert option_strings == {
        "-h",
        "--help",
        "--source-path",
        "--feature-contract",
        "--overwrite",
    }


def test_multi_fold_runner_fails_before_model_when_fold_artifact_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(tmp_path)
    constructed = False

    class RejectAdapter:
        def __init__(self, **kwargs: object) -> None:
            nonlocal constructed
            constructed = True

    monkeypatch.setattr(runner, "FavoritaLightGBMAdapter", RejectAdapter)
    with pytest.raises(FileNotFoundError, match="never builds folds"):
        runner.run_evaluation(config)
    assert constructed is False


def test_profile_roots_are_separate_and_old_shared_root_is_not_used() -> None:
    contextual = runner.resolve_feature_profile("contextual")
    time_aware = runner.resolve_feature_profile("time-aware")
    assert contextual.canonical_artifact_root == Path(
        "artifacts/features/favorita_2017_four_fold_contextual"
    )
    assert time_aware.canonical_artifact_root == Path(
        "artifacts/features/favorita_2017_four_fold_time_aware"
    )
    assert contextual.canonical_artifact_root != time_aware.canonical_artifact_root
    assert Path("artifacts/features/favorita_2017_four_fold") not in (
        contextual.canonical_artifact_root,
        time_aware.canonical_artifact_root,
    )



def test_multi_cli_selects_matching_profile_specific_fold_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[runner.FavoritaEvaluationRunConfig] = []

    def fake_run(config: runner.FavoritaEvaluationRunConfig):
        captured.append(config)
        return runner._artifact_paths(config.output_dir)

    monkeypatch.setattr(runner, "run_evaluation", fake_run)
    assert runner.main(["--feature-contract", "contextual"]) == 0
    assert captured[0].fold_output_dir == Path(
        "artifacts/features/favorita_2017_four_fold_contextual"
    )
    assert captured[0].output_dir == runner.CONTEXTUAL_OUTPUT_DIR
