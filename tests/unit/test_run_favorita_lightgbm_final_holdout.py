from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from pipelines.evaluation import run_favorita_lightgbm_final_holdout as runner


def _source(path: Path) -> None:
    pq.write_table(
        pa.table(
            {
                "date": [pa.scalar("2017-01-01", type=pa.string())],
                "store_nbr": [1],
            }
        ),
        path,
    )


def _artifact_validation(*, validation: bool, digest: str) -> dict[str, object]:
    if validation:
        return {
            "rows": 16,
            "forecast_date_min": "2017-07-31",
            "forecast_date_max": "2017-08-15",
            "horizons": list(range(1, 17)),
            "row_key_target_sha256": digest,
        }
    return {
        "rows": 100,
        "forecast_date_min": "2017-01-01",
        "forecast_date_max": "2017-07-30",
        "horizons": list(range(1, 17)),
        "row_key_target_sha256": digest,
    }


def _footer_boundaries(path: Path, *, feature_profile: str) -> dict[str, object]:
    del feature_profile
    if path.name == "validation.parquet":
        return {
            "rows": 16,
            "forecast_origin_min": "2017-07-30",
            "forecast_origin_max": "2017-07-30",
            "forecast_date_min": "2017-07-31",
            "forecast_date_max": "2017-08-15",
            "horizons": list(range(1, 17)),
        }
    return {
        "rows": 100,
        "forecast_origin_min": "2016-12-31",
        "forecast_origin_max": "2017-07-29",
        "forecast_date_min": "2017-01-01",
        "forecast_date_max": "2017-07-30",
        "horizons": list(range(1, 17)),
    }


class FakeWriter:
    created_paths: list[Path] = []

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"temporary predictions")
        self.created_paths.append(path)

    def close(self) -> None:
        pass

    def abort(self) -> None:
        self.path.unlink(missing_ok=True)


class FakeAdapter:
    instances: list["FakeAdapter"] = []

    def __init__(
        self,
        *,
        feature_columns,
        model_parameters,
        num_boost_round,
    ) -> None:
        self.feature_columns = feature_columns
        self.model_parameters = dict(model_parameters)
        self.num_boost_round = num_boost_round
        self.feature_contract_name = (
            "contextual" if len(feature_columns) < 40 else "time-aware"
        )
        self.training_path: Path | None = None
        self.instances.append(self)

    def fit_parquet(self, path: Path) -> None:
        self.training_path = path


def _fake_stream(**kwargs):
    model = kwargs["model"]
    overall = kwargs["overall_accumulator"]
    horizons = kwargs["horizon_accumulators"]
    for horizon in runner.FORECAST_HORIZONS:
        actual = [float(horizon)]
        prediction = [float(horizon) + (0.5 if model.feature_contract_name == "contextual" else 0.25)]
        perishable = [horizon % 2]
        overall.update(actual, prediction, perishable)
        horizons[horizon].update(actual, prediction, perishable)
    effective = dict(runner.LIGHTGBM_PARAMETERS)
    effective.update(model.model_parameters)
    return SimpleNamespace(
        row_count=16,
        model_evidence={
            "model_parameters": effective,
            "num_boost_round": model.num_boost_round,
        },
    )


def _fake_materializer(calls: list[tuple[object, dict[str, object]]], digest="a" * 64):
    def materialize(config, **kwargs):
        calls.append((config, kwargs))
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        config.output_path.write_bytes(b"temporary features")
        return {
            "artifact_validation": _artifact_validation(
                validation=len(config.forecast_origins) == 1,
                digest=digest,
            )
        }

    return materialize


