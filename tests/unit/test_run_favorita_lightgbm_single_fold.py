from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from pipelines.evaluation import run_favorita_lightgbm_single_fold as runner
from pipelines.evaluation.favorita_metrics import FavoritaMetricAccumulator
from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FINAL_HOLDOUT,
)
from pipelines.features.favorita_model_ready import (
    TRAINING_OUTPUT_COLUMNS,
    _fixture_source_frame,
    build_feature_rows_for_origin,
    to_arrow_table,
)


def _fold(fold_id: int):
    return next(fold for fold in APPROVED_FOLDS if fold.fold_id == fold_id)


def _model_ready_frame(fold_id: int, *, validation: bool) -> pd.DataFrame:
    source, fixture_origin = _fixture_source_frame()
    frame = build_feature_rows_for_origin(
        source,
        forecast_origin=fixture_origin,
        allow_assumed_future_promotion=True,
        allow_assumed_future_holidays=True,
    )
    fold = _fold(fold_id)
    origin = (
        fold.forecast_origin
        if validation
        else fold.forecast_origin - timedelta(days=32)
    )
    frame["forecast_origin"] = pd.Timestamp(origin)
    frame["forecast_date"] = frame["forecast_origin"] + pd.to_timedelta(
        frame["forecast_horizon"],
        unit="D",
    )
    return frame.loc[:, TRAINING_OUTPUT_COLUMNS]


def _write_existing_fold(root: Path, fold_id: int) -> runner.FoldArtifactPaths:
    fold = _fold(fold_id)
    paths = runner._fold_artifact_paths(fold_id, root)
    paths.directory.mkdir(parents=True, exist_ok=True)
    training = _model_ready_frame(fold_id, validation=False)
    validation = _model_ready_frame(fold_id, validation=True)
    pq.write_table(to_arrow_table(training), paths.training, row_group_size=5)
    pq.write_table(to_arrow_table(validation), paths.validation, row_group_size=5)
    manifest = {
        "fold_id": fold_id,
        "canonical_fold_id": fold_id,
        "canonical_validation_design": runner.CANONICAL_VALIDATION_DESIGN,
        "execution_scope": runner.EXECUTION_SCOPE,
        "experiment_subset": list(runner.SUPPORTED_FOLD_IDS),
        "forecast_origin": fold.forecast_origin.isoformat(),
        "validation_start": fold.validation_start.isoformat(),
        "validation_end": fold.validation_end.isoformat(),
        "final_holdout_excluded": True,
        "future_actual_leakage": False,
        "max_items_per_store": None,
        "ordered_schema": list(TRAINING_OUTPUT_COLUMNS),
        "training_row_count": len(training),
        "validation_row_count": len(validation),
    }
    paths.manifest.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    return paths


def _config(tmp_path: Path, fold_id: int = 1) -> runner.SingleFoldEvaluationConfig:
    return runner.SingleFoldEvaluationConfig(
        fold_id=fold_id,
        fold_output_dir=tmp_path / "folds",
        output_dir=tmp_path / "evaluation",
        validation_batch_size=5,
    )


class _FakeAdapter:
    prediction_value = 2.0
    fitted_paths: list[Path] = []
    prediction_batch_sizes: list[int] = []

    def fit_parquet(self, path: Path) -> None:
        self.fitted_paths.append(path)

    def predict_frame(self, frame: pd.DataFrame) -> np.ndarray:
        self.prediction_batch_sizes.append(len(frame))
        return np.full(len(frame), self.prediction_value, dtype="float64")


def _install_fake_adapter(monkeypatch: pytest.MonkeyPatch, value: float = 2.0) -> None:
    class FakeAdapter(_FakeAdapter):
        prediction_value = value
        fitted_paths: list[Path] = []
        prediction_batch_sizes: list[int] = []

    monkeypatch.setattr(runner, "FavoritaLightGBMAdapter", FakeAdapter)


