from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

FORECAST_HORIZONS: tuple[int, ...] = tuple(range(1, 15))
SALES_LAG_OFFSETS: dict[str, int] = {
    "sales_lag_1": 1,
    "sales_lag_7": 7,
    "sales_lag_14": 14,
    "sales_lag_28": 28,
}
SALES_MEAN_WINDOWS: tuple[int, ...] = (7, 14, 28)
SALES_STD_WINDOWS: tuple[int, ...] = (7, 28)

AUDIT_COLUMNS: tuple[str, ...] = (
    "forecast_origin",
    "forecast_date",
    "forecast_horizon",
)
STATIC_COLUMNS: tuple[str, ...] = (
    "store_nbr",
    "item_nbr",
    "family",
    "class",
    "perishable",
    "city",
    "state",
    "store_type",
    "cluster",
)
TARGET_COLUMN = "unit_sales"
SALES_FEATURE_COLUMNS: tuple[str, ...] = (
    "sales_lag_1",
    "sales_lag_7",
    "sales_lag_14",
    "sales_lag_28",
    "sales_rolling_mean_7",
    "sales_rolling_mean_14",
    "sales_rolling_mean_28",
    "sales_rolling_std_7",
    "sales_rolling_std_28",
)
CALENDAR_COLUMNS: tuple[str, ...] = (
    "day_of_week",
    "day_of_month",
    "week_of_year",
    "month",
    "quarter",
    "is_weekend",
)
PROMOTION_COLUMNS: tuple[str, ...] = ("onpromotion",)
TRANSACTION_FEATURE_COLUMNS: tuple[str, ...] = (
    "transactions_at_origin",
    "transactions_mean_7d",
    "transactions_mean_14d",
    "transactions_lag_7",
    "transactions_lag_14",
)
OIL_FEATURE_COLUMNS: tuple[str, ...] = (
    "oil_pct_change_1d",
    "oil_pct_change_7d",
    "oil_rolling_change_7d",
    "oil_rolling_volatility_7d",
)
HOLIDAY_FEATURE_COLUMNS: tuple[str, ...] = (
    "is_holiday",
    "holiday_type",
    "holiday_locale",
    "holiday_transferred",
    "holiday_event_count",
)

MODEL_FEATURE_COLUMNS: tuple[str, ...] = (
    *STATIC_COLUMNS,
    *SALES_FEATURE_COLUMNS,
    *CALENDAR_COLUMNS,
    *PROMOTION_COLUMNS,
    *TRANSACTION_FEATURE_COLUMNS,
    *OIL_FEATURE_COLUMNS,
    *HOLIDAY_FEATURE_COLUMNS,
)
TRAINING_OUTPUT_COLUMNS: tuple[str, ...] = (
    *AUDIT_COLUMNS,
    *STATIC_COLUMNS,
    TARGET_COLUMN,
    *SALES_FEATURE_COLUMNS,
    *CALENDAR_COLUMNS,
    *PROMOTION_COLUMNS,
    *TRANSACTION_FEATURE_COLUMNS,
    *OIL_FEATURE_COLUMNS,
    *HOLIDAY_FEATURE_COLUMNS,
)
INFERENCE_OUTPUT_COLUMNS: tuple[str, ...] = (
    *AUDIT_COLUMNS,
    *MODEL_FEATURE_COLUMNS,
)

FORBIDDEN_MODEL_COLUMNS: frozenset[str] = frozenset(
    {
        "id",
        "unit_sales",
        "transactions",
        "dcoilwtico",
        "holiday_description",
        "is_earthquake",
        "earthquake_flag",
        "days_since_earthquake",
    }
)

SOURCE_READ_COLUMNS: tuple[str, ...] = (
    "date",
    "store_nbr",
    "item_nbr",
    "unit_sales",
    "onpromotion",
    "family",
    "class",
    "perishable",
    "city",
    "state",
    "store_type",
    "cluster",
    "transactions",
    "dcoilwtico",
    "is_holiday",
    "holiday_type",
    "holiday_locale",
    "holiday_description",
    "holiday_transferred",
    "holiday_event_count",
)

OUTPUT_ARROW_SCHEMA = pa.schema(
    [
        pa.field("forecast_origin", pa.timestamp("us"), nullable=False),
        pa.field("forecast_date", pa.timestamp("us"), nullable=False),
        pa.field("forecast_horizon", pa.int8(), nullable=False),
        pa.field("store_nbr", pa.int16(), nullable=False),
        pa.field("item_nbr", pa.int32(), nullable=False),
        pa.field("family", pa.large_string(), nullable=False),
        pa.field("class", pa.int16(), nullable=False),
        pa.field("perishable", pa.int8(), nullable=False),
        pa.field("city", pa.large_string(), nullable=False),
        pa.field("state", pa.large_string(), nullable=False),
        pa.field("store_type", pa.large_string(), nullable=False),
        pa.field("cluster", pa.int8(), nullable=False),
        pa.field("unit_sales", pa.float64(), nullable=False),
        *[
            pa.field(name, pa.float64(), nullable=True)
            for name in SALES_FEATURE_COLUMNS
        ],
        pa.field("day_of_week", pa.int8(), nullable=False),
        pa.field("day_of_month", pa.int8(), nullable=False),
        pa.field("week_of_year", pa.int8(), nullable=False),
        pa.field("month", pa.int8(), nullable=False),
        pa.field("quarter", pa.int8(), nullable=False),
        pa.field("is_weekend", pa.bool_(), nullable=False),
        pa.field("onpromotion", pa.bool_(), nullable=True),
        *[
            pa.field(name, pa.float64(), nullable=True)
            for name in TRANSACTION_FEATURE_COLUMNS
        ],
        *[pa.field(name, pa.float64(), nullable=True) for name in OIL_FEATURE_COLUMNS],
        pa.field("is_holiday", pa.bool_(), nullable=True),
        pa.field("holiday_type", pa.large_string(), nullable=True),
        pa.field("holiday_locale", pa.large_string(), nullable=True),
        pa.field("holiday_transferred", pa.bool_(), nullable=True),
        pa.field("holiday_event_count", pa.int16(), nullable=True),
    ]
)

