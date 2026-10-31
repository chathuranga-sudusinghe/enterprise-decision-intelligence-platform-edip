"""Deterministic empirical intervals for the non-negative Favorita demand view."""

from __future__ import annotations

from typing import Any, Final

import numpy as np
import pandas as pd

from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
)

NOMINAL_COVERAGE = 0.90
QUANTILE_METHOD: Final = "linear"
PREDICTION_KEYS = ("forecast_origin", "forecast_date", "store_nbr", "item_nbr")
REQUIRED_COLUMNS = (
    "fold_id",
    "forecast_origin",
    "forecast_date",
    "forecast_horizon",
    "store_nbr",
    "item_nbr",
    "actual_unit_sales",
    "prediction",
    "perishable",
)


def _values(values: Any, name: str) -> np.ndarray:
    array = np.asarray(values)
    if array.ndim != 1 or not len(array):
        raise ValueError(f"{name} must be a non-empty one-dimensional array")
    if array.dtype.kind not in "iuf" or not np.isfinite(array).all():
        raise ValueError(f"{name} must contain finite real numbers")
    return array.astype("float64", copy=False)


def demand_residuals(actual: Any, prediction: Any) -> np.ndarray:
    observed = _values(actual, "actual")
    predicted = _values(prediction, "prediction")
    if len(observed) != len(predicted):
        raise ValueError("actual and prediction lengths differ")
    return np.maximum(observed, 0) - np.maximum(predicted, 0)


def residual_quantiles(residuals: Any) -> tuple[float, float]:
    values = _values(residuals, "residuals")
    lower, upper = np.quantile(values, [0.05, 0.95], method=QUANTILE_METHOD)
    return float(lower), float(upper)


def prediction_intervals(prediction: Any, q05: float, q95: float) -> pd.DataFrame:
    quantiles = _values([q05, q95], "quantiles")
    if quantiles[0] > quantiles[1]:
        raise ValueError("Quantiles must be ordered")
    point = np.maximum(_values(prediction, "prediction"), 0)
    with np.errstate(over="ignore"):
        lower = np.maximum(0, point + q05)
        upper = np.maximum(0, point + q95)
    if not np.isfinite(lower).all() or not np.isfinite(upper).all():
        raise ValueError("Interval arithmetic overflow")
    return pd.DataFrame(
        {
            "point_forecast": point,
            "lower_bound": lower,
            "upper_bound": upper,
            "interval_width": upper - lower,
            "uncertainty_level": NOMINAL_COVERAGE,
        }
    )


def interval_metrics(actual: Any, lower: Any, upper: Any) -> dict[str, Any]:
    observed = np.maximum(_values(actual, "actual"), 0)
    lo, hi = _values(lower, "lower"), _values(upper, "upper")
    if not (len(observed) == len(lo) == len(hi)):
        raise ValueError("Metric input lengths differ")
    if (lo < 0).any() or (hi < lo).any():
        raise ValueError("Bounds must be non-negative and ordered")
    covered = int(((lo <= observed) & (observed <= hi)).sum())
    # Divide before summing to avoid overflow of a finite mean.
    return {
        "row_count": len(observed),
        "covered_count": covered,
        "picp": covered / len(observed),
        "mpiw": float(np.sum((hi - lo) / len(observed))),
    }


