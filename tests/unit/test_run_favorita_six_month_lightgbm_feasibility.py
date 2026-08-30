from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from pipelines.evaluation import (
    run_favorita_six_month_lightgbm_feasibility as runner,
)


def _artifact_validation() -> dict[str, Any]:
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
    }


def _summary(path: Path, *, size_bytes: int) -> dict[str, Any]:
    return {
        **_artifact_validation(),
        "creation_status": "created",
        "artifact_path": path.as_posix(),
        "parquet_size_bytes": size_bytes,
        "parquet_size_gib": size_bytes / (1024**3),
        "within_training_size_threshold": (
            size_bytes <= runner.SIZE_THRESHOLD_BYTES
        ),
        "artifact_preparation_runtime_seconds": 1.0,
    }


def test_six_month_origin_scope_is_daily_and_target_bounded() -> None:
    origins = runner.training_origins()

    assert origins[0] == date(2016, 12, 31)
    assert origins[-1] == date(2017, 6, 14)
    assert origins == tuple(
        origins[0] + timedelta(days=offset) for offset in range(len(origins))
    )
    assert origins[0] + timedelta(days=1) == runner.TARGET_START
    assert origins[-1] + timedelta(days=16) == runner.TARGET_END
    assert runner.TARGET_END < runner.FINAL_HOLDOUT.holdout_start


def test_prepare_reuses_full_store_feature_materialization_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "cleaned.parquet"
    source_path.write_bytes(b"source")
    config = runner.FeasibilityConfig(
        source_path=source_path,
        artifact_root=tmp_path / "six_month_experiment",
    )
    received: dict[str, Any] = {}

    def fake_materialize(build_config, **kwargs):
        received["config"] = build_config
        received["kwargs"] = kwargs
        build_config.output_path.parent.mkdir(parents=True)
        build_config.output_path.write_bytes(b"parquet")
        return {
            "processed_stores": list(runner.ALL_FAVORITA_STORES),
            "artifact_validation": _artifact_validation(),
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
        "progress_prefix": "[Six-month feasibility]",
        "progress_phase": "features",
    }
    assert summary["creation_status"] == "created"
    assert summary["parquet_size_bytes"] == len(b"parquet")


@pytest.mark.parametrize(
    ("size_bytes", "expected_message", "acceptable"),
    (
        (
            runner.SIZE_THRESHOLD_BYTES,
            "size threshold: ACCEPTABLE CANDIDATE (<= 3 GiB)",
            True,
        ),
        (
            runner.SIZE_THRESHOLD_BYTES + 1,
            "size threshold: EXCEEDS 3 GiB; do not train",
            False,
        ),
    ),
)
def test_run_reports_threshold_and_never_starts_lightgbm(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    size_bytes: int,
    expected_message: str,
    acceptable: bool,
) -> None:
    config = runner.FeasibilityConfig(
        source_path=tmp_path / "source.parquet",
        artifact_root=tmp_path / "six_month_experiment",
    )
    monkeypatch.setattr(
        runner,
        "prepare_training_artifact",
        lambda _config: _summary(config.training_path, size_bytes=size_bytes),
    )

    result = runner.run_feasibility(config)

    assert result["within_training_size_threshold"] is acceptable
    assert not hasattr(runner, "FavoritaLightGBMAdapter")
    output = capsys.readouterr().out
    assert "[Six-month feasibility] training rows: 123" in output
    assert "[Six-month feasibility] target dates: 2017-01-01 -> 2017-06-30" in output
    assert expected_message in output
    assert "[Six-month feasibility] LightGBM training: NOT STARTED" in output


def test_previous_one_year_artifact_root_is_rejected(tmp_path: Path) -> None:
    config = runner.FeasibilityConfig(
        source_path=tmp_path / "cleaned.parquet",
        artifact_root=runner.PREVIOUS_ONE_YEAR_ARTIFACT_ROOT,
    )

    with pytest.raises(ValueError, match="dedicated artifact root"):
        runner.prepare_training_artifact(config)
