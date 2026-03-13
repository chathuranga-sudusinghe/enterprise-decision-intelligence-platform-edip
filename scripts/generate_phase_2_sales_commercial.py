from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


# =========================================================
# Configuration
# =========================================================
RANDOM_SEED = 42
BASE_DIR = Path("data") / "synthetic"

FACT_ORDERS_TARGET = 220_000
MIN_ITEMS_PER_ORDER = 1
MAX_ITEMS_PER_ORDER = 4

START_ORDER_ID = 300000
START_ORDER_ITEM_ID = 300000000
START_SALE_ID = 400000000
START_RETURN_ID = 500000000

CURRENCY_CODE = "USD"
TAX_RATE = 0.05

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# =========================================================
# Path handling
# =========================================================
def build_paths(base_dir: Path) -> Dict[str, Path]:
    return {
        "calendar": base_dir / "dim_calendar.csv",
        "channel": base_dir / "dim_channel.csv",
        "customer": base_dir / "dim_customer.csv",
        "product": base_dir / "dim_product.csv",
        "region": base_dir / "dim_region.csv",
        "store": base_dir / "dim_store.csv",
        "warehouse": base_dir / "dim_warehouse.csv",
        "inventory": base_dir / "fact_inventory_snapshot.csv",
        "orders_out": base_dir / "fact_orders.csv",
        "order_items_out": base_dir / "fact_order_items.csv",
        "sales_out": base_dir / "fact_sales.csv",
        "returns_out": base_dir / "fact_returns.csv",
    }


# =========================================================
# Utility helpers
# =========================================================
def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)


def require_columns(df: pd.DataFrame, required: List[str], df_name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{df_name} is missing required columns: {missing}")


def cast_required_int_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="raise").astype("int64")
    return df


def cast_nullable_int_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


