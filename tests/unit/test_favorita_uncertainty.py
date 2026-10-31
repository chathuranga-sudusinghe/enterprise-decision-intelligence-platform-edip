from __future__ import annotations

from typing import cast

import numpy as np
import pandas as pd
import pytest

from pipelines.evaluation.favorita_temporal_validation import APPROVED_FOLDS
from pipelines.evaluation.favorita_uncertainty import (
    demand_residuals,
    interval_metrics,
    prediction_intervals,
    residual_quantiles,
    sequential_intervals,
    validate_predictions,
)


def prediction_fixture() -> pd.DataFrame:
    # Unequal fold populations make unweighted fold averaging observably wrong.
    return pd.DataFrame(
        [
            {
                "fold_id": f.fold_id,
                "forecast_origin": pd.Timestamp(f.forecast_origin),
                "forecast_date": pd.Timestamp(f.forecast_origin) + pd.Timedelta(days=h),
                "forecast_horizon": h,
                "store_nbr": 1,
                "item_nbr": item,
                "actual_unit_sales": float(
                    h + (1 if f.fold_id == 4 and item == 1 else f.fold_id)
                ),
                "prediction": float(h),
                "perishable": 0,
            }
            for f in APPROVED_FOLDS
            for h in range(1, 17)
            for item in range(1, f.fold_id + 1)
        ]
    )


def test_exact_demand_quantiles_and_clipped_bounds() -> None:
    residuals = demand_residuals([-5, 1, 4, 10], [-2, 3, 1, 5])
    np.testing.assert_array_equal(residuals, [0, -2, 3, 5])
    assert residual_quantiles(residuals) == pytest.approx((-1.7, 4.7))
    result = prediction_intervals([-3, 2, 10], -5, -1)
    assert result.to_dict("list") == {
        "point_forecast": [0, 2, 10],
        "lower_bound": [0, 0, 5],
        "upper_bound": [0, 1, 9],
        "interval_width": [0, 1, 4],
        "uncertainty_level": [0.9, 0.9, 0.9],
    }


def test_metrics_include_boundaries_and_clip_actual_demand() -> None:
    assert interval_metrics([-2, 2, 5, 7], [0, 1, 5, 0], [0, 2, 6, 6]) == {
        "row_count": 4,
        "covered_count": 3,
        "picp": 0.75,
        "mpiw": 2.0,
    }


@pytest.mark.parametrize("bad", [[], [np.nan], [np.inf], [True], ["1"], [[1]]])
def test_invalid_residuals_rejected(bad: object) -> None:
    with pytest.raises(ValueError):
        residual_quantiles(bad)


def test_invalid_lengths_and_bounds_rejected() -> None:
    with pytest.raises(ValueError, match="length"):
        demand_residuals([1], [1, 2])
    with pytest.raises(ValueError, match="ordered"):
        prediction_intervals([1], 2, 1)
    with pytest.raises(ValueError, match="length"):
        interval_metrics([1], [0, 1], [2])
    with pytest.raises(ValueError, match="ordered"):
        interval_metrics([1], [2], [1])
    with pytest.raises(ValueError, match="overflow"):
        prediction_intervals([1.7e308], 1.7e308, 1.7e308)


def test_calibration_never_uses_current_or_future_outcomes() -> None:
    frame = prediction_fixture()
    original = frame.copy(deep=True)
    output, calibration = sequential_intervals(frame)
    pd.testing.assert_frame_equal(frame, original)
    assert set(output.fold_id) == {2, 3, 4}
    assert len(output) == 144
    assert calibration["sequential"][0]["q05"] == 1
    assert calibration["sequential"][0]["q95"] == 1
    assert [r["residual_count"] for r in calibration["sequential"]] == [16, 48, 96]
    for changed_fold in (2, 3, 4):
        changed = frame.copy()
        changed.loc[changed.fold_id >= changed_fold, "actual_unit_sales"] += 1000
        altered, _ = sequential_intervals(changed)
        columns = ["point_forecast", "lower_bound", "upper_bound", "interval_width"]
        pd.testing.assert_frame_equal(
            output.loc[output.fold_id <= changed_fold, columns],
            altered.loc[altered.fold_id <= changed_fold, columns],
        )
    assert calibration["final_calibration"]["independently_evaluated"] is False
    pd.testing.assert_frame_equal(
        output[["actual_unit_sales", "prediction"]],
        frame.loc[frame.fold_id > 1, ["actual_unit_sales", "prediction"]].reset_index(
            drop=True
        ),
    )


def test_shuffled_inputs_produce_identical_results() -> None:
    frame = prediction_fixture()
    expected, calibration = sequential_intervals(frame)
    actual, shuffled_calibration = sequential_intervals(
        frame.sample(frac=1, random_state=8)
    )
    pd.testing.assert_frame_equal(actual, expected)
    assert shuffled_calibration == calibration


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("duplicate", "Duplicate"),
        ("holdout", "holdout"),
        ("origin", "origin"),
        ("date", "origin plus horizon"),
        ("missing_fold", "four"),
        ("missing_horizon", "horizons"),
        ("nan", "Null"),
        ("infinite", "finite"),
        ("fractional_key", "integers"),
        ("timezone", "timezone"),
    ],
)
def test_invalid_prediction_evidence(mutation: str, match: str) -> None:
    frame = prediction_fixture()
    if mutation == "duplicate":
        frame = pd.concat([frame, frame.iloc[:1]])
    elif mutation == "holdout":
        frame.loc[0, "forecast_date"] = pd.Timestamp("2017-07-31")
    elif mutation == "origin":
        frame.loc[0, "forecast_origin"] = pd.Timestamp("2017-02-27")
    elif mutation == "date":
        frame.loc[0, "forecast_date"] = cast(
            pd.Timestamp, frame.loc[0, "forecast_date"]
        ) + pd.Timedelta(days=17)
    elif mutation == "missing_fold":
        frame = frame.loc[frame.fold_id != 1]
    elif mutation == "missing_horizon":
        frame = frame.loc[~((frame.fold_id == 1) & (frame.forecast_horizon == 16))]
    elif mutation == "nan":
        frame.loc[0, "prediction"] = np.nan
    elif mutation == "infinite":
        frame.loc[0, "prediction"] = np.inf
    elif mutation == "fractional_key":
        frame["item_nbr"] = frame.item_nbr.astype(float) + 0.5
    else:
        frame["forecast_date"] = frame.forecast_date.dt.tz_localize("UTC")
    with pytest.raises(ValueError, match=match):
        validate_predictions(frame)