@pytest.mark.parametrize("fold_id", runner.SUPPORTED_FOLD_IDS)
def test_supported_fold_selection_uses_canonical_definition(fold_id: int) -> None:
    assert runner._resolve_fold(fold_id) == _fold(fold_id)


@pytest.mark.parametrize("fold_id", (0, 2, 4, 5, 7, 9, True))
def test_unsupported_fold_selection_is_rejected(fold_id: int) -> None:
    with pytest.raises(ValueError, match="supported folds are 1, 3, 6, 8"):
        runner._resolve_fold(fold_id)


def test_cli_has_only_required_single_fold_selection() -> None:
    parser = runner._argument_parser()
    option_strings = {
        option for action in parser._actions for option in action.option_strings
    }
    fold_action = next(action for action in parser._actions if action.dest == "fold")

    assert option_strings == {"-h", "--help", "--fold"}
    assert fold_action.required is True
    assert tuple(fold_action.choices) == runner.SUPPORTED_FOLD_IDS


def test_missing_artifact_fails_without_any_builder_or_model_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    constructed = False

    class RejectAdapter:
        def __init__(self) -> None:
            nonlocal constructed
            constructed = True

    monkeypatch.setattr(runner, "FavoritaLightGBMAdapter", RejectAdapter)

    with pytest.raises(FileNotFoundError, match="never builds fold artifacts"):
        runner.run_single_fold(_config(tmp_path))

    assert constructed is False
    assert not hasattr(runner, "build_approved_fold_datasets")
    assert not hasattr(runner, "build_one_fold_dataset")


@pytest.mark.parametrize(
    ("key", "value", "message"),
    (
        ("canonical_fold_id", 3, "canonical_fold_id"),
        ("canonical_validation_design", "other", "canonical_validation_design"),
        ("execution_scope", "other", "execution_scope"),
        ("experiment_subset", [1], "experiment_subset"),
        ("forecast_origin", "2017-07-30", "forecast_origin"),
        ("final_holdout_excluded", False, "final_holdout_excluded"),
        ("final_holdout_excluded", 1, "final_holdout_excluded"),
        ("future_actual_leakage", True, "future_actual_leakage"),
        ("future_actual_leakage", 0, "future_actual_leakage"),
    ),
)
def test_existing_manifest_contract_is_enforced(
    tmp_path: Path,
    key: str,
    value: object,
    message: str,
) -> None:
    paths = _write_existing_fold(tmp_path / "folds", 1)
    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    manifest[key] = value
    paths.manifest.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        runner.validate_existing_fold(_config(tmp_path))


def test_manifest_validation_window_cannot_enter_final_holdout(tmp_path: Path) -> None:
    paths = _write_existing_fold(tmp_path / "folds", 8)
    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    manifest["validation_end"] = FINAL_HOLDOUT.holdout_start.isoformat()
    paths.manifest.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="validation_end"):
        runner.validate_existing_fold(_config(tmp_path, fold_id=8))


def test_parquet_footer_must_match_manifest_without_training(
    tmp_path: Path,
) -> None:
    paths = _write_existing_fold(tmp_path / "folds", 1)
    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    manifest["training_row_count"] += 1
    paths.manifest.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="row count does not match"):
        runner.validate_existing_fold(_config(tmp_path))


def test_markdown_rejects_any_canonical_holdout_scoring_claim() -> None:
    payload = runner._empty_results()
    payload["final_holdout_scored"] = True

    with pytest.raises(ValueError, match="final_holdout_scored=false"):
        runner.render_markdown_summary(payload)