SEMANTIC_TYPES: dict[str, str] = {
    "forecast_origin": "audit timestamp: end-of-day origin t",
    "forecast_date": "audit timestamp: target date t+h",
    "forecast_horizon": "bounded integer horizon 1..14",
    "store_nbr": "categorical identifier (physical int16 code retained)",
    "item_nbr": "categorical identifier (physical int32 code retained)",
    "family": "categorical",
    "class": "categorical (physical int16 code retained)",
    "perishable": "binary",
    "city": "categorical",
    "state": "categorical",
    "store_type": "categorical",
    "cluster": "categorical identifier (physical int8 code retained)",
    "unit_sales": "numeric supervised target; excluded from inference matrix",
    **{
        name: "nullable numeric origin-bounded historical sales feature"
        for name in SALES_FEATURE_COLUMNS
    },
    "day_of_week": "ISO weekday index, Monday=0 through Sunday=6",
    "day_of_month": "calendar integer",
    "week_of_year": "ISO-8601 week number",
    "month": "calendar integer",
    "quarter": "calendar integer",
    "is_weekend": "Boolean: Saturday or Sunday",
    "onpromotion": "nullable future-known Boolean; unknown unless planned-at-origin assumption enabled",
    **{
        name: "nullable numeric origin-bounded store transaction feature"
        for name in TRANSACTION_FEATURE_COLUMNS
    },
    **{
        name: "nullable numeric origin-bounded oil movement feature"
        for name in OIL_FEATURE_COLUMNS
    },
    "is_holiday": "nullable future-known Boolean with broader merged lineage",
    "holiday_type": "nullable future-known categorical",
    "holiday_locale": "nullable future-known categorical",
    "holiday_transferred": "nullable future-known Boolean",
    "holiday_event_count": "nullable future-known numeric count",
}

FEATURE_DEFINITIONS: dict[str, str] = {
    "sales_lag_1": "unit_sales on exact calendar date t-1",
    "sales_lag_7": "unit_sales on exact calendar date t-7",
    "sales_lag_14": "unit_sales on exact calendar date t-14",
    "sales_lag_28": "unit_sales on exact calendar date t-28",
    "sales_rolling_mean_7": "mean over complete observed calendar window [t-7,t-1]; null unless all 7 dates exist",
    "sales_rolling_mean_14": "mean over complete observed calendar window [t-14,t-1]; null unless all 14 dates exist",
    "sales_rolling_mean_28": "mean over complete observed calendar window [t-28,t-1]; null unless all 28 dates exist",
    "sales_rolling_std_7": "sample std (ddof=1) over complete observed calendar window [t-7,t-1]",
    "sales_rolling_std_28": "sample std (ddof=1) over complete observed calendar window [t-28,t-1]",
    "transactions_at_origin": "store transactions on exact calendar date t",
    "transactions_mean_7d": "mean over complete non-null store-date window [t-6,t]; otherwise null",
    "transactions_mean_14d": "mean over complete non-null store-date window [t-13,t]; otherwise null",
    "transactions_lag_7": "store transactions on exact calendar date t-7",
    "transactions_lag_14": "store transactions on exact calendar date t-14",
    "oil_pct_change_1d": "P(t)/P(t-1)-1 using exact non-null dates; null for missing/zero denominator",
    "oil_pct_change_7d": "P(t)/P(t-7)-1 using exact non-null dates; null for missing/zero denominator",
    "oil_rolling_change_7d": "last/first-1 across >=2 observed prices in [t-6,t]; no fill; null for zero denominator",
    "oil_rolling_volatility_7d": "sample std (ddof=1) of consecutive observed-price returns in [t-6,t]; >=3 prices required",
}


@dataclass(frozen=True)
class FeatureBuildConfig:
    source_path: Path
    output_path: Path
    manifest_path: Path
    forecast_origins: tuple[date, ...]
    store_batches: tuple[tuple[int, ...], ...]
    max_items_per_store: int | None = None
    allow_assumed_future_promotion: bool = False
    allow_assumed_future_holidays: bool = False
    overwrite: bool = False


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while chunk := file_handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def source_footer(path: Path) -> dict[str, Any]:
    parquet_file = pq.ParquetFile(path)
    return {
        "path": path.as_posix(),
        "rows": parquet_file.metadata.num_rows,
        "columns": len(parquet_file.schema_arrow),
        "row_groups": parquet_file.metadata.num_row_groups,
        "schema": {field.name: str(field.type) for field in parquet_file.schema_arrow},
    }


def validate_build_config(config: FeatureBuildConfig) -> None:
    if not config.source_path.is_file():
        raise FileNotFoundError(config.source_path)
    if not config.forecast_origins:
        raise ValueError("At least one explicit forecast origin is required")
    if tuple(sorted(set(config.forecast_origins))) != config.forecast_origins:
        raise ValueError("Forecast origins must be unique and sorted")
    if not config.store_batches or any(not batch for batch in config.store_batches):
        raise ValueError("At least one non-empty store batch is required")
    flattened_stores = [store for batch in config.store_batches for store in batch]
    if len(flattened_stores) != len(set(flattened_stores)):
        raise ValueError("A store may appear in only one configured batch")
    if config.max_items_per_store is not None and config.max_items_per_store <= 0:
        raise ValueError("max_items_per_store must be positive or None")
    if config.source_path.resolve() in {
        config.output_path.resolve(),
        config.manifest_path.resolve(),
    }:
        raise ValueError("Source, output, and manifest paths must be distinct")


