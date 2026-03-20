from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# =========================================================
# Configuration
# =========================================================
RANDOM_SEED = 42
BASE_DIR = Path("data") / "synthetic"

START_FORECAST_ID = 800000000
START_RECOMMENDATION_ID = 900000000
FORECAST_RUN_ID = 2026031401

FORECAST_HORIZON_DAYS = 28
MIN_HISTORY_DAYS = 56
MAX_PRODUCTS_PER_STORE = 180
MAX_PRODUCTS_PER_WAREHOUSE = 260

MODEL_NAME = "NorthStarHybridDemandModel"
MODEL_VERSION = "v1.0.0"

DEFAULT_FORECAST_DATE = "2025-12-01"

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# =========================================================
# Paths
# =========================================================
@dataclass
class Paths:
    base_dir: Path
    calendar_csv: Path
    product_csv: Path
    supplier_csv: Path
    store_csv: Path
    warehouse_csv: Path
    sales_csv: Path
    promotions_csv: Path
    inventory_csv: Path
    po_csv: Path
    forecast_out_csv: Path
    replenishment_out_csv: Path


def build_paths(base_dir: Path) -> Paths:
    base_dir.mkdir(parents=True, exist_ok=True)

    return Paths(
        base_dir=base_dir,
        calendar_csv=base_dir / "dim_calendar.csv",
        product_csv=base_dir / "dim_product.csv",
        supplier_csv=base_dir / "dim_supplier.csv",
        store_csv=base_dir / "dim_store.csv",
        warehouse_csv=base_dir / "dim_warehouse.csv",
        sales_csv=base_dir / "fact_sales.csv",
        promotions_csv=base_dir / "fact_promotions.csv",
        inventory_csv=base_dir / "fact_inventory_snapshot.csv",
        po_csv=base_dir / "fact_purchase_orders.csv",
        forecast_out_csv=base_dir / "fact_demand_forecast.csv",
        replenishment_out_csv=base_dir / "fact_replenishment_recommendation.csv",
    )


# =========================================================
# Generic helpers
# =========================================================
def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)


