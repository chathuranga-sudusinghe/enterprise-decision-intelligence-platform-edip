from __future__ import annotations

from pipelines.evaluation.favorita_lightgbm_optuna import (
    METRIC_NAMES,
    OPTUNA_SEED,
    SEARCH_SPACE,
    TRIAL_BUDGET,
    TUNABLE_PARAMETER_NAMES,
    PairedTrialParameters,
    resolve_compute_mode,
    shared_trial_mae,
    validate_metric_profile,
    validate_tuning_contract,
)
from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
)


def test_fixed_trial_search_and_temporal_contracts() -> None:
    validate_tuning_contract()

    assert TRIAL_BUDGET == 6
    assert OPTUNA_SEED == 42
    assert tuple(SEARCH_SPACE) == TUNABLE_PARAMETER_NAMES == (
        "learning_rate",
        "num_leaves",
        "min_data_in_leaf",
        "feature_fraction",
        "num_boost_round",
    )
    assert FORECAST_HORIZONS == tuple(range(1, 17))
    assert len(APPROVED_FOLDS) == 4
    assert max(fold.validation_end for fold in APPROVED_FOLDS) < (
        FINAL_HOLDOUT.holdout_start
    )


def test_one_immutable_parameter_configuration_is_reusable_by_both_arms() -> None:
    parameters = PairedTrialParameters(0.05, 31, 20, 0.9, 150)

    contextual = dict(parameters.model_parameters())
    time_aware = dict(parameters.model_parameters())

    assert contextual == time_aware
    assert parameters.as_dict()["num_boost_round"] == 150


def test_shared_objective_is_arithmetic_mean() -> None:
    assert shared_trial_mae(2.0, 4.0) == 3.0


def test_all_metrics_are_retained_and_bias_remains_signed() -> None:
    metrics = {
        "mae": 1.0,
        "rmse": 2.0,
        "wape": 0.3,
        "bias": -0.4,
        "rmsle": 0.5,
        "nwrmsle": 0.6,
    }

    validate_metric_profile(metrics)

    assert tuple(metrics) == METRIC_NAMES
    assert metrics["bias"] < 0


def test_compute_mode_is_resolved_once_and_shared_for_gpu_or_cpu() -> None:
    calls = 0

    def gpu_success() -> None:
        nonlocal calls
        calls += 1

    gpu = resolve_compute_mode(gpu_success)

    def gpu_failure() -> None:
        raise RuntimeError("no GPU")

    cpu = resolve_compute_mode(gpu_failure)

    assert calls == 1
    assert gpu.mode == "gpu"
    assert gpu.model_parameters == {"device_type": "gpu"}
    assert cpu.mode == "cpu"
    assert cpu.model_parameters == {"device_type": "cpu"}