def _read_filtered_source_slice(
    source_path: Path,
    *,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    store_nbrs: Sequence[int],
) -> pd.DataFrame:
    dataset = ds.dataset(source_path, format="parquet")
    filter_expression = (
        (ds.field("date") >= start_date.to_pydatetime())
        & (ds.field("date") <= end_date.to_pydatetime())
        & ds.field("store_nbr").isin(list(store_nbrs))
    )
    table = dataset.scanner(
        columns=list(SOURCE_READ_COLUMNS),
        filter=filter_expression,
        batch_size=131_072,
        use_threads=True,
    ).to_table()
    frame = table.to_pandas()
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.sort_values(["date", "store_nbr", "item_nbr"]).reset_index(drop=True)


def _select_bounded_items(
    source_slice: pd.DataFrame,
    *,
    origin: pd.Timestamp,
    max_items_per_store: int | None,
) -> pd.DataFrame:
    if max_items_per_store is None:
        return source_slice
    forecast_end = origin + pd.Timedelta(days=max(FORECAST_HORIZONS))
    target_period = source_slice.loc[
        source_slice["date"].between(origin + pd.Timedelta(days=1), forecast_end),
        ["store_nbr", "item_nbr"],
    ].drop_duplicates()
    selected = (
        target_period.sort_values(["store_nbr", "item_nbr"])
        .groupby("store_nbr", sort=True, group_keys=False)
        .head(max_items_per_store)
    )
    return source_slice.merge(selected, on=["store_nbr", "item_nbr"], how="inner")


def _validate_slice_grain(source_slice: pd.DataFrame) -> None:
    duplicate_count = int(
        source_slice.duplicated(["date", "store_nbr", "item_nbr"]).sum()
    )
    if duplicate_count:
        raise ValueError(f"Source slice has {duplicate_count} duplicate grain rows")