def test_final_holdout_runner_enforces_contract_and_publishes_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.parquet"
    _source(source)
    output = tmp_path / "evidence"
    calls: list[tuple[object, dict[str, object]]] = []
    FakeAdapter.instances = []
    FakeWriter.created_paths = []
    monkeypatch.setattr(runner, "_StreamingPredictionWriter", FakeWriter)

    paths = runner.run_final_holdout(
        runner.FinalHoldoutRunConfig(source_path=source, output_dir=output),
        materializer=_fake_materializer(calls),
        boundary_reader=_footer_boundaries,
        adapter_factory=FakeAdapter,
        stream_evaluator=_fake_stream,
    )

    evidence = json.loads(paths.json.read_text(encoding="utf-8"))
    assert evidence["jira_id"] == "SCRUM-19"
    assert evidence["holdout_contract"] == {
        "forecast_origin": "2017-07-30",
        "holdout_start": "2017-07-31",
        "holdout_end": "2017-08-15",
        "horizons": list(range(1, 17)),
    }
    assert evidence["parameter_source"] == (
        "SCRUM-59 Trial 0 frozen configuration"
    )
    assert evidence["frozen_model_configuration"] == {
        "model_parameters": {
            "learning_rate": 0.02757359293934948,
            "num_leaves": 123,
            "min_data_in_leaf": 89,
            "feature_fraction": 0.8394633936788146,
        },
        "num_boost_round": 150,
    }
    assert evidence["tuning_performed"] is False
    assert evidence["optuna_invoked"] is False
    assert evidence["additional_trials"] == 0
    assert evidence["same_effective_model_parameters_verified"] is True
    assert evidence["same_num_boost_round_verified"] is True
    assert evidence["cross_arm_validation_row_target_digest_verified"] is True
    assert "forecast_origin_max" not in evidence["dataset_evidence"]["contextual"]["training"]["artifact_validation"]
    assert evidence["dataset_evidence"]["contextual"]["training"]["footer_boundaries"]["forecast_origin_max"] == "2017-07-29"
    assert evidence["source_integrity"]["unchanged"] is True
    assert evidence["source_integrity"]["before"] == evidence["source_integrity"]["after"]
    assert evidence["hypothesis_conclusion"] is None
    assert set(evidence["metric_comparison"]) == set(runner.METRIC_NAMES)
    assert len(FakeAdapter.instances) == 2
    assert FakeAdapter.instances[0].model_parameters == FakeAdapter.instances[1].model_parameters
    assert all(model.num_boost_round == 150 for model in FakeAdapter.instances)
    assert all(
        set(result["overall_metrics"]) == set(runner.METRIC_NAMES)
        and len(result["horizon_metrics"]) == 16
        and [record["forecast_horizon"] for record in result["horizon_metrics"]]
        == list(range(1, 17))
        for result in evidence["arms"].values()
    )
    training_calls = [call for call in calls if len(call[0].forecast_origins) > 1]
    holdout_calls = [call for call in calls if len(call[0].forecast_origins) == 1]
    assert len(training_calls) == len(holdout_calls) == 2
    assert all(max(call[0].forecast_origins) < runner.FINAL_HOLDOUT.forecast_origin for call in training_calls)
    assert all(call[1]["forecast_date_cutoff"] == runner.FINAL_HOLDOUT.forecast_origin for call in training_calls)
    assert all(call[0].forecast_origins == (runner.FINAL_HOLDOUT.forecast_origin,) for call in holdout_calls)
    assert paths.markdown.is_file()
    assert "does not automatically conclude H0 or H1" in paths.markdown.read_text(encoding="utf-8")
    assert not list(output.rglob("*.parquet"))
    assert all(not path.exists() for path in FakeWriter.created_paths)


def test_digest_mismatch_fails_before_scoring_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.parquet"
    _source(source)
    output = tmp_path / "evidence"
    calls = 0

    def materialize(config, **kwargs):
        nonlocal calls
        calls += 1
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        config.output_path.write_bytes(b"temporary")
        digest = ("a" if config.feature_profile == "contextual" else "b") * 64
        return {
            "artifact_validation": _artifact_validation(
                validation=len(config.forecast_origins) == 1,
                digest=digest,
            )
        }

    FakeAdapter.instances = []
    monkeypatch.setattr(runner, "_StreamingPredictionWriter", FakeWriter)
    with pytest.raises(ValueError, match="row/target digests must match"):
        runner.run_final_holdout(
            runner.FinalHoldoutRunConfig(source_path=source, output_dir=output),
            materializer=materialize,
            boundary_reader=_footer_boundaries,
            adapter_factory=FakeAdapter,
            stream_evaluator=_fake_stream,
        )

    assert calls == 4
    assert FakeAdapter.instances == []
    assert not list(output.rglob("*.parquet"))
    assert not (output / runner.JSON_FILENAME).exists()


def test_scoring_failure_cleans_temporary_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.parquet"
    _source(source)
    output = tmp_path / "evidence"
    calls: list[tuple[object, dict[str, object]]] = []
    FakeAdapter.instances = []
    FakeWriter.created_paths = []
    monkeypatch.setattr(runner, "_StreamingPredictionWriter", FakeWriter)

    def fail_stream(**kwargs):
        raise RuntimeError("scoring failed")

    with pytest.raises(RuntimeError, match="scoring failed"):
        runner.run_final_holdout(
            runner.FinalHoldoutRunConfig(source_path=source, output_dir=output),
            materializer=_fake_materializer(calls),
            boundary_reader=_footer_boundaries,
            adapter_factory=FakeAdapter,
            stream_evaluator=fail_stream,
        )

    assert source.is_file()
    assert not list(output.rglob("*.parquet"))
    assert all(not path.exists() for path in FakeWriter.created_paths)


def test_runner_has_no_optuna_or_search_path() -> None:
    source = Path(runner.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert "optuna" not in imported_modules
    assert "create_study" not in source
    assert "suggest_" not in source
    assert "search_space" not in source
