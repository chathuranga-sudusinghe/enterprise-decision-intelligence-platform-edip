from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


# =========================================================
# Configuration
# =========================================================
DEFAULT_GROUP_KEYS: list[str] = ["product_id", "region_id", "channel_id", "location_id"]
DEFAULT_LAG_DAYS: list[int] = [1, 7, 14, 28]
DEFAULT_ROLLING_WINDOWS: list[int] = [7, 14, 28]


# =========================================================
# Data contract
# =========================================================
@dataclass(frozen=True)
class DemandFeatureConfig:
    """
    Configuration for demand feature engineering.

    lag_days:
        Historical lookback points used for lag demand features.

    rolling_windows:
        Rolling windows used for average and volatility features.

    group_keys:
        Keys that define one forecasting series.
        For EDIP, demand should behave differently by product, region, channel,
        and location.

    target_column:
        The demand value to forecast.

    date_column:
        The daily grain date column.

    promotion_flag_column:
        Binary indicator showing whether a product was under promotion.

    inventory_column:
        Available inventory at the end of the day or snapshot point.

    price_column:
        Selling price or effective selling price.

    lead_time_column:
        Supplier lead time. This matters later for replenishment logic.

    stockout_threshold:
        If available inventory is less than or equal to this value,
        treat the row as a stockout / near-stockout indicator.
    """

    lag_days: Sequence[int] = tuple(DEFAULT_LAG_DAYS)
    rolling_windows: Sequence[int] = tuple(DEFAULT_ROLLING_WINDOWS)
    group_keys: Sequence[str] = tuple(DEFAULT_GROUP_KEYS)
    target_column: str = "units_sold"
    date_column: str = "date"
    promotion_flag_column: str = "promotion_flag"
    inventory_column: str = "available_qty"
    price_column: str = "selling_price"
    lead_time_column: str = "lead_time_days_avg"
    stockout_threshold: int = 0


# =========================================================
# Validation helpers
# =========================================================
def _validate_required_columns(df: pd.DataFrame, required_columns: Iterable[str]) -> None:
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(
            "Missing required columns for demand feature engineering: "
            f"{missing_columns}"
        )


