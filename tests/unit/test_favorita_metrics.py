from __future__ import annotations

from math import log1p, sqrt

import pytest

from pipelines.evaluation.favorita_metrics import (
    evaluate_favorita_forecasts,
    mean_absolute_error,
    mean_forecast_error,
    normalized_weighted_root_mean_squared_logarithmic_error,
    root_mean_squared_error,
    root_mean_squared_logarithmic_error,
    weighted_absolute_percentage_error,
)


def test_perfect_predictions_return_exact_zero_for_every_metric() -> None:
    results = evaluate_favorita_forecasts(
        actual=(1.0, 2.0, 3.0),
        prediction=(1.0, 2.0, 3.0),
        perishable=(0, 1, 0),
    )

    assert results.mae == 0.0
    assert results.rmse == 0.0
    assert results.wape == 0.0
    assert results.bias == 0.0
    assert results.rmsle == 0.0
    assert results.nwrmsle == 0.0


@pytest.mark.parametrize(
    ("prediction", "expected_bias"),
    [
        ((3.0, 4.0), 1.0),
        ((1.0, 2.0), -1.0),
    ],
)
def test_bias_sign_identifies_over_and_under_forecasting(
    prediction: tuple[float, ...],
    expected_bias: float,
) -> None:
    assert mean_forecast_error((2.0, 3.0), prediction) == expected_bias


def test_negative_values_are_clipped_only_for_demand_oriented_metrics() -> None:
    actual = [-2.0, 4.0]
    prediction = [-5.0, 1.0]
    original_actual = actual.copy()
    original_prediction = prediction.copy()

    assert mean_absolute_error(actual, prediction) == 3.0
    assert root_mean_squared_error(actual, prediction) == 3.0
    assert mean_forecast_error(actual, prediction) == -3.0
    assert weighted_absolute_percentage_error(actual, prediction) == 0.75
    assert root_mean_squared_logarithmic_error(
        actual, prediction
    ) == pytest.approx(abs(log1p(1.0) - log1p(4.0)) / sqrt(2.0))
    assert actual == original_actual
    assert prediction == original_prediction


def test_wape_uses_total_absolute_error_over_total_non_negative_demand() -> None:
    assert weighted_absolute_percentage_error(
        actual=(10.0, 20.0),
        prediction=(8.0, 25.0),
    ) == pytest.approx(7.0 / 30.0)


def test_wape_rejects_zero_total_evaluation_target() -> None:
    with pytest.raises(ValueError, match="total evaluation target is zero"):
        weighted_absolute_percentage_error(
            actual=(-2.0, 0.0),
            prediction=(0.0, 1.0),
        )


def test_rmsle_uses_transformed_non_negative_values() -> None:
    expected = sqrt(
        (
            (log1p(0.0) - log1p(0.0)) ** 2
            + (log1p(3.0) - log1p(1.0)) ** 2
        )
        / 2.0
    )

    assert root_mean_squared_logarithmic_error(
        actual=(-4.0, 1.0),
        prediction=(-2.0, 3.0),
    ) == pytest.approx(expected)


def test_nwrmsle_uses_normalized_favorita_perishability_weights() -> None:
    expected = sqrt(
        (
            1.0 * (log1p(1.0) - log1p(0.0)) ** 2
            + 1.25 * (log1p(3.0) - log1p(0.0)) ** 2
        )
        / 2.25
    )
    weighted = normalized_weighted_root_mean_squared_logarithmic_error(
        actual=(0.0, 0.0),
        prediction=(1.0, 3.0),
        perishable=(0, 1),
    )
    unweighted = root_mean_squared_logarithmic_error(
        actual=(0.0, 0.0),
        prediction=(1.0, 3.0),
    )

    assert weighted == pytest.approx(expected)
    assert weighted > unweighted


def test_metric_inputs_must_have_equal_lengths_without_row_dropping() -> None:
    with pytest.raises(ValueError, match="same number of rows"):
        mean_absolute_error((1.0, 2.0), (1.0,))


def test_non_finite_values_are_rejected_without_row_dropping() -> None:
    with pytest.raises(ValueError, match="finite"):
        root_mean_squared_error((1.0, float("nan")), (1.0, 2.0))


def test_nwrmsle_rejects_non_binary_or_misaligned_weights() -> None:
    with pytest.raises(ValueError, match="binary"):
        normalized_weighted_root_mean_squared_logarithmic_error(
            (1.0, 2.0),
            (1.0, 2.0),
            (0, 2),
        )
    with pytest.raises(ValueError, match="same number of rows"):
        normalized_weighted_root_mean_squared_logarithmic_error(
            (1.0, 2.0),
            (1.0, 2.0),
            (1,),
        )