def pick_existing_column(df: pd.DataFrame, candidates: List[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def normalize_string_series(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.lower()


def weighted_choice(values: List, weights: List[float]):
    return random.choices(values, weights=weights, k=1)[0]


def safe_round_2(value: float) -> float:
    return round(float(value), 2)


# =========================================================
# Dimension preparation
# =========================================================
def prepare_calendar(calendar_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(calendar_df, ["date_id", "full_date"], "dim_calendar")
    calendar_df = calendar_df.copy()
    calendar_df["full_date"] = pd.to_datetime(calendar_df["full_date"])
    calendar_df["year"] = calendar_df["full_date"].dt.year
    calendar_df["month"] = calendar_df["full_date"].dt.month
    calendar_df["day_of_week"] = calendar_df["full_date"].dt.dayofweek
    calendar_df["is_weekend"] = calendar_df["day_of_week"].isin([5, 6])
    return calendar_df.sort_values("full_date").reset_index(drop=True)


def prepare_channels(channel_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(channel_df, ["channel_id"], "dim_channel")
    channel_df = channel_df.copy()

    name_col = pick_existing_column(channel_df, ["channel_name", "channel_code", "channel_group"])
    if name_col is None:
        channel_df["channel_name_proxy"] = "channel_" + channel_df["channel_id"].astype(str)
        name_col = "channel_name_proxy"

    channel_df["channel_name_norm"] = normalize_string_series(channel_df[name_col])

    if "is_online_flag" in channel_df.columns:
        channel_df["is_online_flag"] = channel_df["is_online_flag"].astype(bool)
    else:
        channel_df["is_online_flag"] = channel_df["channel_name_norm"].str.contains(
            "online|ecom|e-commerce|digital|web"
        )

    if channel_df["is_online_flag"].sum() == 0:
        first_channel_id = int(channel_df.iloc[0]["channel_id"])
        channel_df.loc[channel_df["channel_id"] == first_channel_id, "is_online_flag"] = True

    return channel_df


def prepare_products(product_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(product_df, ["product_id"], "dim_product")
    product_df = product_df.copy()

    if "unit_cost" not in product_df.columns:
        raise ValueError("dim_product must contain unit_cost")

    if "list_price" not in product_df.columns:
        raise ValueError("dim_product must contain list_price")

    product_df["unit_cost"] = pd.to_numeric(product_df["unit_cost"], errors="raise")
    product_df["list_price"] = pd.to_numeric(product_df["list_price"], errors="raise")

    category_col = pick_existing_column(product_df, ["category", "subcategory", "brand"])
    if category_col is None:
        product_df["category"] = "general"
        category_col = "category"

    product_df["category_norm"] = normalize_string_series(product_df[category_col])

    price_ratio = np.where(
        product_df["list_price"] > 0,
        product_df["unit_cost"] / product_df["list_price"],
        0.60,
    )
    product_df["margin_profile"] = np.where(price_ratio > 0.80, "tight", "normal")

    return product_df


def prepare_customers(customer_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(customer_df, ["customer_id"], "dim_customer")
    customer_df = customer_df.copy()

    region_col = pick_existing_column(customer_df, ["region_id", "home_region_id"])
    if region_col is None:
        customer_df["region_id"] = np.nan
    elif region_col != "region_id":
        customer_df["region_id"] = customer_df[region_col]

    return customer_df


def prepare_stores(store_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(store_df, ["store_id"], "dim_store")
    store_df = store_df.copy()

    region_col = pick_existing_column(store_df, ["region_id"])
    if region_col is None:
        store_df["region_id"] = np.nan

    status_col = pick_existing_column(store_df, ["store_status", "status"])
    if status_col is not None:
        active_mask = normalize_string_series(store_df[status_col]).isin(["open", "active"])
        if active_mask.any():
            store_df = store_df.loc[active_mask].copy()

    return store_df.reset_index(drop=True)


def prepare_warehouses(warehouse_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(warehouse_df, ["warehouse_id"], "dim_warehouse")
    warehouse_df = warehouse_df.copy()

    region_col = pick_existing_column(warehouse_df, ["region_id"])
    if region_col is None:
        warehouse_df["region_id"] = np.nan

    status_col = pick_existing_column(warehouse_df, ["operating_status", "status"])
    if status_col is not None:
        active_mask = normalize_string_series(warehouse_df[status_col]).isin(["open", "active"])
        if active_mask.any():
            warehouse_df = warehouse_df.loc[active_mask].copy()

    return warehouse_df.reset_index(drop=True)


# =========================================================
# Demand and inventory helpers
# =========================================================
def build_latest_inventory_state(
    inventory_df: pd.DataFrame,
) -> Tuple[Dict[Tuple[str, int, int], int], Dict[int, int]]:
    require_columns(
        inventory_df,
        ["snapshot_date_id", "product_id", "location_type", "available_qty"],
        "fact_inventory_snapshot",
    )

    inventory_df = inventory_df.copy()
    inventory_df["snapshot_date_id"] = pd.to_numeric(inventory_df["snapshot_date_id"], errors="raise")
    inventory_df["product_id"] = pd.to_numeric(inventory_df["product_id"], errors="raise")
    inventory_df["available_qty"] = pd.to_numeric(inventory_df["available_qty"], errors="raise").astype(int)

    latest_date_id = int(inventory_df["snapshot_date_id"].max())
    latest_df = inventory_df.loc[inventory_df["snapshot_date_id"] == latest_date_id].copy()

    stock_state: Dict[Tuple[str, int, int], int] = {}
    fallback_by_product: Dict[int, int] = {}

    for _, row in latest_df.iterrows():
        location_type = str(row["location_type"]).strip().lower()
        product_id = int(row["product_id"])
        available_qty = int(max(0, row["available_qty"]))

        if location_type == "store" and "store_id" in latest_df.columns and pd.notna(row.get("store_id")):
            location_id = int(row["store_id"])
            stock_state[("store", location_id, product_id)] = available_qty
        elif location_type == "warehouse" and "warehouse_id" in latest_df.columns and pd.notna(row.get("warehouse_id")):
            location_id = int(row["warehouse_id"])
            stock_state[("warehouse", location_id, product_id)] = available_qty

        fallback_by_product[product_id] = fallback_by_product.get(product_id, 0) + available_qty

    return stock_state, fallback_by_product


def build_channel_weights(channel_df: pd.DataFrame) -> Dict[int, float]:
    weights: Dict[int, float] = {}
    offline_count = max(1, int((~channel_df["is_online_flag"]).sum()))

    for _, row in channel_df.iterrows():
        channel_id = int(row["channel_id"])
        is_online = bool(row["is_online_flag"])
        weights[channel_id] = 0.24 if is_online else 0.76 / offline_count

    return weights


def get_region_for_store(store_row: pd.Series, default_region_ids: List[int]) -> int:
    if pd.notna(store_row.get("region_id")):
        return int(store_row["region_id"])
    return random.choice(default_region_ids)


def get_region_for_warehouse(warehouse_row: pd.Series, default_region_ids: List[int]) -> int:
    if pd.notna(warehouse_row.get("region_id")):
        return int(warehouse_row["region_id"])
    return random.choice(default_region_ids)


def get_customer_region(customer_row: pd.Series, fallback_region_ids: List[int]) -> int:
    if pd.notna(customer_row.get("region_id")):
        return int(customer_row["region_id"])
    return random.choice(fallback_region_ids)


def seasonal_multiplier(order_date: pd.Timestamp) -> float:
    month = order_date.month
    if month in [11, 12]:
        return 1.35
    if month in [6, 7]:
        return 1.10
    if month in [1, 2]:
        return 0.92
    return 1.00


def weekday_multiplier(order_date: pd.Timestamp, is_online: bool) -> float:
    weekday = order_date.dayofweek
    if is_online:
        return 1.08 if weekday in [5, 6] else 1.00
    return 1.05 if weekday in [4, 5] else 0.97 if weekday == 0 else 1.00


def region_demand_multiplier(region_id: int, sorted_region_ids: List[int]) -> float:
    if not sorted_region_ids:
        return 1.00

    weakest_region = sorted_region_ids[-1]
    if region_id == weakest_region:
        return 0.88

    return 1.00 + (0.02 * (sorted_region_ids.index(region_id) % 3))


def channel_discount_profile(is_online: bool) -> float:
    if is_online:
        return random.choice([0.00, 0.03, 0.05, 0.08, 0.10])
    return random.choice([0.00, 0.00, 0.02, 0.03, 0.05])


def qty_request_profile(is_online: bool) -> int:
    if is_online:
        return weighted_choice([1, 2, 3, 4], [0.55, 0.28, 0.12, 0.05])
    return weighted_choice([1, 2, 3], [0.72, 0.22, 0.06])


def category_return_rate(category_norm: str) -> float:
    if any(k in category_norm for k in ["apparel", "fashion", "wear"]):
        return 0.10
    if any(k in category_norm for k in ["electronics", "device"]):
        return 0.05
    if any(k in category_norm for k in ["fragile", "glass", "home"]):
        return 0.07
    return 0.04


# =========================================================
# Core generator
# =========================================================
def generate_phase_2_sales_commercial(
    base_dir: Path,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    paths = build_paths(base_dir)

    calendar_df = prepare_calendar(load_csv(paths["calendar"]))
    channel_df = prepare_channels(load_csv(paths["channel"]))
    customer_df = prepare_customers(load_csv(paths["customer"]))
    product_df = prepare_products(load_csv(paths["product"]))
    region_df = load_csv(paths["region"])
    store_df = prepare_stores(load_csv(paths["store"]))
    warehouse_df = prepare_warehouses(load_csv(paths["warehouse"]))
    inventory_df = load_csv(paths["inventory"])

    stock_state, fallback_by_product = build_latest_inventory_state(inventory_df)

    require_columns(region_df, ["region_id"], "dim_region")
    region_ids = sorted(pd.to_numeric(region_df["region_id"], errors="raise").astype(int).tolist())

    reverse_lookup = dict(zip(calendar_df["full_date"], calendar_df["date_id"]))

    channel_weight_map = build_channel_weights(channel_df)
    channel_ids = channel_df["channel_id"].astype(int).tolist()
    channel_weights = [channel_weight_map[ch] for ch in channel_ids]

    online_channel_ids = set(channel_df.loc[channel_df["is_online_flag"], "channel_id"].astype(int).tolist())

    if store_df.empty:
        raise ValueError("dim_store has no active rows available for Phase 2 generation.")

    if warehouse_df.empty:
        raise ValueError("dim_warehouse has no active rows available for Phase 2 generation.")

    store_records = store_df.to_dict("records")
    warehouse_records = warehouse_df.to_dict("records")
    customer_records = customer_df.to_dict("records")

    product_df["product_weight"] = (
        (product_df["list_price"].clip(lower=1) / product_df["list_price"].clip(lower=1).median()).pow(-0.20)
    )
    product_weights = product_df["product_weight"].tolist()
    product_records = product_df.to_dict("records")

    eligible_dates = calendar_df.copy()

    date_weights: List[float] = []
    for _, drow in eligible_dates.iterrows():
        dt = pd.Timestamp(drow["full_date"])
        base_weight = seasonal_multiplier(dt)
        online_mix_weight = 0.52 * weekday_multiplier(dt, True) + 0.48 * weekday_multiplier(dt, False)
        date_weights.append(base_weight * online_mix_weight)

    min_calendar_date = pd.Timestamp(calendar_df["full_date"].min())
    max_calendar_date = pd.Timestamp(calendar_df["full_date"].max())

    orders_rows: List[dict] = []
    order_items_rows: List[dict] = []
    sales_rows: List[dict] = []
    returns_rows: List[dict] = []

    order_id = START_ORDER_ID
    order_item_id = START_ORDER_ITEM_ID
    sale_id = START_SALE_ID
    return_id = START_RETURN_ID

    for _ in range(FACT_ORDERS_TARGET):
        order_date_row = eligible_dates.sample(n=1, weights=date_weights, replace=True).iloc[0]
        order_date = pd.Timestamp(order_date_row["full_date"])
        order_date_id = int(order_date_row["date_id"])

        channel_id = random.choices(channel_ids, weights=channel_weights, k=1)[0]
        is_online = channel_id in online_channel_ids

        customer_row = random.choice(customer_records)
        customer_id = int(customer_row["customer_id"])

        if is_online:
            warehouse_row = random.choice(warehouse_records)
            warehouse_id: int | None = int(warehouse_row["warehouse_id"])
            store_id: int | None = None
            region_id = get_region_for_warehouse(pd.Series(warehouse_row), region_ids)
            fulfillment_type = random.choice(["ship_from_warehouse", "click_and_collect"])

            if fulfillment_type == "click_and_collect":
                store_row = random.choice(store_records)
                store_id = int(store_row["store_id"])
                warehouse_id = None
                region_id = get_region_for_store(pd.Series(store_row), region_ids)
        else:
            store_row = random.choice(store_records)
            store_id = int(store_row["store_id"])
            warehouse_id = None
            region_id = get_region_for_store(pd.Series(store_row), region_ids)
            fulfillment_type = random.choice(["in_store", "ship_from_store"])

        customer_region = get_customer_region(pd.Series(customer_row), region_ids)
        if random.random() < 0.65:
            region_id = customer_region

        order_number = f"ORD-{order_id}"

        line_count = random.randint(MIN_ITEMS_PER_ORDER, MAX_ITEMS_PER_ORDER)
        chosen_products = random.choices(product_records, weights=product_weights, k=line_count)

        gross_order_amount = 0.0
        discount_amount_total = 0.0
        shipping_fee = 0.0
        tax_amount = 0.0
        total_units = 0
        order_item_count = 0

        order_fulfilled_any = False
        order_cancelled_all = True
        partial_line_found = False

        # Avoid failed payment for fulfilled orders.
        order_payment_failed = random.random() < 0.03

        for line_no, product_row in enumerate(chosen_products, start=1):
            product_id = int(product_row["product_id"])
            category_norm = str(product_row["category_norm"])
            unit_cost = float(product_row["unit_cost"])
            unit_list_price = float(product_row["list_price"])

            demand_pressure = (
                seasonal_multiplier(order_date)
                * weekday_multiplier(order_date, is_online)
                * region_demand_multiplier(region_id, region_ids)
            )

            ordered_qty = qty_request_profile(is_online)
            if demand_pressure > 1.20 and random.random() < 0.35:
                ordered_qty += 1

            location_key = None
            if warehouse_id is not None:
                location_key = ("warehouse", int(warehouse_id), product_id)
            elif store_id is not None:
                location_key = ("store", int(store_id), product_id)

            available_qty = stock_state.get(location_key, fallback_by_product.get(product_id, 0))

            base_stockout_prob = 0.02 if not is_online else 0.04
            if demand_pressure > 1.20:
                base_stockout_prob += 0.03

            requested_qty = ordered_qty
            if order_payment_failed:
                fulfilled_qty = 0
            elif available_qty <= 0 or random.random() < base_stockout_prob:
                fulfilled_qty = 0
            else:
                fulfilled_qty = min(requested_qty, available_qty)
                if random.random() < 0.08 and fulfilled_qty > 0:
                    fulfilled_qty = max(1, fulfilled_qty - 1)

            allocated_qty = fulfilled_qty
            cancelled_qty = max(0, requested_qty - fulfilled_qty)
            stockout_flag = fulfilled_qty < requested_qty

            if order_payment_failed:
                item_status = "cancelled"
                stockout_flag = False
            elif fulfilled_qty == 0:
                item_status = "stockout" if stockout_flag else "cancelled"
            elif fulfilled_qty < requested_qty:
                item_status = "partially_fulfilled"
                partial_line_found = True
            else:
                item_status = "fulfilled"

            if location_key is not None and fulfilled_qty > 0:
                stock_state[location_key] = max(0, stock_state.get(location_key, 0) - fulfilled_qty)
                fallback_by_product[product_id] = max(0, fallback_by_product.get(product_id, 0) - fulfilled_qty)

            discount_rate = channel_discount_profile(is_online)
            if demand_pressure < 0.95 and random.random() < 0.20:
                discount_rate += 0.02

            fulfilled_gross_amount = safe_round_2(fulfilled_qty * unit_list_price)
            line_discount_amount = safe_round_2(fulfilled_gross_amount * discount_rate)
            net_line_amount = safe_round_2(fulfilled_gross_amount - line_discount_amount)

            # Keep current DDL logic valid:
            # net_line_amount = (fulfilled_qty * unit_selling_price) - line_discount_amount
            # Therefore unit_selling_price must stay as list price in this generator.
            unit_selling_price = safe_round_2(unit_list_price)
            gross_line_amount = safe_round_2(requested_qty * unit_list_price)

            order_items_rows.append(
                {
                    "order_item_id": order_item_id,
                    "order_id": order_id,
                    "order_line_number": line_no,
                    "order_date_id": order_date_id,
                    "customer_id": customer_id,
                    "channel_id": channel_id,
                    "store_id": store_id,
                    "warehouse_id": warehouse_id,
                    "region_id": region_id,
                    "product_id": product_id,
                    "ordered_qty": requested_qty,
                    "allocated_qty": allocated_qty,
                    "fulfilled_qty": fulfilled_qty,
                    "cancelled_qty": cancelled_qty,
                    "unit_list_price": safe_round_2(unit_list_price),
                    "unit_selling_price": unit_selling_price,
                    "line_discount_amount": line_discount_amount,
                    "gross_line_amount": gross_line_amount,
                    "net_line_amount": net_line_amount,
                    "stockout_flag": stockout_flag,
                    "item_status": item_status,
                    "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

            gross_order_amount += gross_line_amount
            discount_amount_total += line_discount_amount
            total_units += requested_qty
            order_item_count += 1

            if fulfilled_qty > 0:
                order_fulfilled_any = True
                order_cancelled_all = False

                if is_online:
                    lag_days = weighted_choice([0, 1, 2, 3, 4], [0.08, 0.22, 0.28, 0.24, 0.18])
                else:
                    lag_days = weighted_choice([0, 0, 1, 2], [0.60, 0.20, 0.15, 0.05])

                sale_date = order_date + pd.Timedelta(days=lag_days)
                sale_date = min(max(sale_date, min_calendar_date), max_calendar_date)
                sale_date_id = int(reverse_lookup[pd.Timestamp(sale_date)])

                gross_sales_amount = safe_round_2(fulfilled_qty * unit_list_price)
                discount_amount = safe_round_2(gross_sales_amount * discount_rate)
                net_sales_amount = safe_round_2(gross_sales_amount - discount_amount)
                gross_margin_amount = safe_round_2(net_sales_amount - (fulfilled_qty * unit_cost))

                sales_rows.append(
                    {
                        "sale_id": sale_id,
                        "sale_date_id": sale_date_id,
                        "order_id": order_id,
                        "order_item_id": order_item_id,
                        "customer_id": customer_id,
                        "channel_id": channel_id,
                        "store_id": store_id,
                        "warehouse_id": warehouse_id,
                        "region_id": region_id,
                        "product_id": product_id,
                        "units_sold": fulfilled_qty,
                        "unit_list_price": safe_round_2(unit_list_price),
                        "unit_selling_price": safe_round_2(unit_list_price),
                        "gross_sales_amount": gross_sales_amount,
                        "discount_amount": discount_amount,
                        "net_sales_amount": net_sales_amount,
                        "unit_cost": safe_round_2(unit_cost),
                        "gross_margin_amount": gross_margin_amount,
                        "fulfillment_type": fulfillment_type,
                        "sale_status": "completed",
                        "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

                return_rate = category_return_rate(category_norm)
                if random.random() < return_rate:
                    returned_qty = random.randint(1, fulfilled_qty)
                    refund_amount = safe_round_2((returned_qty * unit_list_price) - (returned_qty * unit_list_price * discount_rate))

                    return_reason = weighted_choice(
                        ["damaged", "wrong_item", "customer_remorse", "quality_issue", "late_delivery", "other"],
                        [0.16, 0.08, 0.30, 0.18, 0.12, 0.16],
                    )

                    if return_reason in ["damaged", "quality_issue"]:
                        restockable_flag = False
                        damaged_flag = True
                        inventory_disposition = weighted_choice(
                            ["damaged", "scrap", "vendor_return"],
                            [0.50, 0.25, 0.25],
                        )
                    elif return_reason == "wrong_item":
                        restockable_flag = True
                        damaged_flag = False
                        inventory_disposition = "restock"
                    else:
                        restockable_flag = random.random() < 0.70
                        damaged_flag = False
                        inventory_disposition = (
                            "restock"
                            if restockable_flag
                            else weighted_choice(["vendor_return", "scrap"], [0.65, 0.35])
                        )

                    return_lag = weighted_choice([2, 3, 5, 7, 10, 14], [0.10, 0.16, 0.28, 0.24, 0.14, 0.08])
                    return_date = sale_date + pd.Timedelta(days=return_lag)
                    return_date = min(max(return_date, min_calendar_date), max_calendar_date)
                    return_date_id = int(reverse_lookup[pd.Timestamp(return_date)])

                    returns_rows.append(
                        {
                            "return_id": return_id,
                            "return_date_id": return_date_id,
                            "sale_id": sale_id,
                            "order_id": order_id,
                            "order_item_id": order_item_id,
                            "customer_id": customer_id,
                            "channel_id": channel_id,
                            "store_id": store_id,
                            "warehouse_id": warehouse_id,
                            "region_id": region_id,
                            "product_id": product_id,
                            "returned_qty": returned_qty,
                            "return_reason": return_reason,
                            "return_status": weighted_choice(
                                ["requested", "approved", "received", "refunded"],
                                [0.05, 0.15, 0.40, 0.40],
                            ),
                            "refund_amount": refund_amount,
                            "restockable_flag": restockable_flag,
                            "damaged_flag": damaged_flag,
                            "inventory_disposition": inventory_disposition,
                            "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

                    if restockable_flag and location_key is not None:
                        stock_state[location_key] = stock_state.get(location_key, 0) + returned_qty
                        fallback_by_product[product_id] = fallback_by_product.get(product_id, 0) + returned_qty

                    return_id += 1

                sale_id += 1

            order_item_id += 1

        if order_payment_failed or order_cancelled_all:
            order_status = "cancelled"
            payment_status = weighted_choice(["failed", "pending"], [0.75, 0.25])
        elif partial_line_found:
            order_status = "partially_fulfilled"
            payment_status = weighted_choice(["paid", "pending"], [0.82, 0.18])
        elif order_fulfilled_any:
            order_status = "completed"
            payment_status = weighted_choice(["paid", "pending"], [0.92, 0.08])
        else:
            order_status = "confirmed"
            payment_status = weighted_choice(["pending", "paid"], [0.80, 0.20])

        if is_online:
            shipping_fee = safe_round_2(weighted_choice([0, 3.99, 4.99, 6.99], [0.25, 0.30, 0.30, 0.15]))
        else:
            shipping_fee = 0.0

        tax_amount = safe_round_2((gross_order_amount - discount_amount_total) * TAX_RATE)
        net_order_amount = safe_round_2(gross_order_amount - discount_amount_total + shipping_fee + tax_amount)

        orders_rows.append(
            {
                "order_id": order_id,
                "order_number": order_number,
                "order_date_id": order_date_id,
                "customer_id": customer_id,
                "channel_id": channel_id,
                "store_id": store_id,
                "region_id": region_id,
                "order_status": order_status,
                "payment_status": payment_status,
                "fulfillment_type": fulfillment_type,
                "item_count": order_item_count,
                "total_units": total_units,
                "gross_order_amount": safe_round_2(gross_order_amount),
                "discount_amount": safe_round_2(discount_amount_total),
                "shipping_fee": safe_round_2(shipping_fee),
                "tax_amount": safe_round_2(tax_amount),
                "net_order_amount": safe_round_2(net_order_amount),
                "currency_code": CURRENCY_CODE,
                "order_created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        order_id += 1

    orders_df = pd.DataFrame(orders_rows)
    order_items_df = pd.DataFrame(order_items_rows)
    sales_df = pd.DataFrame(sales_rows)
    returns_df = pd.DataFrame(returns_rows)

    orders_df = cast_required_int_columns(
        orders_df,
        ["order_id", "order_date_id", "customer_id", "channel_id", "region_id", "item_count", "total_units"],
    )

    order_items_df = cast_required_int_columns(
        order_items_df,
        [
            "order_item_id",
            "order_id",
            "order_line_number",
            "order_date_id",
            "customer_id",
            "channel_id",
            "region_id",
            "product_id",
            "ordered_qty",
            "allocated_qty",
            "fulfilled_qty",
            "cancelled_qty",
        ],
    )

    sales_df = cast_required_int_columns(
        sales_df,
        [
            "sale_id",
            "sale_date_id",
            "order_id",
            "order_item_id",
            "customer_id",
            "channel_id",
            "region_id",
            "product_id",
            "units_sold",
        ],
    )

    if not returns_df.empty:
        returns_df = cast_required_int_columns(
            returns_df,
            [
                "return_id",
                "return_date_id",
                "sale_id",
                "order_id",
                "order_item_id",
                "customer_id",
                "channel_id",
                "region_id",
                "product_id",
                "returned_qty",
            ],
        )

    # Keep nullable ID columns as proper integers with blanks, not 6.0 / 12.0.
    orders_df = cast_nullable_int_columns(orders_df, ["store_id"])
    order_items_df = cast_nullable_int_columns(order_items_df, ["store_id", "warehouse_id"])
    sales_df = cast_nullable_int_columns(sales_df, ["store_id", "warehouse_id"])

    if not returns_df.empty:
        returns_df = cast_nullable_int_columns(returns_df, ["store_id", "warehouse_id"])

    orders_df = orders_df.sort_values(["order_date_id", "order_id"]).reset_index(drop=True)
    order_items_df = order_items_df.sort_values(
        ["order_date_id", "order_id", "order_line_number"]
    ).reset_index(drop=True)
    sales_df = sales_df.sort_values(["sale_date_id", "sale_id"]).reset_index(drop=True)
    returns_df = returns_df.sort_values(["return_date_id", "return_id"]).reset_index(drop=True)

    return orders_df, order_items_df, sales_df, returns_df


# =========================================================
# Main
# =========================================================
def main() -> None:
    paths = build_paths(BASE_DIR)

    try:
        BASE_DIR.mkdir(parents=True, exist_ok=True)

        orders_df, order_items_df, sales_df, returns_df = generate_phase_2_sales_commercial(BASE_DIR)

        orders_df.to_csv(paths["orders_out"], index=False)
        order_items_df.to_csv(paths["order_items_out"], index=False)
        sales_df.to_csv(paths["sales_out"], index=False)
        returns_df.to_csv(paths["returns_out"], index=False)

        print("Phase 2.1B generation completed successfully.")
        print(f"Output folder: {BASE_DIR}")
        print(f"fact_orders.csv       : {len(orders_df):,}")
        print(f"fact_order_items.csv  : {len(order_items_df):,}")
        print(f"fact_sales.csv        : {len(sales_df):,}")
        print(f"fact_returns.csv      : {len(returns_df):,}")

    except Exception as exc:
        print(f"Phase 2.1B generation failed: {exc}")
        raise
    finally:
        print("Phase 2.1B generator script finished.")


if __name__ == "__main__":
    main()