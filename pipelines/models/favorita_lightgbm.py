"""Fold-local LightGBM adapter for Favorita direct-horizon forecasting."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from numbers import Integral
from types import MappingProxyType

import lightgbm as lgb
import pandas as pd

from pipelines.evaluation.favorita_backtesting import (
    BacktestExample,
    ForecastModelInput,
    ForecastPrediction,
)
from pipelines.evaluation.favorita_temporal_validation import FORECAST_HORIZONS
from pipelines.features.favorita_model_ready import (
    FORBIDDEN_MODEL_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    TARGET_COLUMN,
)

DEFAULT_FEATURE_COLUMNS: tuple[str, ...] = (
    "forecast_horizon",
    *MODEL_FEATURE_COLUMNS,
)
CATEGORICAL_FEATURE_CANDIDATES: tuple[str, ...] = (
    "store_nbr",
    "item_nbr",
    "family",
    "class",
    "city",
    "state",
    "store_type",
    "cluster",
    "holiday_type",
    "holiday_locale",
)
LIGHTGBM_PARAMETERS: Mapping[str, object] = MappingProxyType(
    {
        "objective": "regression",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_data_in_leaf": 20,
        "feature_fraction": 0.9,
        "seed": 42,
        "num_threads": 4,
        "verbosity": -1,
        "deterministic": True,
        "force_col_wise": True,
    }
)
NUM_BOOST_ROUND = 150

_STRUCTURAL_FEATURES = frozenset({"forecast_horizon", "store_nbr", "item_nbr"})
_EXPECTED_MAPPING_FEATURES = frozenset(MODEL_FEATURE_COLUMNS) - {
    "store_nbr",
    "item_nbr",
}


def _validate_feature_contract(feature_columns: Sequence[str]) -> tuple[str, ...]:
    columns = tuple(feature_columns)
    if not columns:
        raise ValueError("feature_columns must not be empty")
    if len(columns) != len(set(columns)):
        raise ValueError("feature_columns contains duplicate feature names")
    if columns != DEFAULT_FEATURE_COLUMNS:
        raise ValueError(
            "feature_columns must match the ordered Favorita model feature contract"
        )
    return columns


def _validate_feature_mapping(features: Mapping[str, object]) -> None:
    feature_names = frozenset(features)
    forbidden = feature_names & (FORBIDDEN_MODEL_COLUMNS | {TARGET_COLUMN})
    if forbidden:
        names = ", ".join(sorted(forbidden))
        raise ValueError(f"Model input contains forbidden columns: {names}")
    missing = _EXPECTED_MAPPING_FEATURES - feature_names
    unexpected = feature_names - _EXPECTED_MAPPING_FEATURES
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append(f"missing={','.join(sorted(missing))}")
        if unexpected:
            details.append(f"unexpected={','.join(sorted(unexpected))}")
        raise ValueError("Inconsistent model feature schema: " + "; ".join(details))


def _row_values(
    row: BacktestExample | ForecastModelInput,
    feature_columns: Sequence[str],
) -> dict[str, object]:
    if (
        isinstance(row.forecast_horizon, bool)
        or not isinstance(row.forecast_horizon, Integral)
        or row.forecast_horizon not in FORECAST_HORIZONS
    ):
        raise ValueError("forecast_horizon must be an integer from 1 through 16")
    _validate_feature_mapping(row.features)
    if isinstance(row, BacktestExample):
        if row.features["perishable"] != row.perishable:
            raise ValueError(
                "Training feature perishable must match BacktestExample.perishable"
            )
    structural = {
        "forecast_horizon": row.forecast_horizon,
        "store_nbr": row.store_nbr,
        "item_nbr": row.item_nbr,
    }
    return {
        name: structural[name] if name in _STRUCTURAL_FEATURES else row.features[name]
        for name in feature_columns
    }


def _ordered_categories(series: pd.Series) -> tuple[object, ...]:
    values = series.dropna().unique().tolist()
    return tuple(sorted(values, key=lambda value: (type(value).__name__, repr(value))))


class FavoritaLightGBMAdapter:
    """One independently fitted global LightGBM model for one validation fold."""

    def __init__(
        self,
        *,
        feature_columns: Sequence[str] = DEFAULT_FEATURE_COLUMNS,
    ) -> None:
        self._candidate_feature_columns = _validate_feature_contract(feature_columns)
        self._booster: lgb.Booster | None = None
        self._fitted_feature_columns: tuple[str, ...] = ()
        self._excluded_all_null_features: tuple[str, ...] = ()
        self._categorical_feature_columns: tuple[str, ...] = ()
        self._categorical_levels: Mapping[str, tuple[object, ...]] = MappingProxyType(
            {}
        )
        self._training_missing_counts: Mapping[str, int] = MappingProxyType({})

    @property
    def is_fitted(self) -> bool:
        return self._booster is not None

    @property
    def fitted_feature_columns(self) -> tuple[str, ...]:
        return self._fitted_feature_columns

    @property
    def excluded_all_null_features(self) -> tuple[str, ...]:
        return self._excluded_all_null_features

    @property
    def categorical_feature_columns(self) -> tuple[str, ...]:
        return self._categorical_feature_columns

    @property
    def categorical_levels(self) -> Mapping[str, tuple[object, ...]]:
        return self._categorical_levels

    @property
    def training_missing_counts(self) -> Mapping[str, int]:
        return self._training_missing_counts

    @property
    def model_parameters(self) -> Mapping[str, object]:
        return LIGHTGBM_PARAMETERS

    @property
    def num_boost_round(self) -> int:
        return NUM_BOOST_ROUND

    def _materialize_frame(
        self,
        rows: Sequence[BacktestExample | ForecastModelInput],
    ) -> pd.DataFrame:
        return pd.DataFrame.from_records(
            [_row_values(row, self._candidate_feature_columns) for row in rows],
            columns=self._candidate_feature_columns,
        )

    @staticmethod
    def _coerce_numeric(frame: pd.DataFrame, categorical: set[str]) -> None:
        for column in frame.columns:
            if column not in categorical:
                frame[column] = pd.to_numeric(frame[column], errors="raise")
                if pd.api.types.is_bool_dtype(frame[column].dtype):
                    frame[column] = frame[column].astype(float)

    def fit(self, training_rows: Sequence[BacktestExample]) -> None:
        if self.is_fitted:
            raise RuntimeError("FavoritaLightGBMAdapter instances cannot be refitted")
        rows = tuple(training_rows)
        if not rows:
            raise ValueError("training_rows must not be empty")
        if not all(isinstance(row, BacktestExample) for row in rows):
            raise TypeError("training_rows must contain only BacktestExample rows")

        frame = self._materialize_frame(rows)
        excluded = tuple(
            column for column in frame.columns if frame[column].isna().all()
        )
        fitted = tuple(
            column
            for column in self._candidate_feature_columns
            if column not in excluded
        )
        if not fitted:
            raise ValueError("No usable training features remain after null inspection")
        frame = frame.loc[:, fitted].copy()

        categorical = tuple(
            column for column in CATEGORICAL_FEATURE_CANDIDATES if column in fitted
        )
        levels = {column: _ordered_categories(frame[column]) for column in categorical}
        for column in categorical:
            frame[column] = pd.Categorical(frame[column], categories=levels[column])
        self._coerce_numeric(frame, set(categorical))

        targets = pd.Series(
            [row.unit_sales for row in rows], dtype="float64", name=TARGET_COLUMN
        )
        if not all(isfinite(value) for value in targets):
            raise ValueError("Training targets must be finite")

        dataset = lgb.Dataset(
            frame,
            label=targets,
            feature_name=list(fitted),
            categorical_feature=list(categorical),
            free_raw_data=True,
        )
        booster = lgb.train(
            dict(LIGHTGBM_PARAMETERS),
            dataset,
            num_boost_round=NUM_BOOST_ROUND,
        )

        self._booster = booster
        self._fitted_feature_columns = fitted
        self._excluded_all_null_features = excluded
        self._categorical_feature_columns = categorical
        self._categorical_levels = MappingProxyType(levels)
        self._training_missing_counts = MappingProxyType(
            {column: int(frame[column].isna().sum()) for column in fitted}
        )

    def predict(
        self,
        validation_rows: Sequence[ForecastModelInput],
    ) -> tuple[ForecastPrediction, ...]:
        if self._booster is None:
            raise RuntimeError(
                "FavoritaLightGBMAdapter must be fitted before prediction"
            )
        rows = tuple(validation_rows)
        if not rows:
            raise ValueError("validation_rows must not be empty")
        if not all(isinstance(row, ForecastModelInput) for row in rows):
            raise TypeError(
                "validation_rows must contain only target-free ForecastModelInput rows"
            )

        frame = self._materialize_frame(rows)
        frame = frame.loc[:, self._fitted_feature_columns].copy()
        categorical = set(self._categorical_feature_columns)
        for column in self._categorical_feature_columns:
            levels = self._categorical_levels[column]
            values = frame[column]
            known_or_missing = values.isna() | values.isin(levels)
            frame[column] = pd.Categorical(
                values.where(known_or_missing), categories=levels
            )
        self._coerce_numeric(frame, categorical)

        values = self._booster.predict(frame)
        if len(values) != len(rows):
            raise ValueError("LightGBM returned an unexpected prediction count")
        if not all(isfinite(float(value)) for value in values):
            raise ValueError("LightGBM returned a non-finite prediction")

        return tuple(
            ForecastPrediction(
                forecast_origin=row.forecast_origin,
                forecast_date=row.forecast_date,
                forecast_horizon=row.forecast_horizon,
                store_nbr=row.store_nbr,
                item_nbr=row.item_nbr,
                prediction=float(value),
            )
            for row, value in zip(rows, values, strict=True)
        )
