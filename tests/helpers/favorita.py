"""Reusable tiny Favorita model inputs for focused tests."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from pipelines.evaluation.favorita_backtesting import BacktestExample
from pipelines.features.favorita_model_ready import MODEL_FEATURE_COLUMNS
from pipelines.models.favorita_lightgbm import FavoritaLightGBMAdapter

FROZEN_MODEL_PARAMETERS = {
    "learning_rate": 0.02757359293934948,
    "num_leaves": 123,
    "min_data_in_leaf": 89,
    "feature_fraction": 0.8394633936788146,
}


def _feature_values(index: int, null_column: str | None = None) -> dict[str, object]:
    values: dict[str, object] = {
        name: float(index % 7)
        for name in MODEL_FEATURE_COLUMNS
        if name not in {"store_nbr", "item_nbr"}
    }
    values.update(
        {
            "family": "GROCERY I" if index % 2 else "BEVERAGES",
            "class": 1001,
            "perishable": index % 2,
            "city": "Quito",
            "state": "Pichincha",
            "store_type": "D",
            "cluster": 13,
            "is_weekend": False,
            "onpromotion": True,
            "is_holiday": False,
            "holiday_type": "Holiday",
            "holiday_locale": "National",
            "holiday_transferred": False,
        }
    )
    if null_column:
        values[null_column] = None
    return values


def fit_tiny_favorita_adapter() -> FavoritaLightGBMAdapter:
    """Fit a tiny synthetic adapter without full Favorita execution."""

    origin = date(2016, 1, 1)
    rows = tuple(
        BacktestExample(
            origin,
            origin + timedelta(days=1),
            1,
            1 + index % 3,
            1000 + index,
            float(index),
            index % 2,
            _feature_values(index, "oil_rolling_volatility_7d"),
        )
        for index in range(32)
    )
    adapter = FavoritaLightGBMAdapter(model_parameters=FROZEN_MODEL_PARAMETERS)
    adapter.fit(rows)
    return adapter


def tiny_favorita_feature_frame(
    adapter: FavoritaLightGBMAdapter,
) -> pd.DataFrame:
    """Return three ordered model-ready rows for a tiny fitted adapter."""

    records = []
    for index in range(3):
        values = _feature_values(index, "oil_rolling_volatility_7d")
        values.update(
            {
                "forecast_horizon": 1,
                "store_nbr": 1 + index,
                "item_nbr": 1000 + index,
            }
        )
        records.append(values)
    return pd.DataFrame.from_records(records).loc[:, adapter.fitted_feature_columns]
