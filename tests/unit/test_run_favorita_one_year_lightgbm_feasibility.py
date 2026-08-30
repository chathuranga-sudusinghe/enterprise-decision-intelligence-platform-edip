from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from pipelines.evaluation import (
    run_favorita_one_year_lightgbm_feasibility as runner,
)


def _summary(path: Path) -> dict[str, Any]:
    return {
        "rows": 123,
        "columns": 40,
        "row_groups": 1,
        "forecast_date_min": runner.TARGET_START.isoformat(),
        "forecast_date_max": runner.TARGET_END.isoformat(),
        "store_cardinality": 54,
        "item_cardinality": 10,
        "horizons": list(runner.FORECAST_HORIZONS),
        "grain_duplicate_count": 0,
        "null_counts": {},
        "schema": {},
        "creation_status": "created",
        "artifact_path": path.as_posix(),
        "parquet_size_bytes": 7,
        "artifact_preparation_runtime_seconds": 1.0,
    }


def test_experimental_origin_scope_is_daily_and_holdout_safe() -> None:
    origins = runner.training_origins()

    assert origins[0] == date(2016, 7, 29)
    assert origins[-1] == date(2017, 7, 14)
    assert origins == tuple(
        origins[0] + timedelta(days=offset) for offset in range(len(origins))
    )
    assert origins[0] + timedelta(days=1) == runner.TARGET_START
    assert origins[-1] + timedelta(days=16) == runner.TARGET_END
    assert runner.TARGET_END < runner.FINAL_HOLDOUT.holdout_start


def test_prepare_uses_existing_full_store_feature_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "cleaned.parquet"
    source_path.write_bytes(b"source")
    config = runner.FeasibilityConfig(
        source_path=source_path,
        artifact_root=tmp_path / "experiment",
    )
    received: dict[str, Any] = {}

    def fake_materialize(build_config, **kwargs):
        received["config"] = build_config
        received["kwargs"] = kwargs
        build_config.output_path.parent.mkdir(parents=True)
        build_config.output_path.write_bytes(b"parquet")
        return {
            "processed_stores": list(runner.ALL_FAVORITA_STORES),
            "artifact_validation": _summary(build_config.output_path),
        }

    monkeypatch.setattr(runner, "materialize_feature_dataset", fake_materialize)

    summary = runner.prepare_training_artifact(config)

    build_config = received["config"]
    assert build_config.forecast_origins == runner.training_origins()
    assert build_config.store_batches == runner.ALL_STORE_BATCHES
    assert build_config.max_items_per_store is None
    assert build_config.allow_assumed_future_promotion is False
    assert build_config.allow_assumed_future_holidays is False
    assert build_config.overwrite is False
    assert received["kwargs"] == {
        "forecast_date_cutoff": runner.TARGET_END,
        "drop_targets_without_origin_history": True,
        "bounded_memory_validation": True,
        "reuse_source_across_origins": True,
        "progress_prefix": "[Feasibility]",
        "progress_phase": "features",
    }
    assert summary["creation_status"] == "created"
    assert summary["artifact_path"] == config.training_path.as_posix()


def test_run_reports_scope_and_trains_existing_parquet_adapter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = runner.FeasibilityConfig(
        source_path=tmp_path / "source.parquet",
        artifact_root=tmp_path / "experiment",
    )
    config.training_path.parent.mkdir(parents=True)
    config.training_path.write_bytes(b"parquet")
    fitted_paths: list[Path] = []

    class FakeAdapter:
        def fit_parquet(self, path: Path) -> None:
            fitted_paths.append(path)

    monkeypatch.setattr(runner, "prepare_training_artifact", lambda _config: _summary(config.training_path))
    monkeypatch.setattr(runner, "FavoritaLightGBMAdapter", FakeAdapter)
    monkeypatch.setattr(runner, "_peak_process_ram_gib", lambda: 1.25)

    result = runner.run_feasibility(config)

    assert fitted_paths == [config.training_path]
    assert result["training_status"] == "succeeded"
    assert result["peak_process_ram_gib"] == 1.25
    output = capsys.readouterr().out
    assert "[Feasibility] training rows: 123" in output
    assert "[Feasibility] target dates: 2016-07-30 -> 2017-07-30" in output
    assert "[Feasibility] observed stores: 54 of 54" in output
    assert "[Feasibility] training status: SUCCEEDED" in output


def test_training_failure_preserves_valid_experimental_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = runner.FeasibilityConfig(
        source_path=tmp_path / "source.parquet",
        artifact_root=tmp_path / "experiment",
    )
    config.training_path.parent.mkdir(parents=True)
    config.training_path.write_bytes(b"parquet")

    class FailingAdapter:
        def fit_parquet(self, _path: Path) -> None:
            raise MemoryError("bounded feasibility fixture")

    monkeypatch.setattr(runner, "prepare_training_artifact", lambda _config: _summary(config.training_path))
    monkeypatch.setattr(runner, "FavoritaLightGBMAdapter", FailingAdapter)

    with pytest.raises(MemoryError, match="bounded feasibility fixture"):
        runner.run_feasibility(config)

    assert config.training_path.read_bytes() == b"parquet"
    output = capsys.readouterr().out
    assert "[Feasibility] training status: FAILED" in output
    assert "MemoryError: bounded feasibility fixture" in output
