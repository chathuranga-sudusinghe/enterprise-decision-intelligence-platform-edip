from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType

import pytest

from pipelines.evaluation.favorita_lightgbm_optuna import (
    METRIC_NAMES,
    ComputeModeResolution,
)
from pipelines.evaluation.run_favorita_lightgbm_optuna_tuning import (
    TuningRunConfig,
    run_tuning,
)


def _metrics(offset: float) -> dict[str, float]:
    return {
        "mae": 1.0 + offset,
        "rmse": 2.0 + offset,
        "wape": 0.3 + offset,
        "bias": -0.2 + offset,
        "rmsle": 0.4 + offset,
        "nwrmsle": 0.5 + offset,
    }


def _arm_result(offset: float) -> dict[str, object]:
    return {
        "overall_metrics": _metrics(offset),
        "fold_metrics": [
            {"fold_id": fold_id, **_metrics(offset)} for fold_id in range(1, 5)
        ],
        "horizon_metrics": [
            {"forecast_horizon": horizon, **_metrics(offset)}
            for horizon in range(1, 17)
        ],
    }


def test_runner_executes_six_paired_trials_and_writes_complete_evidence(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.parquet"
    source.touch()
    calls: list[tuple[str, object, object, Path]] = []

    def evaluator(arm: str, parameters, compute, output_dir: Path):
        calls.append((arm, parameters, compute, output_dir))
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "predictions.parquet").write_bytes(b"temporary")
        return _arm_result(0.0 if arm == "contextual" else 0.25)

    compute = ComputeModeResolution(
        mode="cpu",
        model_parameters=MappingProxyType({"device_type": "cpu"}),
        gpu_smoke_check_succeeded=False,
        detail="fake CPU fallback",
    )
    paths = run_tuning(
        TuningRunConfig(source_path=source, output_dir=tmp_path / "tuning"),
        evaluator=evaluator,
        compute_resolver=lambda: compute,
    )

    evidence = json.loads(paths.json.read_text(encoding="utf-8"))
    assert len(calls) == 12
    assert [arm for arm, _, _, _ in calls] == [
        arm for _ in range(6) for arm in ("contextual", "time-aware")
    ]
    for index in range(0, len(calls), 2):
        assert calls[index][1] is calls[index + 1][1]
        assert calls[index][2] is calls[index + 1][2] is compute
    assert len(evidence["trials"]) == 6
    assert evidence["metric_names"] == list(METRIC_NAMES)
    assert evidence["research_contract"]["horizons"] == list(range(1, 17))
    assert len(evidence["research_contract"]["folds"]) == 4
    assert evidence["holdout_touched"] is False
    assert evidence["research_contract"]["protected_holdout"]["touched"] is False
    assert evidence["compute_mode"]["resolved_once"] is True
    assert evidence["compute_mode"]["shared_by_both_arms"] is True
    assert "best_optuna_trial_by_shared_mae" in evidence
    assert "best_optuna_parameter_configuration_by_shared_mae" in evidence
    assert "selected_common_parameter_configuration" not in evidence
    assert not list(paths.json.parent.rglob("predictions.parquet"))
    assert all(not output_dir.exists() for _, _, _, output_dir in calls)
    assert paths.markdown.is_file()
    markdown = paths.markdown.read_text(encoding="utf-8")
    assert "## Protected Holdout" in markdown
    assert "| Trial | Arm | MAE | RMSE | WAPE | Bias | RMSLE | NWRMSLE | Shared MAE |" in markdown
    assert markdown.count("| Contextual |") == 6
    assert markdown.count("| Time-Aware |") == 6


def test_failed_arm_evaluation_cleans_only_its_temporary_directory(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.parquet"
    source.touch()
    output_root = tmp_path / "tuning"
    observed_output: Path | None = None

    def failing_evaluator(arm: str, parameters, compute, output_dir: Path):
        nonlocal observed_output
        observed_output = output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "predictions.parquet").write_bytes(b"temporary")
        raise RuntimeError("original evaluation failure")

    compute = ComputeModeResolution(
        mode="cpu",
        model_parameters=MappingProxyType({"device_type": "cpu"}),
        gpu_smoke_check_succeeded=False,
        detail="fake CPU fallback",
    )

    with pytest.raises(RuntimeError, match="original evaluation failure"):
        run_tuning(
            TuningRunConfig(source_path=source, output_dir=output_root),
            evaluator=failing_evaluator,
            compute_resolver=lambda: compute,
        )

    assert observed_output is not None
    assert not observed_output.exists()
    assert not list(output_root.rglob("predictions.parquet"))
    assert source.is_file()
