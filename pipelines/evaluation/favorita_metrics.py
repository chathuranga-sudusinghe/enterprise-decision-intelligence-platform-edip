"""Deterministic SCRUM-17 forecasting metrics for Favorita evaluation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import fsum, isfinite, log1p, sqrt
from numbers import Real

NON_PERISHABLE_WEIGHT = 1.0
PERISHABLE_WEIGHT = 1.25


@dataclass(frozen=True, slots=True)
class ForecastMetricResults:
    """Immutable metric results for one explicitly selected evaluation slice."""

    mae: float
    rmse: float
    wape: float
    bias: float
    rmsle: float
    nwrmsle: float


def _finite_values(values: Iterable[Real], name: str) -> tuple[float, ...]:
    try:
        materialized = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be an iterable of real numbers") from exc

    if not materialized:
        raise ValueError(f"{name} must not be empty")

    validated: list[float] = []
    for value in materialized:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must contain only real numbers")
        converted = float(value)
        if not isfinite(converted):
            raise ValueError(f"{name} must contain only finite values")
        validated.append(converted)
    return tuple(validated)


def _paired_values(
    actual: Iterable[Real],
    prediction: Iterable[Real],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    actual_values = _finite_values(actual, "actual")
    prediction_values = _finite_values(prediction, "prediction")
    if len(actual_values) != len(prediction_values):
        raise ValueError("actual and prediction must have the same number of rows")
    return actual_values, prediction_values


def _non_negative_pairs(
    actual: Iterable[Real],
    prediction: Iterable[Real],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    actual_values, prediction_values = _paired_values(actual, prediction)
    return (
        tuple(max(value, 0.0) for value in actual_values),
        tuple(max(value, 0.0) for value in prediction_values),
    )


def mean_absolute_error(
    actual: Iterable[Real],
    prediction: Iterable[Real],
) -> float:
    """Return MAE on the original target and prediction values."""

    actual_values, prediction_values = _paired_values(actual, prediction)
    return fsum(
        abs(predicted - observed)
        for observed, predicted in zip(actual_values, prediction_values)
    ) / len(actual_values)


def root_mean_squared_error(
    actual: Iterable[Real],
    prediction: Iterable[Real],
) -> float:
    """Return RMSE on the original target and prediction values."""

    actual_values, prediction_values = _paired_values(actual, prediction)
    mean_squared_error = fsum(
        (predicted - observed) ** 2
        for observed, predicted in zip(actual_values, prediction_values)
    ) / len(actual_values)
    return sqrt(mean_squared_error)


def mean_forecast_error(
    actual: Iterable[Real],
    prediction: Iterable[Real],
) -> float:
    """Return Bias as mean(prediction - actual) on original values."""

    actual_values, prediction_values = _paired_values(actual, prediction)
    return fsum(
        predicted - observed
        for observed, predicted in zip(actual_values, prediction_values)
    ) / len(actual_values)


def weighted_absolute_percentage_error(
    actual: Iterable[Real],
    prediction: Iterable[Real],
) -> float:
    """Return WAPE as a ratio after evaluation-only non-negative clipping.

    A zero total evaluation target makes WAPE undefined and raises ValueError.
    Percentage reporting multiplies the returned ratio by 100.
    """

    evaluation_target, evaluation_prediction = _non_negative_pairs(
        actual, prediction
    )
    denominator = fsum(evaluation_target)
    if denominator == 0.0:
        raise ValueError("WAPE is undefined when total evaluation target is zero")
    numerator = fsum(
        abs(predicted - observed)
        for observed, predicted in zip(
            evaluation_target,
            evaluation_prediction,
        )
    )
    return numerator / denominator


def root_mean_squared_logarithmic_error(
    actual: Iterable[Real],
    prediction: Iterable[Real],
) -> float:
    """Return RMSLE after evaluation-only non-negative clipping."""

    evaluation_target, evaluation_prediction = _non_negative_pairs(
        actual, prediction
    )
    mean_squared_log_error = fsum(
        (log1p(predicted) - log1p(observed)) ** 2
        for observed, predicted in zip(
            evaluation_target,
            evaluation_prediction,
        )
    ) / len(evaluation_target)
    return sqrt(mean_squared_log_error)


def normalized_weighted_root_mean_squared_logarithmic_error(
    actual: Iterable[Real],
    prediction: Iterable[Real],
    perishable: Iterable[object],
) -> float:
    """Return NWRMSLE using Favorita perishability weights.

    Perishable rows receive weight 1.25 and non-perishable rows receive 1.0.
    The weighted squared log errors are normalized by the sum of row weights.
    """

    evaluation_target, evaluation_prediction = _non_negative_pairs(
        actual, prediction
    )
    try:
        perishable_values = tuple(perishable)
    except TypeError as exc:
        raise TypeError("perishable must be an iterable of binary indicators") from exc
    if len(perishable_values) != len(evaluation_target):
        raise ValueError(
            "perishable must have the same number of rows as actual and prediction"
        )
    if any(value not in (0, 1, False, True) for value in perishable_values):
        raise ValueError("perishable must contain only binary 0/1 indicators")

    weights = tuple(
        PERISHABLE_WEIGHT if bool(value) else NON_PERISHABLE_WEIGHT
        for value in perishable_values
    )
    weighted_squared_log_error = fsum(
        weight * (log1p(predicted) - log1p(observed)) ** 2
        for observed, predicted, weight in zip(
            evaluation_target,
            evaluation_prediction,
            weights,
        )
    )
    return sqrt(weighted_squared_log_error / fsum(weights))


def evaluate_favorita_forecasts(
    actual: Iterable[Real],
    prediction: Iterable[Real],
    perishable: Iterable[object],
) -> ForecastMetricResults:
    """Return the complete SCRUM-17 metric set for one evaluation slice."""

    actual_values, prediction_values = _paired_values(actual, prediction)
    perishable_values = tuple(perishable)
    return ForecastMetricResults(
        mae=mean_absolute_error(actual_values, prediction_values),
        rmse=root_mean_squared_error(actual_values, prediction_values),
        wape=weighted_absolute_percentage_error(actual_values, prediction_values),
        bias=mean_forecast_error(actual_values, prediction_values),
        rmsle=root_mean_squared_logarithmic_error(
            actual_values, prediction_values
        ),
        nwrmsle=normalized_weighted_root_mean_squared_logarithmic_error(
            actual_values,
            prediction_values,
            perishable_values,
        ),
    )