def validate_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the complete four-fold evidence and return a canonical copy."""
    if frame.empty or not frame.columns.is_unique:
        raise ValueError("Prediction evidence must be non-empty with unique columns")
    if not set(REQUIRED_COLUMNS).issubset(frame.columns):
        raise ValueError("Missing required prediction columns")
    data = frame.loc[:, list(REQUIRED_COLUMNS)].copy()
    if data.isna().any().any():
        raise ValueError("Null prediction evidence is forbidden")
    for column in ("actual_unit_sales", "prediction"):
        _values(data[column].to_numpy(), column)
    for column in (
        "fold_id",
        "forecast_horizon",
        "store_nbr",
        "item_nbr",
        "perishable",
    ):
        if data[column].dtype.kind not in "iu":
            raise ValueError(f"{column} must contain integers")
    if (data[["store_nbr", "item_nbr"]] <= 0).any().any():
        raise ValueError("Store and item keys must be positive")
    if not data["perishable"].isin([0, 1]).all():
        raise ValueError("perishable must be binary")
    for column in ("forecast_origin", "forecast_date"):
        dates = pd.to_datetime(data[column], errors="raise")
        if (
            dates.dt.tz is not None
            or dates.isna().any()
            or not dates.eq(dates.dt.normalize()).all()
        ):
            raise ValueError("Dates must be timezone-naive calendar dates")
        data[column] = dates
    if (data["forecast_date"] >= pd.Timestamp(FINAL_HOLDOUT.holdout_start)).any():
        raise ValueError("Protected holdout and later dates are forbidden")
    if data.duplicated(list(PREDICTION_KEYS)).any():
        raise ValueError("Duplicate prediction keys")
    if set(data["fold_id"]) != {fold.fold_id for fold in APPROVED_FOLDS}:
        raise ValueError("Exactly four canonical folds are required")
    for fold in APPROVED_FOLDS:
        rows = data.loc[data["fold_id"] == fold.fold_id]
        if not rows["forecast_origin"].eq(pd.Timestamp(fold.forecast_origin)).all():
            raise ValueError("Noncanonical forecast origin")
        if set(rows["forecast_horizon"]) != set(FORECAST_HORIZONS):
            raise ValueError("Each fold requires horizons 1 through 16")
        expected = rows["forecast_origin"] + pd.to_timedelta(
            rows["forecast_horizon"], unit="D"
        )
        if not rows["forecast_date"].eq(expected).all():
            raise ValueError("Forecast date must equal origin plus horizon")
    return data.sort_values(
        ["fold_id", "forecast_horizon", "store_nbr", "item_nbr"]
    ).reset_index(drop=True)


def sequential_intervals(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Evaluate folds 2–4 using only completed earlier folds for calibration."""
    data = validate_predictions(frame)
    residuals = demand_residuals(data["actual_unit_sales"], data["prediction"])
    outputs = []
    calibrations = []
    for fold in APPROVED_FOLDS[1:]:
        earlier = data["fold_id"] < fold.fold_id
        if not (
            data.loc[earlier, "forecast_date"] < pd.Timestamp(fold.forecast_origin)
        ).all():
            raise ValueError("Calibration outcomes must precede evaluation origin")
        q05, q95 = residual_quantiles(residuals[earlier.to_numpy()])
        rows = data.loc[data["fold_id"] == fold.fold_id].reset_index(drop=True)
        intervals = prediction_intervals(rows["prediction"], q05, q95)
        rows["actual_demand"] = np.maximum(rows["actual_unit_sales"], 0)
        rows["residual"] = demand_residuals(
            rows["actual_unit_sales"], rows["prediction"]
        )
        outputs.append(pd.concat([rows, intervals], axis=1))
        calibrations.append(
            {
                "evaluation_fold": fold.fold_id,
                "calibration_folds": list(range(1, fold.fold_id)),
                "residual_count": int(earlier.sum()),
                "latest_calibration_target": data.loc[earlier, "forecast_date"]
                .max()
                .date()
                .isoformat(),
                "evaluation_origin": fold.forecast_origin.isoformat(),
                "q05": q05,
                "q95": q95,
            }
        )
    q05, q95 = residual_quantiles(residuals)
    calibration = {
        "nominal_coverage": NOMINAL_COVERAGE,
        "quantile_method": QUANTILE_METHOD,
        "residual_definition": "max(actual_unit_sales, 0) - max(prediction, 0)",
        "pooling": "global across stores, items, and horizons",
        "warmup_fold": 1,
        "sequential": calibrations,
        "final_calibration": {
            "calibration_folds": [1, 2, 3, 4],
            "residual_count": len(data),
            "latest_calibration_target": data["forecast_date"].max().date().isoformat(),
            "q05": q05,
            "q95": q95,
            "independently_evaluated": False,
            "usage": "Later approved development only; no protected holdout scoring under issue #128",
        },
    }
    return pd.concat(outputs, ignore_index=True), calibration