def _origin_static_frame(
    history: pd.DataFrame,
    target_series: pd.DataFrame,
) -> pd.DataFrame:
    static_attributes = list(STATIC_COLUMNS[2:])
    latest_origin_rows = (
        history.sort_values(["store_nbr", "item_nbr", "date"])
        .drop_duplicates(["store_nbr", "item_nbr"], keep="last")
        .loc[:, ["store_nbr", "item_nbr", *static_attributes]]
    )
    origin_static = target_series.merge(
        latest_origin_rows,
        on=["store_nbr", "item_nbr"],
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    missing_series = origin_static["_merge"] != "both"
    if missing_series.any():
        missing_count = int(missing_series.sum())
        raise ValueError(
            f"{missing_count} target series have no static attributes available at the origin"
        )
    origin_static = origin_static.drop(columns="_merge")
    if origin_static[static_attributes].isna().any().any():
        raise ValueError("Origin-time static attributes contain unexpected nulls")
    return origin_static


def _series_feature_frame(
    history: pd.DataFrame,
    target_series: pd.DataFrame,
    origin: pd.Timestamp,
) -> pd.DataFrame:
    features = target_series.copy()
    for feature_name, offset_days in SALES_LAG_OFFSETS.items():
        lookup_date = origin - pd.Timedelta(days=offset_days)
        lookup = history.loc[
            history["date"] == lookup_date,
            ["store_nbr", "item_nbr", "unit_sales"],
        ].rename(columns={"unit_sales": feature_name})
        features = features.merge(lookup, on=["store_nbr", "item_nbr"], how="left")

    for window in SALES_MEAN_WINDOWS:
        window_start = origin - pd.Timedelta(days=window)
        window_end = origin - pd.Timedelta(days=1)
        window_data = history.loc[history["date"].between(window_start, window_end)]
        grouped = window_data.groupby(["store_nbr", "item_nbr"])["unit_sales"]
        aggregates = grouped.agg(observations="size", non_null="count", value="mean")
        valid = (aggregates["observations"] == window) & (
            aggregates["non_null"] == window
        )
        feature_name = f"sales_rolling_mean_{window}"
        aggregates[feature_name] = aggregates["value"].where(valid)
        features = features.merge(
            aggregates[[feature_name]].reset_index(),
            on=["store_nbr", "item_nbr"],
            how="left",
        )

    for window in SALES_STD_WINDOWS:
        window_start = origin - pd.Timedelta(days=window)
        window_end = origin - pd.Timedelta(days=1)
        window_data = history.loc[history["date"].between(window_start, window_end)]
        grouped = window_data.groupby(["store_nbr", "item_nbr"])["unit_sales"]
        aggregates = grouped.agg(
            observations="size",
            non_null="count",
            value=lambda values: values.std(ddof=1),
        )
        valid = (aggregates["observations"] == window) & (
            aggregates["non_null"] == window
        )
        feature_name = f"sales_rolling_std_{window}"
        aggregates[feature_name] = aggregates["value"].where(valid)
        features = features.merge(
            aggregates[[feature_name]].reset_index(),
            on=["store_nbr", "item_nbr"],
            how="left",
        )
    return features


def _consistent_store_date_transactions(history: pd.DataFrame) -> pd.DataFrame:
    relevant = history[["date", "store_nbr", "transactions"]]
    consistency = relevant.groupby(["date", "store_nbr"])["transactions"].nunique(
        dropna=False
    )
    if not consistency.empty and int(consistency.max()) > 1:
        raise ValueError("Conflicting transactions values within a store-date")
    return relevant.drop_duplicates(["date", "store_nbr"])


def _transaction_feature_frame(
    history: pd.DataFrame,
    stores: pd.DataFrame,
    origin: pd.Timestamp,
) -> pd.DataFrame:
    store_daily = _consistent_store_date_transactions(history)
    features = stores.copy()
    exact_offsets = {
        "transactions_at_origin": 0,
        "transactions_lag_7": 7,
        "transactions_lag_14": 14,
    }
    for feature_name, offset_days in exact_offsets.items():
        lookup_date = origin - pd.Timedelta(days=offset_days)
        lookup = store_daily.loc[
            store_daily["date"] == lookup_date,
            ["store_nbr", "transactions"],
        ].rename(columns={"transactions": feature_name})
        features = features.merge(lookup, on="store_nbr", how="left")

    for window in (7, 14):
        window_start = origin - pd.Timedelta(days=window - 1)
        window_data = store_daily.loc[store_daily["date"].between(window_start, origin)]
        aggregates = window_data.groupby("store_nbr")["transactions"].agg(
            observations="size", non_null="count", value="mean"
        )
        valid = (aggregates["observations"] == window) & (
            aggregates["non_null"] == window
        )
        feature_name = f"transactions_mean_{window}d"
        aggregates[feature_name] = aggregates["value"].where(valid)
        features = features.merge(
            aggregates[[feature_name]].reset_index(), on="store_nbr", how="left"
        )
    return features


def _consistent_date_oil(history: pd.DataFrame) -> pd.DataFrame:
    relevant = history[["date", "dcoilwtico"]]
    consistency = relevant.groupby("date")["dcoilwtico"].nunique(dropna=False)
    if not consistency.empty and int(consistency.max()) > 1:
        raise ValueError("Conflicting dcoilwtico values within a date")
    return relevant.drop_duplicates("date").sort_values("date")


def _safe_relative_change(numerator: float | None, denominator: float | None) -> float:
    if numerator is None or denominator is None:
        return np.nan
    if pd.isna(numerator) or pd.isna(denominator) or float(denominator) == 0.0:
        return np.nan
    return float(numerator) / float(denominator) - 1.0


def _oil_feature_values(
    history: pd.DataFrame, origin: pd.Timestamp
) -> dict[str, float]:
    oil_daily = _consistent_date_oil(history)
    prices_by_date = oil_daily.set_index("date")["dcoilwtico"]

    def price_on(day: pd.Timestamp) -> float | None:
        if day not in prices_by_date.index:
            return None
        value = prices_by_date.loc[day]
        return None if pd.isna(value) else float(value)

    price_t = price_on(origin)
    price_t_minus_1 = price_on(origin - pd.Timedelta(days=1))
    price_t_minus_7 = price_on(origin - pd.Timedelta(days=7))
    window = oil_daily.loc[
        oil_daily["date"].between(origin - pd.Timedelta(days=6), origin),
        "dcoilwtico",
    ].dropna()
    observed_prices = window.to_numpy(dtype=float)
    rolling_change = np.nan
    rolling_volatility = np.nan
    if len(observed_prices) >= 2 and observed_prices[0] != 0.0:
        rolling_change = observed_prices[-1] / observed_prices[0] - 1.0
    if len(observed_prices) >= 3 and not np.any(observed_prices[:-1] == 0.0):
        returns = observed_prices[1:] / observed_prices[:-1] - 1.0
        rolling_volatility = float(np.std(returns, ddof=1))
    return {
        "oil_pct_change_1d": _safe_relative_change(price_t, price_t_minus_1),
        "oil_pct_change_7d": _safe_relative_change(price_t, price_t_minus_7),
        "oil_rolling_change_7d": rolling_change,
        "oil_rolling_volatility_7d": rolling_volatility,
    }


def _apply_future_known_policy(
    target_rows: pd.DataFrame,
    *,
    allow_assumed_future_promotion: bool,
    allow_assumed_future_holidays: bool,
) -> pd.DataFrame:
    output = target_rows.copy()
    if allow_assumed_future_promotion:
        output["onpromotion"] = output["onpromotion"].astype("boolean")
    else:
        output["onpromotion"] = pd.Series(pd.NA, index=output.index, dtype="boolean")

    earthquake_mask = output["holiday_description"].str.contains(
        r"terremoto|earthquake|manabi", case=False, na=False, regex=True
    )
    if allow_assumed_future_holidays:
        output["is_holiday"] = output["is_holiday"].astype("boolean")
        output["holiday_transferred"] = output["holiday_transferred"].astype("boolean")
        output["holiday_event_count"] = output["holiday_event_count"].astype("Int16")
        for column in HOLIDAY_FEATURE_COLUMNS:
            output.loc[earthquake_mask, column] = pd.NA
    else:
        output["is_holiday"] = pd.Series(pd.NA, index=output.index, dtype="boolean")
        output["holiday_type"] = pd.Series(pd.NA, index=output.index, dtype="string")
        output["holiday_locale"] = pd.Series(pd.NA, index=output.index, dtype="string")
        output["holiday_transferred"] = pd.Series(
            pd.NA, index=output.index, dtype="boolean"
        )
        output["holiday_event_count"] = pd.Series(
            pd.NA, index=output.index, dtype="Int16"
        )
    return output


def _add_calendar_features(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["day_of_week"] = output["forecast_date"].dt.dayofweek
    output["day_of_month"] = output["forecast_date"].dt.day
    output["week_of_year"] = output["forecast_date"].dt.isocalendar().week
    output["month"] = output["forecast_date"].dt.month
    output["quarter"] = output["forecast_date"].dt.quarter
    output["is_weekend"] = output["day_of_week"].isin([5, 6])
    return output


def build_feature_rows_for_origin(
    source_slice: pd.DataFrame,
    *,
    forecast_origin: date | pd.Timestamp,
    max_items_per_store: int | None = None,
    allow_assumed_future_promotion: bool = False,
    allow_assumed_future_holidays: bool = False,
) -> pd.DataFrame:
    origin = pd.Timestamp(forecast_origin).normalize()
    source = source_slice.copy()
    source["date"] = pd.to_datetime(source["date"]).dt.normalize()
    source = _select_bounded_items(
        source,
        origin=origin,
        max_items_per_store=max_items_per_store,
    )
    _validate_slice_grain(source)

    history = source.loc[source["date"] <= origin].copy()
    forecast_end = origin + pd.Timedelta(days=max(FORECAST_HORIZONS))
    target_rows = source.loc[
        source["date"].between(origin + pd.Timedelta(days=1), forecast_end)
    ].copy()
    if target_rows.empty:
        return pd.DataFrame(columns=TRAINING_OUTPUT_COLUMNS)

    target_rows = target_rows.rename(columns={"date": "forecast_date"})
    target_rows["forecast_origin"] = origin
    target_rows["forecast_horizon"] = (target_rows["forecast_date"] - origin).dt.days
    target_rows = _apply_future_known_policy(
        target_rows,
        allow_assumed_future_promotion=allow_assumed_future_promotion,
        allow_assumed_future_holidays=allow_assumed_future_holidays,
    )
    target_rows = _add_calendar_features(target_rows)

    target_series = target_rows[["store_nbr", "item_nbr"]].drop_duplicates()
    origin_static = _origin_static_frame(history, target_series)
    static_attributes = list(STATIC_COLUMNS[2:])
    target_rows = target_rows.drop(columns=static_attributes).merge(
        origin_static,
        on=["store_nbr", "item_nbr"],
        how="left",
        validate="many_to_one",
    )
    series_features = _series_feature_frame(history, target_series, origin)
    store_features = _transaction_feature_frame(
        history,
        target_rows[["store_nbr"]].drop_duplicates(),
        origin,
    )
    oil_features = _oil_feature_values(history, origin)

    output = target_rows.merge(
        series_features, on=["store_nbr", "item_nbr"], how="left"
    ).merge(store_features, on="store_nbr", how="left")
    for column, value in oil_features.items():
        output[column] = value

    output = output.loc[:, list(TRAINING_OUTPUT_COLUMNS)].copy()
    output = output.sort_values(
        ["forecast_origin", "forecast_date", "store_nbr", "item_nbr"]
    ).reset_index(drop=True)
    validate_feature_frame(output)
    return output


def to_arrow_table(frame: pd.DataFrame) -> pa.Table:
    return pa.Table.from_pandas(
        frame.loc[:, list(TRAINING_OUTPUT_COLUMNS)],
        schema=OUTPUT_ARROW_SCHEMA,
        preserve_index=False,
        safe=True,
    )


def validate_feature_frame(frame: pd.DataFrame) -> None:
    if tuple(frame.columns) != TRAINING_OUTPUT_COLUMNS:
        raise AssertionError("Training output column order differs from contract")
    if not frame["forecast_horizon"].isin(FORECAST_HORIZONS).all():
        raise AssertionError("forecast_horizon must be restricted to 1..14")
    expected_dates = frame["forecast_origin"] + pd.to_timedelta(
        frame["forecast_horizon"], unit="D"
    )
    if not (frame["forecast_date"] == expected_dates).all():
        raise AssertionError("forecast_date must equal forecast_origin + horizon")
    duplicate_count = int(
        frame.duplicated(
            ["forecast_origin", "forecast_date", "store_nbr", "item_nbr"]
        ).sum()
    )
    if duplicate_count:
        raise AssertionError(f"Output grain has {duplicate_count} duplicates")
    if FORBIDDEN_MODEL_COLUMNS.intersection(MODEL_FEATURE_COLUMNS):
        raise AssertionError("Forbidden fields entered MODEL_FEATURE_COLUMNS")
    if TARGET_COLUMN in INFERENCE_OUTPUT_COLUMNS:
        raise AssertionError("Target entered inference output columns")
    if tuple(
        column for column in TRAINING_OUTPUT_COLUMNS if column != TARGET_COLUMN
    ) != (INFERENCE_OUTPUT_COLUMNS):
        raise AssertionError("Training/inference ordered schema parity failed")


class AtomicParquetBatchWriter:
    def __init__(self, output_path: Path, *, overwrite: bool) -> None:
        self.output_path = output_path
        self.overwrite = overwrite
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.temp_path = self.output_path.with_name(
            f".{self.output_path.name}.{uuid.uuid4().hex}.tmp"
        )
        self.writer: pq.ParquetWriter | None = None
        self.rows_written = 0

    def write(self, table: pa.Table) -> None:
        if self.writer is None:
            if self.output_path.exists() and not self.overwrite:
                raise FileExistsError(self.output_path)
            self.writer = pq.ParquetWriter(
                self.temp_path,
                OUTPUT_ARROW_SCHEMA,
                compression="zstd",
            )
        self.writer.write_table(table)
        self.rows_written += table.num_rows

    def finalize(self) -> None:
        if self.writer is None or self.rows_written == 0:
            raise RuntimeError("No feature rows were written")
        self.writer.close()
        self.writer = None
        parquet_file = pq.ParquetFile(self.temp_path)
        if parquet_file.metadata.num_rows != self.rows_written:
            raise AssertionError("Temporary Parquet row-count validation failed")
        if not parquet_file.schema_arrow.equals(OUTPUT_ARROW_SCHEMA):
            raise AssertionError("Temporary Parquet schema validation failed")
        os.replace(self.temp_path, self.output_path)

    def abort(self) -> None:
        if self.writer is not None:
            self.writer.close()
            self.writer = None
        self.temp_path.unlink(missing_ok=True)


def validate_feature_artifact(output_path: Path) -> dict[str, Any]:
    parquet_file = pq.ParquetFile(output_path)
    if not parquet_file.schema_arrow.equals(OUTPUT_ARROW_SCHEMA):
        raise AssertionError("Output Arrow schema differs from declared contract")
    null_counts = {name: 0 for name in TRAINING_OUTPUT_COLUMNS}
    row_count = 0
    min_forecast_date: datetime | None = None
    max_forecast_date: datetime | None = None
    stores: set[int] = set()
    items: set[int] = set()
    horizons: set[int] = set()
    duplicate_count = 0
    seen_keys: set[tuple[Any, ...]] = set()
    for row_group_index in range(parquet_file.metadata.num_row_groups):
        table = parquet_file.read_row_group(row_group_index)
        row_count += table.num_rows
        for column in TRAINING_OUTPUT_COLUMNS:
            null_counts[column] += table.column(column).null_count
        frame = table.select(
            [
                "forecast_origin",
                "forecast_date",
                "forecast_horizon",
                "store_nbr",
                "item_nbr",
            ]
        ).to_pandas()
        validate_dates = frame["forecast_origin"] + pd.to_timedelta(
            frame["forecast_horizon"], unit="D"
        )
        if not (frame["forecast_date"] == validate_dates).all():
            raise AssertionError("Artifact horizon/date equation failed")
        if not frame["forecast_horizon"].isin(FORECAST_HORIZONS).all():
            raise AssertionError("Artifact contains an invalid horizon")
        for key in frame[
            ["forecast_origin", "forecast_date", "store_nbr", "item_nbr"]
        ].itertuples(index=False, name=None):
            if key in seen_keys:
                duplicate_count += 1
            seen_keys.add(key)
        stores.update(int(value) for value in frame["store_nbr"].unique())
        items.update(int(value) for value in frame["item_nbr"].unique())
        horizons.update(int(value) for value in frame["forecast_horizon"].unique())
        current_min = frame["forecast_date"].min().to_pydatetime()
        current_max = frame["forecast_date"].max().to_pydatetime()
        min_forecast_date = (
            current_min
            if min_forecast_date is None
            else min(min_forecast_date, current_min)
        )
        max_forecast_date = (
            current_max
            if max_forecast_date is None
            else max(max_forecast_date, current_max)
        )
    if duplicate_count:
        raise AssertionError(f"Artifact has {duplicate_count} duplicate grain rows")
    return {
        "rows": row_count,
        "columns": len(parquet_file.schema_arrow),
        "row_groups": parquet_file.metadata.num_row_groups,
        "forecast_date_min": (
            min_forecast_date.date().isoformat() if min_forecast_date else None
        ),
        "forecast_date_max": (
            max_forecast_date.date().isoformat() if max_forecast_date else None
        ),
        "store_cardinality": len(stores),
        "item_cardinality": len(items),
        "horizons": sorted(horizons),
        "grain_duplicate_count": duplicate_count,
        "null_counts": null_counts,
        "schema": {field.name: str(field.type) for field in parquet_file.schema_arrow},
    }


def materialize_feature_dataset(config: FeatureBuildConfig) -> dict[str, Any]:
    validate_build_config(config)
    writer = AtomicParquetBatchWriter(config.output_path, overwrite=config.overwrite)
    expected_target_rows = 0
    batches_written = 0
    try:
        for origin_date in config.forecast_origins:
            origin = pd.Timestamp(origin_date)
            start_date = origin - pd.Timedelta(days=28)
            end_date = origin + pd.Timedelta(days=max(FORECAST_HORIZONS))
            for store_batch in config.store_batches:
                source_slice = _read_filtered_source_slice(
                    config.source_path,
                    start_date=start_date,
                    end_date=end_date,
                    store_nbrs=store_batch,
                )
                source_slice = _select_bounded_items(
                    source_slice,
                    origin=origin,
                    max_items_per_store=config.max_items_per_store,
                )
                expected_target_rows += int(
                    source_slice["date"]
                    .between(origin + pd.Timedelta(days=1), end_date)
                    .sum()
                )
                feature_rows = build_feature_rows_for_origin(
                    source_slice,
                    forecast_origin=origin,
                    max_items_per_store=None,
                    allow_assumed_future_promotion=config.allow_assumed_future_promotion,
                    allow_assumed_future_holidays=config.allow_assumed_future_holidays,
                )
                if feature_rows.empty:
                    continue
                writer.write(to_arrow_table(feature_rows))
                batches_written += 1
        writer.finalize()
    except Exception:
        writer.abort()
        raise

    artifact_validation = validate_feature_artifact(config.output_path)
    if artifact_validation["rows"] != expected_target_rows:
        raise AssertionError(
            "Output rows differ from observed target rows; synthetic or missing rows detected"
        )
    return {
        "creation_status": "created",
        "batches_written": batches_written,
        "expected_observed_target_rows": expected_target_rows,
        "artifact_validation": artifact_validation,
    }


def build_feature_manifest(
    *,
    config: FeatureBuildConfig,
    source_metadata: dict[str, Any],
    source_sha256: str,
    build_result: dict[str, Any],
    validation_results: dict[str, bool],
    creation_scope: str,
    limitations: Sequence[str],
) -> dict[str, Any]:
    return {
        "artifact": {
            "artifact_type": "Parquet",
            "output_path": config.output_path.as_posix(),
            "manifest_path": config.manifest_path.as_posix(),
            "creation_status": build_result["creation_status"],
            "creation_scope": creation_scope,
        },
        "source": {
            **source_metadata,
            "sha256": source_sha256,
            "mutated": False,
        },
        "output": build_result["artifact_validation"],
        "grain": [
            "forecast_origin",
            "forecast_date",
            "store_nbr",
            "item_nbr",
        ],
        "ordered_schema": list(TRAINING_OUTPUT_COLUMNS),
        "arrow_schema": {field.name: str(field.type) for field in OUTPUT_ARROW_SCHEMA},
        "semantic_types": SEMANTIC_TYPES,
        "model_feature_columns": list(MODEL_FEATURE_COLUMNS),
        "inference_output_columns": list(INFERENCE_OUTPUT_COLUMNS),
        "feature_definitions": FEATURE_DEFINITIONS,
        "forecast_configuration": {
            "forecast_origins": [
                value.isoformat() for value in config.forecast_origins
            ],
            "forecast_horizons": list(FORECAST_HORIZONS),
            "forecast_origin_semantics": "end of calendar day t",
            "direct_horizon_aware": True,
            "recursive_feedback": False,
            "store_batches": [list(batch) for batch in config.store_batches],
            "max_items_per_store": config.max_items_per_store,
        },
        "future_known_policy": {
            "promotion_planned_at_origin_assumption_enabled": config.allow_assumed_future_promotion,
            "holiday_published_at_origin_assumption_enabled": config.allow_assumed_future_holidays,
            "unknown_when_assumption_disabled": True,
        },
        "null_behavior": {
            "missing_exact_lag_date": "null",
            "incomplete_sales_calendar_window": "null",
            "incomplete_or_missing_transactions_window": "null",
            "missing_or_zero oil denominator": "null",
            "imputation_performed": False,
        },
        "sparse_data_policy": {
            "full_panel_created": False,
            "synthetic_zero_demand_created": False,
            "only_observed_target_rows_materialized": True,
            "negative_and_fractional_sales_preserved": True,
        },
        "forbidden_feature_assertions": {
            "forbidden_columns": sorted(FORBIDDEN_MODEL_COLUMNS),
            "forbidden_columns_absent": not bool(
                FORBIDDEN_MODEL_COLUMNS.intersection(MODEL_FEATURE_COLUMNS)
            ),
            "raw_dcoilwtico_absent": "dcoilwtico" not in MODEL_FEATURE_COLUMNS,
            "earthquake_features_absent": not any(
                "earthquake" in column for column in MODEL_FEATURE_COLUMNS
            ),
            "target_absent_from_inference": TARGET_COLUMN
            not in INFERENCE_OUTPUT_COLUMNS,
        },
        "processing": {
            "method": "explicit origin and store-batch filtered PyArrow reads with incremental atomic Parquet writing",
            "complete_source_loaded_at_once": False,
            "batches_written": build_result["batches_written"],
            "expected_observed_target_rows": build_result[
                "expected_observed_target_rows"
            ],
        },
        "validation": {key: bool(value) for key, value in validation_results.items()},
        "limitations": list(limitations),
        "reproducibility": {
            "python": os.sys.version.split()[0],
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "pyarrow": pa.__version__,
            "notebook": "notebooks/favorita/08_build_model_ready_feature_dataset.ipynb",
        },
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (date, datetime, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def write_json_atomic(payload: dict[str, Any], path: Path, *, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temp_path.write_text(
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                default=_json_default,
            )
            + "\n",
            encoding="utf-8",
        )
        json.loads(temp_path.read_text(encoding="utf-8"))
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _fixture_source_frame() -> tuple[pd.DataFrame, pd.Timestamp]:
    origin = pd.Timestamp("2020-02-10")
    dates = pd.date_range(
        origin - pd.Timedelta(days=35), origin + pd.Timedelta(days=14)
    )
    rows: list[dict[str, Any]] = []
    for item_nbr in (100, 200):
        for sequence, current_date in enumerate(dates):
            if item_nbr == 200 and current_date == origin - pd.Timedelta(days=7):
                continue
            sales = float(sequence) + (0.5 if item_nbr == 100 else 1.25)
            if item_nbr == 100 and current_date == origin - pd.Timedelta(days=3):
                sales = -2.5
            description = (
                "Terremoto Manabi"
                if current_date == origin + pd.Timedelta(days=3)
                else (
                    "Local Holiday"
                    if current_date == origin + pd.Timedelta(days=5)
                    else None
                )
            )
            rows.append(
                {
                    "date": current_date,
                    "store_nbr": 1,
                    "item_nbr": item_nbr,
                    "unit_sales": sales,
                    "onpromotion": None if sequence % 11 == 0 else sequence % 2 == 0,
                    "family": (
                        "FUTURE_CHANGED"
                        if item_nbr == 100
                        and current_date == origin + pd.Timedelta(days=1)
                        else "FIXTURE"
                    ),
                    "class": 10,
                    "perishable": 0,
                    "city": "Fixture City",
                    "state": "Fixture State",
                    "store_type": "A",
                    "cluster": 1,
                    "transactions": (
                        None
                        if current_date == origin - pd.Timedelta(days=20)
                        else 1000 + sequence
                    ),
                    "dcoilwtico": (
                        None if current_date.weekday() >= 5 else 40.0 + sequence / 10.0
                    ),
                    "is_holiday": description is not None,
                    "holiday_type": "Event" if description else None,
                    "holiday_locale": "National" if description else None,
                    "holiday_description": description,
                    "holiday_transferred": False,
                    "holiday_event_count": 1 if description else 0,
                }
            )
    return pd.DataFrame(rows), origin


def run_deterministic_fixture_validation() -> dict[str, bool]:
    fixture, origin = _fixture_source_frame()
    direct = build_feature_rows_for_origin(
        fixture,
        forecast_origin=origin,
        allow_assumed_future_promotion=True,
        allow_assumed_future_holidays=True,
    )
    with tempfile.TemporaryDirectory(prefix="favorita_feature_fixture_") as directory:
        parquet_path = Path(directory) / "fixture.parquet"
        pq.write_table(
            pa.Table.from_pandas(fixture, preserve_index=False),
            parquet_path,
            row_group_size=7,
        )
        reloaded = _read_filtered_source_slice(
            parquet_path,
            start_date=origin - pd.Timedelta(days=28),
            end_date=origin + pd.Timedelta(days=14),
            store_nbrs=(1,),
        )
        across_row_groups = build_feature_rows_for_origin(
            reloaded,
            forecast_origin=origin,
            allow_assumed_future_promotion=True,
            allow_assumed_future_holidays=True,
        )
    pd.testing.assert_frame_equal(
        direct.reset_index(drop=True),
        across_row_groups.reset_index(drop=True),
        check_dtype=False,
    )

    item_100 = direct.loc[direct["item_nbr"] == 100].iloc[0]
    item_200 = direct.loc[direct["item_nbr"] == 200].iloc[0]
    source_item_100 = (
        fixture.loc[fixture["item_nbr"] == 100]
        .drop_duplicates("date")
        .set_index("date")
        .sort_index()
    )
    expected_sales_lags = {
        "sales_lag_1": float(
            source_item_100.loc[origin - pd.Timedelta(days=1), "unit_sales"]
        ),
        "sales_lag_7": float(
            source_item_100.loc[origin - pd.Timedelta(days=7), "unit_sales"]
        ),
        "sales_lag_14": float(
            source_item_100.loc[origin - pd.Timedelta(days=14), "unit_sales"]
        ),
        "sales_lag_28": float(
            source_item_100.loc[origin - pd.Timedelta(days=28), "unit_sales"]
        ),
    }
    for feature_name, expected_value in expected_sales_lags.items():
        assert item_100[feature_name] == expected_value

    for window in SALES_MEAN_WINDOWS:
        window_values = source_item_100.loc[
            origin - pd.Timedelta(days=window) : origin - pd.Timedelta(days=1),
            "unit_sales",
        ]
        assert len(window_values) == window
        assert item_100[f"sales_rolling_mean_{window}"] == float(window_values.mean())
    for window in SALES_STD_WINDOWS:
        window_values = source_item_100.loc[
            origin - pd.Timedelta(days=window) : origin - pd.Timedelta(days=1),
            "unit_sales",
        ]
        assert len(window_values) == window
        assert np.isclose(
            item_100[f"sales_rolling_std_{window}"],
            float(window_values.std(ddof=1)),
        )

    assert item_100["family"] == "FIXTURE"
    assert pd.isna(item_200["sales_lag_7"])
    for window in SALES_MEAN_WINDOWS:
        assert pd.isna(item_200[f"sales_rolling_mean_{window}"])
    for window in SALES_STD_WINDOWS:
        assert pd.isna(item_200[f"sales_rolling_std_{window}"])

    store_transactions = (
        fixture[["date", "store_nbr", "transactions"]]
        .drop_duplicates(["date", "store_nbr"])
        .set_index("date")
        .sort_index()["transactions"]
    )
    assert item_100["transactions_at_origin"] == float(store_transactions.loc[origin])
    assert item_100["transactions_lag_7"] == float(
        store_transactions.loc[origin - pd.Timedelta(days=7)]
    )
    assert item_100["transactions_lag_14"] == float(
        store_transactions.loc[origin - pd.Timedelta(days=14)]
    )
    expected_transactions_mean_7 = float(
        store_transactions.loc[origin - pd.Timedelta(days=6) : origin].mean()
    )
    expected_transactions_mean_14 = float(
        store_transactions.loc[origin - pd.Timedelta(days=13) : origin].mean()
    )
    assert item_100["transactions_mean_7d"] == expected_transactions_mean_7
    assert item_100["transactions_mean_14d"] == expected_transactions_mean_14

    future_mutated_fixture = fixture.copy()
    future_mask = future_mutated_fixture["date"] > origin
    future_mutated_fixture.loc[future_mask, "unit_sales"] = 1_000_000_000.0
    future_mutated_fixture.loc[future_mask, "transactions"] = 2_000_000_000.0
    future_mutated = build_feature_rows_for_origin(
        future_mutated_fixture,
        forecast_origin=origin,
        allow_assumed_future_promotion=True,
        allow_assumed_future_holidays=True,
    )
    historical_feature_columns = [
        *SALES_FEATURE_COLUMNS,
        *TRANSACTION_FEATURE_COLUMNS,
    ]
    pd.testing.assert_frame_equal(
        direct[historical_feature_columns],
        future_mutated[historical_feature_columns],
        check_dtype=False,
    )

    earthquake_date = origin + pd.Timedelta(days=3)
    earthquake_rows = direct.loc[direct["forecast_date"] == earthquake_date]
    assert earthquake_rows[list(HOLIDAY_FEATURE_COLUMNS)].isna().all().all()
    assert "holiday_description" not in direct.columns
    assert "dcoilwtico" not in direct.columns
    assert "id" not in direct.columns
    assert TARGET_COLUMN not in INFERENCE_OUTPUT_COLUMNS
    assert direct["forecast_horizon"].between(1, 14).all()
    assert (
        direct["forecast_date"]
        == direct["forecast_origin"]
        + pd.to_timedelta(direct["forecast_horizon"], unit="D")
    ).all()
    return {
        "sales_lag_1_is_t_minus_1": True,
        "sales_lag_7_is_t_minus_7": True,
        "sales_lag_14_is_t_minus_14": True,
        "sales_lag_28_is_t_minus_28": True,
        "sales_windows_exclude_origin": True,
        "complete_calendar_windows": True,
        "missing_exact_date_remains_null": True,
        "missing_date_invalidates_sales_windows": True,
        "transactions_at_origin_is_t": True,
        "transactions_lag_7_is_t_minus_7": True,
        "transactions_lag_14_is_t_minus_14": True,
        "transaction_windows_include_origin": True,
        "future_actuals_do_not_affect_historical_features": True,
        "cross_row_group_equivalence": True,
        "origin_bounded_static_join": True,
        "earthquake_features_excluded": True,
        "forbidden_columns_absent": True,
        "horizon_date_equation": True,
        "train_inference_schema_parity": True,
    }
