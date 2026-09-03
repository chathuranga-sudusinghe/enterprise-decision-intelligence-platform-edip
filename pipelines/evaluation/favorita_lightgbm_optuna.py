"""Shared paired Optuna contract for SCRUM-59 Favorita LightGBM tuning."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Literal, Protocol

import lightgbm as lgb
import numpy as np

from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
    validate_approved_contract,
)
from pipelines.models.favorita_lightgbm import LIGHTGBM_PARAMETERS

JIRA_ID = "SCRUM-59"
EXPERIMENT_NAME = "Shared LightGBM Optuna tuning for Contextual and Time-Aware"
EXPERIMENT_VERSION = "1.0"
TRIAL_BUDGET = 6
OPTUNA_SEED = 42
METRIC_NAMES: tuple[str, ...] = (
    "mae",
    "rmse",
    "wape",
    "bias",
    "rmsle",
    "nwrmsle",
)
TUNABLE_PARAMETER_NAMES: tuple[str, ...] = (
    "learning_rate",
    "num_leaves",
    "min_data_in_leaf",
    "feature_fraction",
    "num_boost_round",
)
SEARCH_SPACE: Mapping[str, Mapping[str, object]] = MappingProxyType(
    {
        "learning_rate": MappingProxyType(
            {"kind": "float", "low": 0.01, "high": 0.15, "log": True}
        ),
        "num_leaves": MappingProxyType(
            {"kind": "int", "low": 16, "high": 128}
        ),
        "min_data_in_leaf": MappingProxyType(
            {"kind": "int", "low": 10, "high": 200, "log": True}
        ),
        "feature_fraction": MappingProxyType(
            {"kind": "float", "low": 0.6, "high": 1.0}
        ),
        "num_boost_round": MappingProxyType(
            {"kind": "int", "low": 100, "high": 500, "step": 50}
        ),
    }
)


class OptunaTrial(Protocol):
    def suggest_float(
        self,
        name: str,
        low: float,
        high: float,
        *,
        step: float | None = None,
        log: bool = False,
    ) -> float: ...

    def suggest_int(
        self,
        name: str,
        low: int,
        high: int,
        *,
        step: int = 1,
        log: bool = False,
    ) -> int: ...


@dataclass(frozen=True, slots=True)
class PairedTrialParameters:
    learning_rate: float
    num_leaves: int
    min_data_in_leaf: int
    feature_fraction: float
    num_boost_round: int

    def model_parameters(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "learning_rate": self.learning_rate,
                "num_leaves": self.num_leaves,
                "min_data_in_leaf": self.min_data_in_leaf,
                "feature_fraction": self.feature_fraction,
            }
        )

    def as_dict(self) -> dict[str, float | int]:
        return {
            "learning_rate": self.learning_rate,
            "num_leaves": self.num_leaves,
            "min_data_in_leaf": self.min_data_in_leaf,
            "feature_fraction": self.feature_fraction,
            "num_boost_round": self.num_boost_round,
        }


@dataclass(frozen=True, slots=True)
class ComputeModeResolution:
    mode: Literal["gpu", "cpu"]
    model_parameters: Mapping[str, object]
    gpu_smoke_check_succeeded: bool
    detail: str


def suggest_parameters(trial: OptunaTrial) -> PairedTrialParameters:
    """Suggest exactly the five approved shared tuning dimensions."""

    return PairedTrialParameters(
        learning_rate=trial.suggest_float(
            "learning_rate", 0.01, 0.15, log=True
        ),
        num_leaves=trial.suggest_int("num_leaves", 16, 128),
        min_data_in_leaf=trial.suggest_int(
            "min_data_in_leaf", 10, 200, log=True
        ),
        feature_fraction=trial.suggest_float("feature_fraction", 0.6, 1.0),
        num_boost_round=trial.suggest_int(
            "num_boost_round", 100, 500, step=50
        ),
    )


def validate_paired_parameters(parameters: PairedTrialParameters) -> None:
    values = parameters.as_dict()
    if tuple(values) != TUNABLE_PARAMETER_NAMES:
        raise ValueError("Paired trial parameters must match the tuning contract")
    for name, specification in SEARCH_SPACE.items():
        value = values[name]
        low = specification["low"]
        high = specification["high"]
        if not low <= value <= high:  # type: ignore[operator]
            raise ValueError(f"{name} is outside the approved search space")
    if (parameters.num_boost_round - 100) % 50:
        raise ValueError("num_boost_round must use the approved step of 50")


def shared_trial_mae(contextual_mae: float, time_aware_mae: float) -> float:
    """Return the paired scalar used only for Optuna trial ranking."""

    if not isfinite(contextual_mae) or not isfinite(time_aware_mae):
        raise ValueError("Both paired MAE values must be finite")
    return (contextual_mae + time_aware_mae) / 2.0


def validate_metric_profile(metrics: Mapping[str, object]) -> None:
    if tuple(metrics) != METRIC_NAMES and set(metrics) != set(METRIC_NAMES):
        raise ValueError("Metric profile must retain exactly all six metrics")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(float(value))
        for value in metrics.values()
    ):
        raise ValueError("Metric profile values must be finite numbers")


def validate_tuning_contract() -> None:
    """Validate reuse of the frozen temporal and protected-holdout contracts."""

    validate_approved_contract()
    if TRIAL_BUDGET != 6:
        raise ValueError("SCRUM-59 requires exactly six paired trials")
    if tuple(SEARCH_SPACE) != TUNABLE_PARAMETER_NAMES:
        raise ValueError("Search space differs from the five approved parameters")
    if FORECAST_HORIZONS != tuple(range(1, 17)):
        raise ValueError("Tuning horizons must be exactly 1 through 16")
    if any(fold.validation_end >= FINAL_HOLDOUT.holdout_start for fold in APPROVED_FOLDS):
        raise ValueError("Canonical folds must exclude the protected holdout")


def _gpu_smoke_train() -> None:
    features = np.array(
        [[0.0, 1.0], [1.0, 0.0], [0.5, 0.5], [1.0, 1.0]], dtype="float32"
    )
    labels = np.array([0.0, 1.0, 0.5, 1.5], dtype="float32")
    dataset = lgb.Dataset(features, label=labels)
    parameters = dict(LIGHTGBM_PARAMETERS)
    parameters["device_type"] = "gpu"
    lgb.train(parameters, dataset, num_boost_round=1)


def resolve_compute_mode(
    smoke_train: Callable[[], None] = _gpu_smoke_train,
) -> ComputeModeResolution:
    """Resolve compute once; later real-study failures are intentionally fatal."""

    try:
        smoke_train()
    except Exception as exc:  # LightGBM raises multiple backend-specific errors.
        return ComputeModeResolution(
            mode="cpu",
            model_parameters=MappingProxyType({"device_type": "cpu"}),
            gpu_smoke_check_succeeded=False,
            detail=f"GPU unavailable; CPU frozen: {type(exc).__name__}: {exc}",
        )
    return ComputeModeResolution(
        mode="gpu",
        model_parameters=MappingProxyType({"device_type": "gpu"}),
        gpu_smoke_check_succeeded=True,
        detail="Tiny synthetic LightGBM GPU training succeeded; GPU frozen.",
    )


validate_tuning_contract()