def _ensure_datetime_column(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
    output_df = df.copy()
    output_df[date_column] = pd.to_datetime(output_df[date_column], errors="coerce")

    if output_df[date_column].isna().any():
        invalid_count = int(output_df[date_column].isna().sum())
        raise ValueError(
            f"Date parsing failed for column '{date_column}'. "
            f"Invalid row count: {invalid_count}"
        )

    return output_df


def _ensure_numeric_column(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    output_df = df.copy()
    output_df[column_name] = pd.to_numeric(output_df[column_name], errors="coerce")
    return output_df


# =========================================================
# Core feature functions
# =========================================================
def add_calendar_features(
    df: pd.DataFrame,
    *,
    date_column: str,
) -> pd.DataFrame:
    """
    Add calendar-based demand features.

    These are important because your project rules already say seasonality must
    be visible across month, holiday period, region, and channel.
    """
    output_df = df.copy()

    output_df["day_of_week"] = output_df[date_column].dt.dayofweek
    output_df["day_of_month"] = output_df[date_column].dt.day
    output_df["week_of_year"] = output_df[date_column].dt.isocalendar().week.astype(int)
    output_df["month"] = output_df[date_column].dt.month
    output_df["quarter"] = output_df[date_column].dt.quarter
    output_df["year"] = output_df[date_column].dt.year
    output_df["is_weekend"] = output_df["day_of_week"].isin([5, 6]).astype(int)
    output_df["is_month_start"] = output_df[date_column].dt.is_month_start.astype(int)
    output_df["is_month_end"] = output_df[date_column].dt.is_month_end.astype(int)

    return output_df


def add_price_features(
    df: pd.DataFrame,
    *,
    group_keys: Sequence[str],
    date_column: str,
    price_column: str,
) -> pd.DataFrame:
    """
    Add price movement features.
    """
    output_df = df.copy()
    output_df = output_df.sort_values(list(group_keys) + [date_column]).reset_index(drop=True)

    grouped = output_df.groupby(list(group_keys), sort=False)

    output_df["price_lag_1"] = grouped[price_column].shift(1)
    output_df["price_change_1d"] = output_df[price_column] - output_df["price_lag_1"]
    output_df["price_change_pct_1d"] = np.where(
        output_df["price_lag_1"].fillna(0) > 0,
        (output_df[price_column] - output_df["price_lag_1"]) / output_df["price_lag_1"],
        0.0,
    )

    return output_df


def add_inventory_features(
    df: pd.DataFrame,
    *,
    group_keys: Sequence[str],
    date_column: str,
    inventory_column: str,
    stockout_threshold: int,
) -> pd.DataFrame:
    """
    Add inventory stress and stockout-related features.

    Your project rules say stockouts suppress realized sales, so these features
    are necessary to separate true demand from constrained realized sales.
    """
    output_df = df.copy()
    output_df = output_df.sort_values(list(group_keys) + [date_column]).reset_index(drop=True)

    grouped = output_df.groupby(list(group_keys), sort=False)

    output_df["inventory_lag_1"] = grouped[inventory_column].shift(1)
    output_df["inventory_delta_1d"] = output_df[inventory_column] - output_df["inventory_lag_1"]
    output_df["is_stockout"] = (output_df[inventory_column] <= stockout_threshold).astype(int)
    output_df["is_low_stock"] = (output_df[inventory_column] <= (stockout_threshold + 10)).astype(int)

    return output_df


def add_lag_features(
    df: pd.DataFrame,
    *,
    group_keys: Sequence[str],
    date_column: str,
    target_column: str,
    lag_days: Sequence[int],
) -> pd.DataFrame:
    """
    Add lag demand features.
    """
    output_df = df.copy()
    output_df = output_df.sort_values(list(group_keys) + [date_column]).reset_index(drop=True)

    grouped = output_df.groupby(list(group_keys), sort=False)

    for lag_day in lag_days:
        output_df[f"{target_column}_lag_{lag_day}"] = grouped[target_column].shift(lag_day)

    return output_df


def add_rolling_features(
    df: pd.DataFrame,
    *,
    group_keys: Sequence[str],
    date_column: str,
    target_column: str,
    rolling_windows: Sequence[int],
) -> pd.DataFrame:
    """
    Add rolling demand summary features.

    We shift by 1 first so the current day does not leak into the feature set.
    """
    output_df = df.copy()
    output_df = output_df.sort_values(list(group_keys) + [date_column]).reset_index(drop=True)

    grouped = output_df.groupby(list(group_keys), sort=False)

    shifted_target = grouped[target_column].shift(1)

    for window in rolling_windows:
        rolling_group = shifted_target.groupby(
            [output_df[key] for key in group_keys],
            sort=False
        )

        output_df[f"{target_column}_roll_mean_{window}"] = (
            rolling_group.rolling(window=window, min_periods=1).mean().reset_index(level=list(range(len(group_keys))), drop=True)
        )
        output_df[f"{target_column}_roll_std_{window}"] = (
            rolling_group.rolling(window=window, min_periods=1).std().reset_index(level=list(range(len(group_keys))), drop=True)
        )
        output_df[f"{target_column}_roll_min_{window}"] = (
            rolling_group.rolling(window=window, min_periods=1).min().reset_index(level=list(range(len(group_keys))), drop=True)
        )
        output_df[f"{target_column}_roll_max_{window}"] = (
            rolling_group.rolling(window=window, min_periods=1).max().reset_index(level=list(range(len(group_keys))), drop=True)
        )

    return output_df


def add_promotion_features(
    df: pd.DataFrame,
    *,
    group_keys: Sequence[str],
    date_column: str,
    promotion_flag_column: str,
) -> pd.DataFrame:
    """
    Add promotion-related features.

    Promotions are one of the locked business rules that must affect demand.
    """
    output_df = df.copy()
    output_df = output_df.sort_values(list(group_keys) + [date_column]).reset_index(drop=True)

    grouped = output_df.groupby(list(group_keys), sort=False)

    output_df["promotion_flag"] = output_df[promotion_flag_column].fillna(0).astype(int)
    output_df["promotion_lag_1"] = grouped["promotion_flag"].shift(1).fillna(0).astype(int)

    # Consecutive promotion days inside each demand series
    promo_groups = (output_df["promotion_flag"] != grouped["promotion_flag"].shift()).cumsum()
    output_df["promotion_run_length"] = (
        output_df.groupby(promo_groups)["promotion_flag"].cumsum()
        * output_df["promotion_flag"]
    )

    return output_df


def add_supplier_context_features(
    df: pd.DataFrame,
    *,
    lead_time_column: str,
) -> pd.DataFrame:
    """
    Add supplier timing risk context.

    Lead time matters because slower suppliers increase replenishment risk.
    """
    output_df = df.copy()

    output_df["lead_time_days_avg"] = output_df[lead_time_column]
    output_df["is_long_lead_time"] = (output_df[lead_time_column] >= 14).astype(int)
    output_df["is_very_long_lead_time"] = (output_df[lead_time_column] >= 21).astype(int)

    return output_df


def add_target_features(
    df: pd.DataFrame,
    *,
    group_keys: Sequence[str],
    date_column: str,
    target_column: str,
    horizon_days: int = 1,
) -> pd.DataFrame:
    """
    Add forecasting target.

    For the first version, use next-day demand as the supervised learning target.
    """
    output_df = df.copy()
    output_df = output_df.sort_values(list(group_keys) + [date_column]).reset_index(drop=True)

    grouped = output_df.groupby(list(group_keys), sort=False)
    output_df[f"target_{target_column}_t_plus_{horizon_days}"] = grouped[target_column].shift(-horizon_days)

    return output_df


def build_demand_features(
    base_df: pd.DataFrame,
    config: DemandFeatureConfig | None = None,
) -> pd.DataFrame:
    """
    Main feature engineering entry point.

    Expected input grain:
        One row per product-region-channel-location-date.

    Expected columns:
        product_id
        region_id
        channel_id
        location_id
        date
        units_sold
        promotion_flag
        available_qty
        selling_price
        lead_time_days_avg

    Optional extra columns are preserved.
    """
    cfg = config or DemandFeatureConfig()

    required_columns = [
        *cfg.group_keys,
        cfg.date_column,
        cfg.target_column,
        cfg.promotion_flag_column,
        cfg.inventory_column,
        cfg.price_column,
        cfg.lead_time_column,
    ]
    _validate_required_columns(base_df, required_columns)

    features_df = base_df.copy()
    features_df = _ensure_datetime_column(features_df, cfg.date_column)
    features_df = _ensure_numeric_column(features_df, cfg.target_column)
    features_df = _ensure_numeric_column(features_df, cfg.inventory_column)
    features_df = _ensure_numeric_column(features_df, cfg.price_column)
    features_df = _ensure_numeric_column(features_df, cfg.lead_time_column)

    features_df = features_df.sort_values(list(cfg.group_keys) + [cfg.date_column]).reset_index(drop=True)

    features_df = add_calendar_features(
        features_df,
        date_column=cfg.date_column,
    )
    features_df = add_price_features(
        features_df,
        group_keys=cfg.group_keys,
        date_column=cfg.date_column,
        price_column=cfg.price_column,
    )
    features_df = add_inventory_features(
        features_df,
        group_keys=cfg.group_keys,
        date_column=cfg.date_column,
        inventory_column=cfg.inventory_column,
        stockout_threshold=cfg.stockout_threshold,
    )
    features_df = add_lag_features(
        features_df,
        group_keys=cfg.group_keys,
        date_column=cfg.date_column,
        target_column=cfg.target_column,
        lag_days=cfg.lag_days,
    )
    features_df = add_rolling_features(
        features_df,
        group_keys=cfg.group_keys,
        date_column=cfg.date_column,
        target_column=cfg.target_column,
        rolling_windows=cfg.rolling_windows,
    )
    features_df = add_promotion_features(
        features_df,
        group_keys=cfg.group_keys,
        date_column=cfg.date_column,
        promotion_flag_column=cfg.promotion_flag_column,
    )
    features_df = add_supplier_context_features(
        features_df,
        lead_time_column=cfg.lead_time_column,
    )
    features_df = add_target_features(
        features_df,
        group_keys=cfg.group_keys,
        date_column=cfg.date_column,
        target_column=cfg.target_column,
        horizon_days=1,
    )

    return features_df


# =========================================================
# Utility function for later pipeline use
# =========================================================
def save_feature_dataset(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Save engineered features in parquet format.

    Use cloud-friendly Path handling, not hardcoded file paths.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)


# =========================================================
# Example local execution
# =========================================================
if __name__ == "__main__":
    sample_input_path = Path("data") / "processed" / "training_base" / "demand_base.parquet"
    sample_output_path = Path("data") / "processed" / "features" / "demand_features.parquet"

    if not sample_input_path.exists():
        raise FileNotFoundError(
            "Sample input file not found. Expected path: "
            f"{sample_input_path}"
        )

    input_df = pd.read_parquet(sample_input_path)
    feature_df = build_demand_features(input_df)
    save_feature_dataset(feature_df, sample_output_path)

    print(f"Feature dataset saved to: {sample_output_path}")