def require_columns(df: pd.DataFrame, required: List[str], df_name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{df_name} is missing required columns: {missing}")


def cast_required_int_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    for col in columns:
        if df[col].isna().any():
            raise ValueError(f"Required integer column '{col}' contains NULL values.")
        df[col] = pd.to_numeric(df[col], errors="raise").astype("int64")
    return df


def cast_nullable_int_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


def safe_round_2(value: float) -> float:
    return round(float(value), 2)


def safe_round_4(value: float) -> float:
    return round(float(value), 4)


def normalize_text(value: object) -> str:
    return str(value).strip().lower()


def coefficient_of_variation(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    mean_val = float(np.mean(values))
    if mean_val <= 0:
        return 0.0
    std_val = float(np.std(values))
    return std_val / mean_val


# =========================================================
# Data preparation
# =========================================================
def prepare_calendar(calendar_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(calendar_df, ["date_id", "full_date"], "dim_calendar")
    calendar_df = calendar_df.copy()
    calendar_df["date_id"] = pd.to_numeric(calendar_df["date_id"], errors="raise").astype(int)
    calendar_df["full_date"] = pd.to_datetime(calendar_df["full_date"])
    calendar_df = calendar_df.sort_values("full_date").reset_index(drop=True)
    calendar_df["day_of_week_num"] = calendar_df["full_date"].dt.dayofweek
    calendar_df["month"] = calendar_df["full_date"].dt.month
    calendar_df["quarter"] = calendar_df["full_date"].dt.quarter

    if "holiday_flag" in calendar_df.columns:
        calendar_df["holiday_flag"] = calendar_df["holiday_flag"].fillna(False).astype(bool)
    else:
        calendar_df["holiday_flag"] = False

    return calendar_df


def prepare_products(product_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(
        product_df,
        [
            "product_id",
            "supplier_id",
            "unit_cost",
            "list_price",
            "reorder_point_default",
            "safety_stock_default",
        ],
        "dim_product",
    )
    product_df = product_df.copy()
    product_df["product_id"] = pd.to_numeric(product_df["product_id"], errors="raise").astype(int)
    product_df["supplier_id"] = pd.to_numeric(product_df["supplier_id"], errors="raise").astype(int)
    product_df["unit_cost"] = pd.to_numeric(product_df["unit_cost"], errors="raise").astype(float)
    product_df["list_price"] = pd.to_numeric(product_df["list_price"], errors="raise").astype(float)
    product_df["reorder_point_default"] = pd.to_numeric(
        product_df["reorder_point_default"], errors="raise"
    ).astype(int)
    product_df["safety_stock_default"] = pd.to_numeric(
        product_df["safety_stock_default"], errors="raise"
    ).astype(int)

    if "category" not in product_df.columns:
        product_df["category"] = "general"

    product_df["category_norm"] = product_df["category"].astype(str).str.strip().str.lower()
    return product_df


def prepare_suppliers(supplier_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(supplier_df, ["supplier_id", "lead_time_days_avg"], "dim_supplier")
    supplier_df = supplier_df.copy()
    supplier_df["supplier_id"] = pd.to_numeric(supplier_df["supplier_id"], errors="raise").astype(int)
    supplier_df["lead_time_days_avg"] = pd.to_numeric(
        supplier_df["lead_time_days_avg"], errors="raise"
    ).astype(int)

    if "on_time_rate" in supplier_df.columns:
        supplier_df["on_time_rate"] = pd.to_numeric(supplier_df["on_time_rate"], errors="coerce").fillna(90.0)
    else:
        supplier_df["on_time_rate"] = 90.0

    return supplier_df


def prepare_stores(store_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(store_df, ["store_id", "region_id"], "dim_store")
    store_df = store_df.copy()
    store_df["store_id"] = pd.to_numeric(store_df["store_id"], errors="raise").astype(int)
    store_df["region_id"] = pd.to_numeric(store_df["region_id"], errors="raise").astype(int)

    if "store_status" in store_df.columns:
        active_mask = store_df["store_status"].astype(str).str.strip().str.lower().isin(["active", "open"])
        if active_mask.any():
            store_df = store_df.loc[active_mask].copy()

    return store_df.reset_index(drop=True)


def prepare_warehouses(warehouse_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(warehouse_df, ["warehouse_id", "region_id"], "dim_warehouse")
    warehouse_df = warehouse_df.copy()
    warehouse_df["warehouse_id"] = pd.to_numeric(warehouse_df["warehouse_id"], errors="raise").astype(int)
    warehouse_df["region_id"] = pd.to_numeric(warehouse_df["region_id"], errors="raise").astype(int)

    if "operating_status" in warehouse_df.columns:
        active_mask = warehouse_df["operating_status"].astype(str).str.strip().str.lower().isin(
            ["active", "open"]
        )
        if active_mask.any():
            warehouse_df = warehouse_df.loc[active_mask].copy()

    return warehouse_df.reset_index(drop=True)


def prepare_sales(sales_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(
        sales_df,
        ["sale_date_id", "product_id", "region_id", "units_sold"],
        "fact_sales",
    )
    sales_df = sales_df.copy()
    sales_df["sale_date_id"] = pd.to_numeric(sales_df["sale_date_id"], errors="raise").astype(int)
    sales_df["product_id"] = pd.to_numeric(sales_df["product_id"], errors="raise").astype(int)
    sales_df["region_id"] = pd.to_numeric(sales_df["region_id"], errors="raise").astype(int)
    sales_df["units_sold"] = pd.to_numeric(sales_df["units_sold"], errors="raise").astype(float)

    if "store_id" in sales_df.columns:
        sales_df["store_id"] = pd.to_numeric(sales_df["store_id"], errors="coerce").astype("Int64")
    else:
        sales_df["store_id"] = pd.Series(pd.array([pd.NA] * len(sales_df), dtype="Int64"))

    if "warehouse_id" in sales_df.columns:
        sales_df["warehouse_id"] = pd.to_numeric(sales_df["warehouse_id"], errors="coerce").astype("Int64")
    else:
        sales_df["warehouse_id"] = pd.Series(pd.array([pd.NA] * len(sales_df), dtype="Int64"))

    return sales_df


def prepare_promotions(promotions_df: pd.DataFrame) -> pd.DataFrame:
    if promotions_df.empty:
        return promotions_df.copy()

    required = ["product_id", "start_date_id", "end_date_id", "discount_pct"]
    require_columns(promotions_df, required, "fact_promotions")
    promotions_df = promotions_df.copy()
    promotions_df["product_id"] = pd.to_numeric(promotions_df["product_id"], errors="raise").astype(int)
    promotions_df["start_date_id"] = pd.to_numeric(promotions_df["start_date_id"], errors="raise").astype(int)
    promotions_df["end_date_id"] = pd.to_numeric(promotions_df["end_date_id"], errors="raise").astype(int)
    promotions_df["discount_pct"] = pd.to_numeric(promotions_df["discount_pct"], errors="raise").astype(float)

    if "region_id" in promotions_df.columns:
        promotions_df["region_id"] = pd.to_numeric(promotions_df["region_id"], errors="coerce").astype("Int64")
    else:
        promotions_df["region_id"] = pd.Series(pd.array([pd.NA] * len(promotions_df), dtype="Int64"))

    if "channel_id" in promotions_df.columns:
        promotions_df["channel_id"] = pd.to_numeric(promotions_df["channel_id"], errors="coerce").astype("Int64")
    else:
        promotions_df["channel_id"] = pd.Series(pd.array([pd.NA] * len(promotions_df), dtype="Int64"))

    return promotions_df


def prepare_inventory(inventory_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(
        inventory_df,
        [
            "snapshot_date_id",
            "product_id",
            "location_type",
            "available_qty",
            "reorder_point_qty",
            "safety_stock_qty",
        ],
        "fact_inventory_snapshot",
    )
    inventory_df = inventory_df.copy()
    inventory_df["snapshot_date_id"] = pd.to_numeric(inventory_df["snapshot_date_id"], errors="raise").astype(int)
    inventory_df["product_id"] = pd.to_numeric(inventory_df["product_id"], errors="raise").astype(int)
    inventory_df["available_qty"] = pd.to_numeric(inventory_df["available_qty"], errors="raise").astype(float)
    inventory_df["reorder_point_qty"] = pd.to_numeric(inventory_df["reorder_point_qty"], errors="raise").astype(float)
    inventory_df["safety_stock_qty"] = pd.to_numeric(inventory_df["safety_stock_qty"], errors="raise").astype(float)

    if "store_id" in inventory_df.columns:
        inventory_df["store_id"] = pd.to_numeric(inventory_df["store_id"], errors="coerce").astype("Int64")
    else:
        inventory_df["store_id"] = pd.Series(pd.array([pd.NA] * len(inventory_df), dtype="Int64"))

    if "warehouse_id" in inventory_df.columns:
        inventory_df["warehouse_id"] = pd.to_numeric(
            inventory_df["warehouse_id"], errors="coerce"
        ).astype("Int64")
    else:
        inventory_df["warehouse_id"] = pd.Series(pd.array([pd.NA] * len(inventory_df), dtype="Int64"))

    inventory_df["location_type_norm"] = inventory_df["location_type"].astype(str).str.strip().str.lower()
    return inventory_df


def prepare_purchase_orders(po_df: pd.DataFrame) -> pd.DataFrame:
    if po_df.empty:
        return po_df.copy()

    required = ["product_id", "supplier_id", "warehouse_id", "po_date_id", "expected_receipt_date_id", "ordered_qty"]
    require_columns(po_df, required, "fact_purchase_orders")
    po_df = po_df.copy()
    for col in ["product_id", "supplier_id", "warehouse_id", "po_date_id", "expected_receipt_date_id", "ordered_qty"]:
        po_df[col] = pd.to_numeric(po_df[col], errors="raise").astype(int)
    return po_df


# =========================================================
# Feature building
# =========================================================
def get_forecast_date(calendar_df: pd.DataFrame) -> pd.Timestamp:
    calendar_dates = sorted(pd.to_datetime(calendar_df["full_date"]).tolist())
    if not calendar_dates:
        raise ValueError("dim_calendar is empty.")

    default_dt = pd.Timestamp(DEFAULT_FORECAST_DATE)

    # Use default date only if enough future dates exist for the full forecast horizon
    if default_dt in set(calendar_dates):
        max_dt = max(calendar_dates)
        if default_dt + pd.Timedelta(days=FORECAST_HORIZON_DAYS) <= max_dt:
            return default_dt

    # Otherwise choose a safe anchor date inside the calendar
    safe_idx = len(calendar_dates) - FORECAST_HORIZON_DAYS - 1
    if safe_idx < 0:
        raise ValueError(
            f"dim_calendar does not contain enough dates for a {FORECAST_HORIZON_DAYS}-day forecast horizon."
        )

    return pd.Timestamp(calendar_dates[safe_idx])

def build_date_maps(calendar_df: pd.DataFrame) -> Tuple[Dict[int, pd.Timestamp], Dict[pd.Timestamp, int]]:
    date_id_to_ts = dict(zip(calendar_df["date_id"], calendar_df["full_date"]))
    ts_to_date_id = dict(zip(calendar_df["full_date"], calendar_df["date_id"]))
    return date_id_to_ts, ts_to_date_id


def build_active_promotion_lookup(
    promotions_df: pd.DataFrame,
    date_id_to_ts: Dict[int, pd.Timestamp],
) -> Dict[Tuple[int, pd.Timestamp, Optional[int]], float]:
    lookup: Dict[Tuple[int, pd.Timestamp, Optional[int]], float] = {}

    if promotions_df.empty:
        return lookup

    for _, row in promotions_df.iterrows():
        product_id = int(row["product_id"])
        region_id = int(row["region_id"]) if pd.notna(row["region_id"]) else None
        start_dt = pd.Timestamp(date_id_to_ts[int(row["start_date_id"])])
        end_dt = pd.Timestamp(date_id_to_ts[int(row["end_date_id"])])
        discount_pct = float(row["discount_pct"])

        for dt in pd.date_range(start=start_dt, end=end_dt, freq="D"):
            key = (product_id, pd.Timestamp(dt), region_id)
            lookup[key] = max(discount_pct, lookup.get(key, 0.0))

    return lookup


def build_latest_inventory_lookup(
    inventory_df: pd.DataFrame,
) -> pd.DataFrame:
    latest_snapshot = int(inventory_df["snapshot_date_id"].max())
    latest_df = inventory_df.loc[inventory_df["snapshot_date_id"] == latest_snapshot].copy()
    return latest_df


def build_supplier_lookup(supplier_df: pd.DataFrame) -> Dict[int, Dict[str, float]]:
    return supplier_df.set_index("supplier_id")[["lead_time_days_avg", "on_time_rate"]].to_dict("index")


def build_product_lookup(product_df: pd.DataFrame) -> Dict[int, Dict[str, float]]:
    keep_cols = [
        "supplier_id",
        "unit_cost",
        "list_price",
        "reorder_point_default",
        "safety_stock_default",
        "category_norm",
    ]
    return product_df.set_index("product_id")[keep_cols].to_dict("index")


def build_recent_po_signal(po_df: pd.DataFrame, forecast_date_id: int) -> Dict[Tuple[int, int], float]:
    if po_df.empty:
        return {}

    recent_po = po_df.loc[po_df["po_date_id"] <= forecast_date_id].copy()
    if recent_po.empty:
        return {}

    recent_po = (
        recent_po.sort_values("po_date_id")
        .groupby(["product_id", "warehouse_id"], as_index=False)
        .tail(3)
    )

    agg = recent_po.groupby(["product_id", "warehouse_id"], as_index=False)["ordered_qty"].mean()
    return {
        (int(r["product_id"]), int(r["warehouse_id"])): float(r["ordered_qty"])
        for _, r in agg.iterrows()
    }


def sales_history_for_scope(
    sales_df: pd.DataFrame,
    location_type: str,
    location_id: int,
    product_id: int,
    forecast_date_id: int,
) -> pd.DataFrame:
    filtered = sales_df.loc[
        (sales_df["product_id"] == product_id)
        & (sales_df["sale_date_id"] < forecast_date_id)
    ].copy()

    if location_type == "store":
        filtered = filtered.loc[filtered["store_id"] == location_id].copy()
    else:
        filtered = filtered.loc[filtered["warehouse_id"] == location_id].copy()

    return filtered


def estimate_base_daily_demand(history_df: pd.DataFrame, min_history_days: int) -> float:
    if history_df.empty:
        return 0.0

    history_df = history_df.sort_values("sale_date_id").copy()
    last_rows = history_df.tail(min_history_days)
    return float(last_rows["units_sold"].mean())


def estimate_weekday_profile(
    history_df: pd.DataFrame,
    date_id_to_ts: Dict[int, pd.Timestamp],
) -> Dict[int, float]:
    if history_df.empty:
        return {i: 1.0 for i in range(7)}

    tmp = history_df.copy()
    tmp["weekday"] = tmp["sale_date_id"].map(date_id_to_ts).apply(lambda x: pd.Timestamp(x).dayofweek)
    day_means = tmp.groupby("weekday")["units_sold"].mean().to_dict()
    overall_mean = max(float(tmp["units_sold"].mean()), 0.01)

    profile = {}
    for i in range(7):
        profile[i] = float(day_means.get(i, overall_mean)) / overall_mean

    return profile


def estimate_location_noise(history_df: pd.DataFrame) -> float:
    if history_df.empty:
        return 0.22

    cv = coefficient_of_variation(history_df["units_sold"].to_numpy(dtype=float))
    return min(0.35, max(0.08, 0.10 + cv * 0.40))


def estimate_confidence(
    history_df: pd.DataFrame,
    supplier_on_time_rate: float,
    promotion_days_in_horizon: int,
) -> float:
    history_points = len(history_df)
    history_factor = min(1.0, history_points / 84.0)
    supplier_factor = max(0.0, min(1.0, supplier_on_time_rate / 100.0))
    promo_penalty = min(0.18, promotion_days_in_horizon * 0.006)

    confidence = 0.45 + (history_factor * 0.30) + (supplier_factor * 0.20) - promo_penalty
    return safe_round_4(min(0.98, max(0.35, confidence)))


def priority_from_risk(stockout_risk: float) -> str:
    if stockout_risk >= 0.80:
        return "critical"
    if stockout_risk >= 0.60:
        return "high"
    if stockout_risk >= 0.35:
        return "normal"
    return "low"


def approval_status_from_priority(priority_level: str) -> str:
    if priority_level == "critical":
        return random.choices(["pending", "approved"], weights=[0.70, 0.30], k=1)[0]
    if priority_level == "high":
        return random.choices(["pending", "approved", "draft"], weights=[0.45, 0.35, 0.20], k=1)[0]
    return random.choices(["draft", "pending", "approved"], weights=[0.55, 0.25, 0.20], k=1)[0]


def reason_code_for_recommendation(
    stockout_risk: float,
    available_qty: float,
    reorder_point: float,
    safety_stock: float,
    lead_time_days: int,
) -> str:
    if available_qty <= 0:
        return "immediate_stockout_risk"
    if stockout_risk >= 0.80:
        return "high_forecast_vs_low_stock"
    if available_qty < safety_stock:
        return "below_safety_stock"
    if available_qty < reorder_point:
        return "below_reorder_point"
    if lead_time_days >= 14:
        return "long_supplier_lead_time"
    return "demand_rebalancing"


# =========================================================
# Core generation
# =========================================================
def generate_forecasts_and_replenishment(
    calendar_df: pd.DataFrame,
    product_df: pd.DataFrame,
    supplier_df: pd.DataFrame,
    store_df: pd.DataFrame,
    warehouse_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    promotions_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    po_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    forecast_date = get_forecast_date(calendar_df)
    date_id_to_ts, ts_to_date_id = build_date_maps(calendar_df)
    forecast_date_id = int(ts_to_date_id[forecast_date])

    target_dates = pd.date_range(
        start=forecast_date + pd.Timedelta(days=1),
        periods=FORECAST_HORIZON_DAYS,
        freq="D",
    )
    target_dates = [pd.Timestamp(dt) for dt in target_dates if pd.Timestamp(dt) in ts_to_date_id]

    if len(target_dates) < FORECAST_HORIZON_DAYS:
        raise ValueError(
            f"Only {len(target_dates)} target dates are available in dim_calendar, "
            f"but {FORECAST_HORIZON_DAYS} are required."
        )

    latest_inventory_df = build_latest_inventory_lookup(inventory_df)
    active_promo_lookup = build_active_promotion_lookup(promotions_df, date_id_to_ts)
    supplier_lookup = build_supplier_lookup(supplier_df)
    product_lookup = build_product_lookup(product_df)
    recent_po_signal = build_recent_po_signal(po_df, forecast_date_id)

    forecast_rows: List[Dict] = []
    recommendation_rows: List[Dict] = []

    forecast_id = START_FORECAST_ID
    recommendation_id = START_RECOMMENDATION_ID

    # -------------------------
    # Store-level forecasts
    # -------------------------
    store_inventory = latest_inventory_df.loc[
        (latest_inventory_df["location_type_norm"] == "store") & latest_inventory_df["store_id"].notna()
    ].copy()

    if len(store_inventory) > 0:
        store_inventory = (
            store_inventory.sort_values(["store_id", "available_qty"], ascending=[True, False])
            .groupby("store_id", as_index=False)
            .head(MAX_PRODUCTS_PER_STORE)
            .reset_index(drop=True)
        )

    for _, inv_row in store_inventory.iterrows():
        product_id = int(inv_row["product_id"])
        store_id = int(inv_row["store_id"])
        region_id = int(
            store_df.loc[store_df["store_id"] == store_id, "region_id"].iloc[0]
        )

        product_meta = product_lookup[product_id]
        supplier_id = int(product_meta["supplier_id"])
        supplier_meta = supplier_lookup[supplier_id]

        history_df = sales_history_for_scope(
            sales_df=sales_df,
            location_type="store",
            location_id=store_id,
            product_id=product_id,
            forecast_date_id=forecast_date_id,
        )

        base_daily_demand = estimate_base_daily_demand(history_df, MIN_HISTORY_DAYS)
        weekday_profile = estimate_weekday_profile(history_df, date_id_to_ts)
        noise_level = estimate_location_noise(history_df)

        promo_days = 0
        total_forecast_units = 0.0

        for target_dt in target_dates:
            weekday_factor = weekday_profile.get(target_dt.dayofweek, 1.0)
            monthly_factor = 1.08 if target_dt.month in [11, 12] else 1.04 if target_dt.month in [6, 7] else 0.96 if target_dt.month in [1, 2] else 1.0

            promo_discount = active_promo_lookup.get((product_id, target_dt, region_id), 0.0)
            promo_discount = max(
                promo_discount,
                active_promo_lookup.get((product_id, target_dt, None), 0.0),
            )
            promo_factor = 1.0 + min(0.45, promo_discount / 100.0 * 1.3)

            if promo_factor > 1.0:
                promo_days += 1

            region_factor = 1.05 if region_id in [2, 4] else 0.98 if region_id == 1 else 1.0
            expected = base_daily_demand * weekday_factor * monthly_factor * promo_factor * region_factor

            random_jitter = np.random.normal(loc=0.0, scale=max(0.15, expected * noise_level * 0.18))
            forecast_units = max(0.0, expected + random_jitter)

            interval_width = max(0.75, forecast_units * (0.16 + noise_level))
            lower = max(0.0, forecast_units - interval_width)
            upper = forecast_units + interval_width

            confidence = estimate_confidence(
                history_df=history_df,
                supplier_on_time_rate=float(supplier_meta["on_time_rate"]),
                promotion_days_in_horizon=promo_days,
            )

            forecast_rows.append(
                {
                    "forecast_id": forecast_id,
                    "forecast_run_id": FORECAST_RUN_ID,
                    "forecast_date_id": forecast_date_id,
                    "target_date_id": int(ts_to_date_id[target_dt]),
                    "product_id": product_id,
                    "store_id": store_id,
                    "warehouse_id": pd.NA,
                    "region_id": region_id,
                    "forecast_units": safe_round_2(forecast_units),
                    "forecast_lower_bound": safe_round_2(lower),
                    "forecast_upper_bound": safe_round_2(upper),
                    "model_name": MODEL_NAME,
                    "model_version": MODEL_VERSION,
                    "confidence_score": confidence,
                    "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            total_forecast_units += forecast_units
            forecast_id += 1

        available_qty = float(inv_row["available_qty"])
        reorder_point = float(inv_row["reorder_point_qty"])
        safety_stock = float(inv_row["safety_stock_qty"])
        lead_time_days = int(supplier_meta["lead_time_days_avg"])

        lead_time_daily = base_daily_demand if base_daily_demand > 0 else max(0.10, total_forecast_units / max(1, len(target_dates)))
        demand_during_lead_time = lead_time_daily * max(1, lead_time_days)
        projected_need = demand_during_lead_time + safety_stock

        gap = max(0.0, projected_need - available_qty)
        expected_service_level = max(0.50, min(0.995, 1.0 - (gap / max(projected_need, 1.0)) * 0.7))
        stockout_risk = max(0.01, min(0.99, gap / max(projected_need, 1.0)))

        recommended_order_qty = int(math.ceil(gap)) if gap > 1 else 0
        recommended_transfer_qty = 0

        if recommended_order_qty > 0:
            recommendation_rows.append(
                {
                    "recommendation_id": recommendation_id,
                    "forecast_run_id": FORECAST_RUN_ID,
                    "recommendation_date_id": forecast_date_id,
                    "product_id": product_id,
                    "target_store_id": store_id,
                    "target_warehouse_id": pd.NA,
                    "recommended_order_qty": recommended_order_qty,
                    "recommended_transfer_qty": recommended_transfer_qty,
                    "priority_level": priority_from_risk(stockout_risk),
                    "reason_code": reason_code_for_recommendation(
                        stockout_risk=stockout_risk,
                        available_qty=available_qty,
                        reorder_point=reorder_point,
                        safety_stock=safety_stock,
                        lead_time_days=lead_time_days,
                    ),
                    "expected_stockout_risk": safe_round_4(stockout_risk),
                    "expected_service_level": safe_round_4(expected_service_level),
                    "recommended_supplier_id": supplier_id,
                    "approval_status": approval_status_from_priority(priority_from_risk(stockout_risk)),
                    "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            recommendation_id += 1

    # -------------------------
    # Warehouse-level forecasts
    # -------------------------
    warehouse_inventory = latest_inventory_df.loc[
        (latest_inventory_df["location_type_norm"] == "warehouse") & latest_inventory_df["warehouse_id"].notna()
    ].copy()

    if len(warehouse_inventory) > 0:
        warehouse_inventory = (
            warehouse_inventory.sort_values(["warehouse_id", "available_qty"], ascending=[True, False])
            .groupby("warehouse_id", as_index=False)
            .head(MAX_PRODUCTS_PER_WAREHOUSE)
            .reset_index(drop=True)
        )

    for _, inv_row in warehouse_inventory.iterrows():
        product_id = int(inv_row["product_id"])
        warehouse_id = int(inv_row["warehouse_id"])
        region_id = int(
            warehouse_df.loc[warehouse_df["warehouse_id"] == warehouse_id, "region_id"].iloc[0]
        )

        product_meta = product_lookup[product_id]
        supplier_id = int(product_meta["supplier_id"])
        supplier_meta = supplier_lookup[supplier_id]

        history_df = sales_history_for_scope(
            sales_df=sales_df,
            location_type="warehouse",
            location_id=warehouse_id,
            product_id=product_id,
            forecast_date_id=forecast_date_id,
        )

        base_daily_demand = estimate_base_daily_demand(history_df, MIN_HISTORY_DAYS)
        weekday_profile = estimate_weekday_profile(history_df, date_id_to_ts)
        noise_level = estimate_location_noise(history_df)

        po_signal = recent_po_signal.get((product_id, warehouse_id), 0.0)
        if base_daily_demand <= 0 and po_signal > 0:
            base_daily_demand = po_signal / 30.0

        promo_days = 0
        total_forecast_units = 0.0

        for target_dt in target_dates:
            weekday_factor = weekday_profile.get(target_dt.dayofweek, 1.0)
            monthly_factor = 1.06 if target_dt.month in [11, 12] else 1.03 if target_dt.month in [6, 7] else 0.97 if target_dt.month in [1, 2] else 1.0

            promo_discount = active_promo_lookup.get((product_id, target_dt, region_id), 0.0)
            promo_discount = max(
                promo_discount,
                active_promo_lookup.get((product_id, target_dt, None), 0.0),
            )
            promo_factor = 1.0 + min(0.30, promo_discount / 100.0 * 0.90)

            if promo_factor > 1.0:
                promo_days += 1

            warehouse_factor = 1.12 if warehouse_id == 1 else 0.95
            expected = base_daily_demand * weekday_factor * monthly_factor * promo_factor * warehouse_factor

            random_jitter = np.random.normal(loc=0.0, scale=max(0.20, expected * noise_level * 0.20))
            forecast_units = max(0.0, expected + random_jitter)

            interval_width = max(1.00, forecast_units * (0.18 + noise_level))
            lower = max(0.0, forecast_units - interval_width)
            upper = forecast_units + interval_width

            confidence = estimate_confidence(
                history_df=history_df,
                supplier_on_time_rate=float(supplier_meta["on_time_rate"]),
                promotion_days_in_horizon=promo_days,
            )

            forecast_rows.append(
                {
                    "forecast_id": forecast_id,
                    "forecast_run_id": FORECAST_RUN_ID,
                    "forecast_date_id": forecast_date_id,
                    "target_date_id": int(ts_to_date_id[target_dt]),
                    "product_id": product_id,
                    "store_id": pd.NA,
                    "warehouse_id": warehouse_id,
                    "region_id": region_id,
                    "forecast_units": safe_round_2(forecast_units),
                    "forecast_lower_bound": safe_round_2(lower),
                    "forecast_upper_bound": safe_round_2(upper),
                    "model_name": MODEL_NAME,
                    "model_version": MODEL_VERSION,
                    "confidence_score": confidence,
                    "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            total_forecast_units += forecast_units
            forecast_id += 1

        available_qty = float(inv_row["available_qty"])
        reorder_point = float(inv_row["reorder_point_qty"])
        safety_stock = float(inv_row["safety_stock_qty"])
        lead_time_days = int(supplier_meta["lead_time_days_avg"])

        lead_time_daily = base_daily_demand if base_daily_demand > 0 else max(0.10, total_forecast_units / max(1, len(target_dates)))
        demand_during_lead_time = lead_time_daily * max(1, lead_time_days)
        projected_need = demand_during_lead_time + safety_stock

        gap = max(0.0, projected_need - available_qty)
        expected_service_level = max(0.50, min(0.995, 1.0 - (gap / max(projected_need, 1.0)) * 0.7))
        stockout_risk = max(0.01, min(0.99, gap / max(projected_need, 1.0)))

        recommended_order_qty = 0
        recommended_transfer_qty = 0

        if gap > 1:
            if warehouse_id != 1 and available_qty < reorder_point:
                recommended_transfer_qty = int(math.ceil(gap * 0.55))
                recommended_order_qty = int(math.ceil(max(0.0, gap - recommended_transfer_qty)))
            else:
                recommended_order_qty = int(math.ceil(gap))

        if recommended_order_qty > 0 or recommended_transfer_qty > 0:
            recommendation_rows.append(
                {
                    "recommendation_id": recommendation_id,
                    "forecast_run_id": FORECAST_RUN_ID,
                    "recommendation_date_id": forecast_date_id,
                    "product_id": product_id,
                    "target_store_id": pd.NA,
                    "target_warehouse_id": warehouse_id,
                    "recommended_order_qty": recommended_order_qty,
                    "recommended_transfer_qty": recommended_transfer_qty,
                    "priority_level": priority_from_risk(stockout_risk),
                    "reason_code": reason_code_for_recommendation(
                        stockout_risk=stockout_risk,
                        available_qty=available_qty,
                        reorder_point=reorder_point,
                        safety_stock=safety_stock,
                        lead_time_days=lead_time_days,
                    ),
                    "expected_stockout_risk": safe_round_4(stockout_risk),
                    "expected_service_level": safe_round_4(expected_service_level),
                    "recommended_supplier_id": supplier_id if recommended_order_qty > 0 else pd.NA,
                    "approval_status": approval_status_from_priority(priority_from_risk(stockout_risk)),
                    "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            recommendation_id += 1

    forecast_df = pd.DataFrame(forecast_rows)
    replenishment_df = pd.DataFrame(recommendation_rows)

    forecast_df = cast_required_int_columns(
        forecast_df,
        ["forecast_id", "forecast_run_id", "forecast_date_id", "target_date_id", "product_id", "region_id"],
    )
    forecast_df = cast_nullable_int_columns(forecast_df, ["store_id", "warehouse_id"])

    forecast_df["forecast_units"] = pd.to_numeric(forecast_df["forecast_units"], errors="raise")
    forecast_df["forecast_lower_bound"] = pd.to_numeric(forecast_df["forecast_lower_bound"], errors="raise")
    forecast_df["forecast_upper_bound"] = pd.to_numeric(forecast_df["forecast_upper_bound"], errors="raise")
    forecast_df["confidence_score"] = pd.to_numeric(forecast_df["confidence_score"], errors="raise")

    replenishment_df = cast_required_int_columns(
        replenishment_df,
        [
            "recommendation_id",
            "forecast_run_id",
            "recommendation_date_id",
            "product_id",
            "recommended_order_qty",
            "recommended_transfer_qty",
        ],
    )
    replenishment_df = cast_nullable_int_columns(
        replenishment_df,
        ["target_store_id", "target_warehouse_id", "recommended_supplier_id"],
    )
    replenishment_df["expected_stockout_risk"] = pd.to_numeric(
        replenishment_df["expected_stockout_risk"], errors="raise"
    )
    replenishment_df["expected_service_level"] = pd.to_numeric(
        replenishment_df["expected_service_level"], errors="raise"
    )

    return forecast_df, replenishment_df


# =========================================================
# Saving
# =========================================================
def save_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


# =========================================================
# Main
# =========================================================
def main() -> None:
    try:
        paths = build_paths(BASE_DIR)

        logger.info("Loading Phase 3 source files.")
        calendar_df = prepare_calendar(load_csv(paths.calendar_csv))
        product_df = prepare_products(load_csv(paths.product_csv))
        supplier_df = prepare_suppliers(load_csv(paths.supplier_csv))
        store_df = prepare_stores(load_csv(paths.store_csv))
        warehouse_df = prepare_warehouses(load_csv(paths.warehouse_csv))
        sales_df = prepare_sales(load_csv(paths.sales_csv))
        promotions_df = prepare_promotions(load_csv(paths.promotions_csv))
        inventory_df = prepare_inventory(load_csv(paths.inventory_csv))
        po_df = prepare_purchase_orders(load_csv(paths.po_csv))

        logger.info("Generating forecast and replenishment outputs.")
        forecast_df, replenishment_df = generate_forecasts_and_replenishment(
            calendar_df=calendar_df,
            product_df=product_df,
            supplier_df=supplier_df,
            store_df=store_df,
            warehouse_df=warehouse_df,
            sales_df=sales_df,
            promotions_df=promotions_df,
            inventory_df=inventory_df,
            po_df=po_df,
        )

        save_csv(forecast_df, paths.forecast_out_csv)
        save_csv(replenishment_df, paths.replenishment_out_csv)

        logger.info("Phase 3 generation completed successfully.")
        logger.info("Forecast rows: %s", f"{len(forecast_df):,}")
        logger.info("Replenishment rows: %s", f"{len(replenishment_df):,}")
        logger.info("Forecast output: %s", paths.forecast_out_csv)
        logger.info("Replenishment output: %s", paths.replenishment_out_csv)

    except Exception as exc:
        logger.exception("Phase 3 forecast/replenishment generation failed: %s", exc)
        raise
    finally:
        logger.info("Phase 3 generator script finished.")


if __name__ == "__main__":
    main()