def test_success_uses_parquet_fit_batched_guards_and_metric_accumulator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact_paths = _write_existing_fold(tmp_path / "folds", 1)
    _install_fake_adapter(monkeypatch, value=2.0)
    adapter_class = runner.FavoritaLightGBMAdapter
    guarded_batches: list[int] = []
    metric_batches: list[int] = []
    original_guard = runner._validate_validation_batch

    def tracked_guard(*args: object, **kwargs: object) -> None:
        frame = args[1]
        guarded_batches.append(len(frame))
        original_guard(*args, **kwargs)

    class TrackingAccumulator(FavoritaMetricAccumulator):
        def update(self, actual, prediction, perishable) -> None:
            actual_values = tuple(actual)
            metric_batches.append(len(actual_values))
            super().update(actual_values, prediction, perishable)

    monkeypatch.setattr(runner, "_validate_validation_batch", tracked_guard)
    monkeypatch.setattr(runner, "FavoritaMetricAccumulator", TrackingAccumulator)
    clock = iter((10.0, 12.5))
    monkeypatch.setattr(runner, "perf_counter", lambda: next(clock))

    result_paths = runner.run_single_fold(_config(tmp_path))

    assert adapter_class.fitted_paths == [artifact_paths.training]
    assert len(adapter_class.prediction_batch_sizes) > 1
    assert guarded_batches == adapter_class.prediction_batch_sizes
    assert metric_batches == adapter_class.prediction_batch_sizes
    payload = json.loads(result_paths.experiment_results.read_text(encoding="utf-8"))
    record = payload["folds"]["1"]
    assert payload["completed_folds"] == [1]
    assert payload["final_holdout_scored"] is False
    assert record["runtime_seconds"] == 2.5
    assert record["training_rows"] > 0
    assert record["validation_rows"] == sum(metric_batches)
    assert set(record["metrics"]) == set(runner.METRIC_NAMES)
    assert result_paths.markdown_summary.read_text(encoding="utf-8") == (
        runner.render_markdown_summary(payload)
    )
    assert set(
        path.name for path in result_paths.experiment_results.parent.iterdir()
    ) == {
        runner.EXPERIMENT_RESULTS_FILENAME,
        runner.MARKDOWN_SUMMARY_FILENAME,
    }


def test_separate_invocations_preserve_prior_fold_and_rerun_replaces_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_existing_fold(tmp_path / "folds", 1)
    _write_existing_fold(tmp_path / "folds", 3)
    clock = iter((0.0, 1.0, 10.0, 12.0, 20.0, 23.0))
    monkeypatch.setattr(runner, "perf_counter", lambda: next(clock))

    _install_fake_adapter(monkeypatch, value=1.0)
    paths = runner.run_single_fold(_config(tmp_path, fold_id=3))
    _install_fake_adapter(monkeypatch, value=2.0)
    runner.run_single_fold(_config(tmp_path, fold_id=1))
    before_rerun = json.loads(paths.experiment_results.read_text(encoding="utf-8"))
    fold_3_before = before_rerun["folds"]["3"]
    first_fold_1 = before_rerun["folds"]["1"]

    _install_fake_adapter(monkeypatch, value=4.0)
    runner.run_single_fold(_config(tmp_path, fold_id=1))
    after_rerun = json.loads(paths.experiment_results.read_text(encoding="utf-8"))

    assert after_rerun["completed_folds"] == [1, 3]
    assert tuple(after_rerun["folds"]) == ("1", "3")
    assert after_rerun["folds"]["3"] == fold_3_before
    assert after_rerun["folds"]["1"]["runtime_seconds"] == 3.0
    assert after_rerun["folds"]["1"] != first_fold_1
    assert paths.markdown_summary.read_text(encoding="utf-8") == (
        runner.render_markdown_summary(after_rerun)
    )


def test_failed_fold_preserves_existing_json_and_markdown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_existing_fold(tmp_path / "folds", 1)
    _install_fake_adapter(monkeypatch)
    paths = runner.run_single_fold(_config(tmp_path))
    json_before = paths.experiment_results.read_bytes()
    markdown_before = paths.markdown_summary.read_bytes()

    class FailingAdapter:
        def fit_parquet(self, path: Path) -> None:
            raise RuntimeError("training failed")

    monkeypatch.setattr(runner, "FavoritaLightGBMAdapter", FailingAdapter)

    with pytest.raises(RuntimeError, match="training failed"):
        runner.run_single_fold(_config(tmp_path))

    assert paths.experiment_results.read_bytes() == json_before
    assert paths.markdown_summary.read_bytes() == markdown_before
