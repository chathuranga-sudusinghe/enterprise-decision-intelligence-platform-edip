"""Deterministic SCRUM-15 temporal-validation contract for Favorita.

This module defines date boundaries and validates them. It intentionally does
not fit models, calculate metrics, or orchestrate multi-fold backtests.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

FORECAST_HORIZONS: tuple[int, ...] = tuple(range(1, 17))
VALIDATION_WINDOW_DAYS = len(FORECAST_HORIZONS)
EXPECTED_FOLD_COUNT = 4
MODELING_TARGET_START = date(2016, 1, 1)


@dataclass(frozen=True, slots=True)
class TemporalValidationFold:
    """One immutable expanding-window validation boundary."""

    fold_id: int
    forecast_origin: date
    validation_start: date
    validation_end: date


@dataclass(frozen=True, slots=True)
class HoldoutWindow:
    """Immutable protected final holdout boundary."""

    forecast_origin: date
    holdout_start: date
    holdout_end: date


def derive_target_window(forecast_origin: date) -> tuple[date, date]:
    """Return the inclusive t+1 through t+16 target-date window."""

    return (
        forecast_origin + timedelta(days=min(FORECAST_HORIZONS)),
        forecast_origin + timedelta(days=max(FORECAST_HORIZONS)),
    )


def _fold(fold_id: int, forecast_origin: date) -> TemporalValidationFold:
    validation_start, validation_end = derive_target_window(forecast_origin)
    return TemporalValidationFold(
        fold_id=fold_id,
        forecast_origin=forecast_origin,
        validation_start=validation_start,
        validation_end=validation_end,
    )


APPROVED_FOLD_ORIGINS: tuple[date, ...] = (
    date(2016, 6, 30),
    date(2016, 12, 31),
    date(2017, 4, 30),
    date(2017, 7, 14),
)

APPROVED_FOLDS: tuple[TemporalValidationFold, ...] = tuple(
    _fold(fold_id, forecast_origin)
    for fold_id, forecast_origin in enumerate(APPROVED_FOLD_ORIGINS, start=1)
)

FINAL_HOLDOUT_ORIGIN = date(2017, 7, 30)
_FINAL_HOLDOUT_START, _FINAL_HOLDOUT_END = derive_target_window(FINAL_HOLDOUT_ORIGIN)
FINAL_HOLDOUT = HoldoutWindow(
    forecast_origin=FINAL_HOLDOUT_ORIGIN,
    holdout_start=_FINAL_HOLDOUT_START,
    holdout_end=_FINAL_HOLDOUT_END,
)


def is_training_target_eligible(
    forecast_date: date,
    fold_origin: date,
) -> bool:
    """Return whether a labelled example is in the simulated training past."""

    return forecast_date <= fold_origin


def require_training_target_eligible(
    forecast_date: date,
    fold_origin: date,
) -> None:
    """Reject a training target whose label occurs after the fold origin."""

    if not is_training_target_eligible(forecast_date, fold_origin):
        raise ValueError("Training forecast_date must be on or before the fold origin")


def validate_forecast_horizons(
    horizons: Sequence[int] = FORECAST_HORIZONS,
) -> None:
    """Require the exact ordered integer horizon contract 1 through 16."""

    if tuple(horizons) != FORECAST_HORIZONS:
        raise ValueError("Forecast horizons must be exactly integers 1 through 16")


def validate_forecast_date_horizon(
    forecast_origin: date,
    forecast_date: date,
    forecast_horizon: int,
) -> None:
    """Validate one direct-horizon date equation against the locked contract."""

    if isinstance(forecast_horizon, bool) or forecast_horizon not in FORECAST_HORIZONS:
        raise ValueError("forecast_horizon must be an integer from 1 through 16")
    expected_date = forecast_origin + timedelta(days=forecast_horizon)
    if forecast_date != expected_date:
        raise ValueError(
            "forecast_date must equal forecast_origin + forecast_horizon days"
        )


def _inclusive_duration(start: date, end: date) -> int:
    return (end - start).days + 1


def validate_holdout_contract(
    holdout: HoldoutWindow = FINAL_HOLDOUT,
) -> None:
    """Validate the exact protected 16-day final holdout."""

    if holdout.forecast_origin != FINAL_HOLDOUT_ORIGIN:
        raise ValueError("Final holdout origin must be 2017-07-30")
    expected_start, expected_end = derive_target_window(holdout.forecast_origin)
    if holdout.holdout_start != expected_start:
        raise ValueError("Final holdout must start one day after its origin")
    if holdout.holdout_end != expected_end:
        raise ValueError("Final holdout must end 16 days after its origin")
    if _inclusive_duration(holdout.holdout_start, holdout.holdout_end) != 16:
        raise ValueError("Final holdout must contain exactly 16 calendar dates")


def validate_fold_contract(
    folds: Sequence[TemporalValidationFold] = APPROVED_FOLDS,
    holdout: HoldoutWindow = FINAL_HOLDOUT,
) -> None:
    """Validate fold count, chronology, windows, and holdout separation."""

    validate_forecast_horizons()
    validate_holdout_contract(holdout)

    if len(folds) != EXPECTED_FOLD_COUNT:
        raise ValueError("The SCRUM-15 contract requires exactly 4 folds")
    if tuple(fold.fold_id for fold in folds) != tuple(range(1, 5)):
        raise ValueError("Fold identifiers must be the ordered integers 1 through 4")

    origins = tuple(fold.forecast_origin for fold in folds)
    if any(current >= following for current, following in zip(origins, origins[1:])):
        raise ValueError("Fold origins must be strictly increasing")

    for fold in folds:
        expected_start, expected_end = derive_target_window(fold.forecast_origin)
        if fold.validation_start != expected_start:
            raise ValueError(
                f"Fold {fold.fold_id} validation_start must equal origin + 1 day"
            )
        if fold.validation_end != expected_end:
            raise ValueError(
                f"Fold {fold.fold_id} validation_end must equal origin + 16 days"
            )
        if _inclusive_duration(fold.validation_start, fold.validation_end) != 16:
            raise ValueError(
                f"Fold {fold.fold_id} must contain exactly 16 calendar dates"
            )

    for current, following in zip(folds, folds[1:]):
        if current.validation_end >= following.validation_start:
            raise ValueError("Validation windows must not overlap")

    if any(fold.validation_end >= holdout.holdout_start for fold in folds):
        raise ValueError("Validation windows must end before the final holdout")


def validate_approved_contract() -> None:
    """Validate the canonical approved folds and protected final holdout."""

    if tuple(fold.forecast_origin for fold in APPROVED_FOLDS) != APPROVED_FOLD_ORIGINS:
        raise ValueError("Approved folds do not match the canonical origins")
    validate_fold_contract(APPROVED_FOLDS, FINAL_HOLDOUT)


validate_approved_contract()
