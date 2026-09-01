from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta

import pytest

from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLD_ORIGINS,
    APPROVED_FOLDS,
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
    MODELING_TARGET_END,
    MODELING_TARGET_START,
    HoldoutWindow,
    TemporalValidationFold,
    derive_target_window,
    is_training_target_eligible,
    require_training_target_eligible,
    validate_approved_contract,
    validate_fold_contract,
    validate_forecast_date_horizon,
    validate_forecast_horizons,
    validate_holdout_contract,
)

EXPECTED_ORIGINS = (
    date(2017, 2, 28),
    date(2017, 4, 14),
    date(2017, 5, 31),
    date(2017, 7, 14),
)

EXPECTED_WINDOWS = (
    (date(2017, 3, 1), date(2017, 3, 16)),
    (date(2017, 4, 15), date(2017, 4, 30)),
    (date(2017, 6, 1), date(2017, 6, 16)),
    (date(2017, 7, 15), date(2017, 7, 30)),
)


def test_exact_four_approved_origins() -> None:
    assert APPROVED_FOLD_ORIGINS == EXPECTED_ORIGINS
    assert tuple(fold.forecast_origin for fold in APPROVED_FOLDS) == EXPECTED_ORIGINS


def test_exact_four_approved_validation_windows() -> None:
    assert (
        tuple((fold.validation_start, fold.validation_end) for fold in APPROVED_FOLDS)
        == EXPECTED_WINDOWS
    )


def test_origins_are_in_strict_chronological_order() -> None:
    assert all(
        current < following
        for current, following in zip(EXPECTED_ORIGINS, EXPECTED_ORIGINS[1:])
    )


def test_each_validation_window_contains_sixteen_dates() -> None:
    assert all(
        (fold.validation_end - fold.validation_start).days + 1 == 16
        for fold in APPROVED_FOLDS
    )


def test_each_validation_start_is_origin_plus_one() -> None:
    assert all(
        fold.validation_start == fold.forecast_origin + timedelta(days=1)
        for fold in APPROVED_FOLDS
    )


def test_each_validation_end_is_origin_plus_sixteen() -> None:
    assert all(
        fold.validation_end == fold.forecast_origin + timedelta(days=16)
        for fold in APPROVED_FOLDS
    )


def test_validation_windows_do_not_overlap() -> None:
    assert all(
        current.validation_end < following.validation_start
        for current, following in zip(APPROVED_FOLDS, APPROVED_FOLDS[1:])
    )


def test_validation_windows_do_not_overlap_final_holdout() -> None:
    assert all(
        fold.validation_end < FINAL_HOLDOUT.holdout_start for fold in APPROVED_FOLDS
    )


def test_exact_final_holdout_definition() -> None:
    assert FINAL_HOLDOUT.forecast_origin == date(2017, 7, 30)
    assert FINAL_HOLDOUT.holdout_start == date(2017, 7, 31)
    assert FINAL_HOLDOUT.holdout_end == date(2017, 8, 15)
    assert (FINAL_HOLDOUT.holdout_end - FINAL_HOLDOUT.holdout_start).days + 1 == 16


def test_exact_modeling_target_scope() -> None:
    assert MODELING_TARGET_START == date(2017, 1, 1)
    assert MODELING_TARGET_END == date(2017, 7, 30)
    assert APPROVED_FOLDS[-1].validation_end == MODELING_TARGET_END

def test_training_target_on_origin_is_eligible() -> None:
    origin = APPROVED_FOLDS[0].forecast_origin
    assert is_training_target_eligible(origin, origin)
    require_training_target_eligible(origin, origin)


def test_training_target_before_origin_is_eligible() -> None:
    origin = APPROVED_FOLDS[0].forecast_origin
    forecast_date = origin - timedelta(days=1)
    assert is_training_target_eligible(forecast_date, origin)
    require_training_target_eligible(forecast_date, origin)


def test_training_target_after_origin_is_rejected() -> None:
    origin = APPROVED_FOLDS[0].forecast_origin
    forecast_date = origin + timedelta(days=1)
    assert not is_training_target_eligible(forecast_date, origin)
    with pytest.raises(ValueError, match="on or before"):
        require_training_target_eligible(forecast_date, origin)


def test_incorrect_fold_duration_is_rejected() -> None:
    invalid_folds = list(APPROVED_FOLDS)
    invalid_folds[0] = replace(
        invalid_folds[0],
        validation_end=invalid_folds[0].validation_end + timedelta(days=1),
    )
    with pytest.raises(ValueError, match=r"origin \+ 16 days"):
        validate_fold_contract(invalid_folds)


def test_overlapping_folds_are_rejected() -> None:
    overlapping_origin = APPROVED_FOLDS[0].forecast_origin + timedelta(days=8)
    start, end = derive_target_window(overlapping_origin)
    invalid_folds = list(APPROVED_FOLDS)
    invalid_folds[1] = TemporalValidationFold(2, overlapping_origin, start, end)
    with pytest.raises(ValueError, match="must not overlap"):
        validate_fold_contract(invalid_folds)


def test_holdout_overlap_is_rejected() -> None:
    overlapping_origin = date(2017, 7, 20)
    start, end = derive_target_window(overlapping_origin)
    invalid_folds = list(APPROVED_FOLDS)
    invalid_folds[-1] = TemporalValidationFold(4, overlapping_origin, start, end)
    with pytest.raises(ValueError, match="before the final holdout"):
        validate_fold_contract(invalid_folds)


def test_exact_forecast_horizon_set_is_required() -> None:
    assert FORECAST_HORIZONS == tuple(range(1, 17))
    validate_forecast_horizons(FORECAST_HORIZONS)
    with pytest.raises(ValueError, match="exactly"):
        validate_forecast_horizons(tuple(range(1, 16)))


def test_forecast_date_must_match_direct_horizon_equation() -> None:
    origin = date(2017, 6, 30)
    validate_forecast_date_horizon(origin, date(2017, 7, 14), 14)
    with pytest.raises(ValueError, match="must equal"):
        validate_forecast_date_horizon(origin, date(2017, 7, 15), 14)


def test_holdout_contract_rejects_wrong_origin() -> None:
    invalid_holdout = HoldoutWindow(
        forecast_origin=date(2017, 7, 29),
        holdout_start=date(2017, 7, 30),
        holdout_end=date(2017, 8, 14),
    )
    with pytest.raises(ValueError, match="2017-07-30"):
        validate_holdout_contract(invalid_holdout)


def test_canonical_contract_validation_succeeds() -> None:
    validate_approved_contract()
