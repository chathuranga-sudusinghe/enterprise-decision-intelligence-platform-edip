from __future__ import annotations

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

PROMOTION_TARGET_MIN = 140
PROMOTION_TARGET_MAX = 220

START_PROMOTION_ID = 600000000
START_PRICE_HISTORY_ID = 700000000

PROMOTION_PRIORITIES = ["high", "medium", "low"]
ONLINE_CHANNEL_NAMES = {"e-commerce", "mobile app", "marketplace"}

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# =========================================================
# Paths
# =========================================================
@dataclass
class Paths:
    base_dir: Path
    calendar_csv: Path
    channel_csv: Path
    product_csv: Path
    region_csv: Path
    sales_csv: Path
    promotions_csv: Path
    price_history_csv: Path


def build_paths(base_dir: Path) -> Paths:
    return Paths(
        base_dir=base_dir,
        calendar_csv=base_dir / "dim_calendar.csv",
        channel_csv=base_dir / "dim_channel.csv",
        product_csv=base_dir / "dim_product.csv",
        region_csv=base_dir / "dim_region.csv",
        sales_csv=base_dir / "fact_sales.csv",
        promotions_csv=base_dir / "fact_promotions.csv",
        price_history_csv=base_dir / "fact_price_history.csv",
    )


# =========================================================
# Utilities
# =========================================================
def safe_round_2(value: float) -> float:
    return round(float(value), 2)


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)


def require_columns(df: pd.DataFrame, columns: List[str], name: str) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def weighted_choice(items: List, weights: List[float]):
    if len(items) != len(weights):
        raise ValueError("Items and weights must have same length.")
    total = sum(weights)
    if total <= 0:
        raise ValueError("Weights must sum to a positive value.")
    return random.choices(items, weights=weights, k=1)[0]


# =========================================================
# Preparation
# =========================================================
def prepare_calendar(calendar_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(calendar_df, ["date_id"], "dim_calendar")

    if "full_date" not in calendar_df.columns:
        calendar_df["full_date"] = pd.to_datetime(
            calendar_df["date_id"].astype(str),
            format="%Y%m%d",
        )
    else:
        calendar_df["full_date"] = pd.to_datetime(calendar_df["full_date"])

    calendar_df["date_id"] = pd.to_numeric(calendar_df["date_id"], errors="raise").astype(int)
    calendar_df = calendar_df.sort_values("full_date").reset_index(drop=True)

    calendar_df["month"] = calendar_df["full_date"].dt.month
    calendar_df["year"] = calendar_df["full_date"].dt.year
    calendar_df["quarter"] = calendar_df["full_date"].dt.quarter
    calendar_df["is_month_end"] = calendar_df["full_date"].dt.is_month_end

    if "holiday_flag" in calendar_df.columns:
        calendar_df["holiday_flag"] = calendar_df["holiday_flag"].fillna(False).astype(bool)
    else:
        calendar_df["holiday_flag"] = False

    return calendar_df


def prepare_channels(channel_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(
        channel_df,
        ["channel_id", "channel_name", "is_online_flag"],
        "dim_channel",
    )
    channel_df["channel_id"] = pd.to_numeric(channel_df["channel_id"], errors="raise").astype(int)
    channel_df["channel_name_norm"] = channel_df["channel_name"].astype(str).str.strip().str.lower()
    channel_df["is_online_flag"] = channel_df["is_online_flag"].astype(bool)
    return channel_df


def prepare_products(product_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(
        product_df,
        ["product_id", "product_name", "category", "list_price", "unit_cost", "active_flag"],
        "dim_product",
    )
    product_df["product_id"] = pd.to_numeric(product_df["product_id"], errors="raise").astype(int)
    product_df["list_price"] = pd.to_numeric(product_df["list_price"], errors="raise").astype(float)
    product_df["unit_cost"] = pd.to_numeric(product_df["unit_cost"], errors="raise").astype(float)
    product_df["active_flag"] = product_df["active_flag"].astype(bool)

    product_df = product_df.loc[product_df["active_flag"]].copy()
    if product_df.empty:
        raise ValueError("dim_product has no active rows available.")

    product_df["category_norm"] = product_df["category"].astype(str).str.strip().str.lower()
    product_df["product_name"] = product_df["product_name"].astype(str).fillna("Unknown Product")
    return product_df


def prepare_regions(region_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(region_df, ["region_id"], "dim_region")
    region_df["region_id"] = pd.to_numeric(region_df["region_id"], errors="raise").astype(int)

    if "region_name" not in region_df.columns:
        region_df["region_name"] = "Region-" + region_df["region_id"].astype(str)

    region_df["region_name"] = region_df["region_name"].astype(str)
    return region_df.sort_values("region_id").reset_index(drop=True)


def prepare_sales(sales_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(
        sales_df,
        ["product_id", "channel_id", "region_id", "units_sold"],
        "fact_sales",
    )

    if "sale_date_id" in sales_df.columns:
        sales_df["sale_date_id"] = pd.to_numeric(sales_df["sale_date_id"], errors="raise").astype(int)
    else:
        sales_df["sale_date_id"] = np.nan

    sales_df["product_id"] = pd.to_numeric(sales_df["product_id"], errors="raise").astype(int)
    sales_df["channel_id"] = pd.to_numeric(sales_df["channel_id"], errors="raise").astype(int)
    sales_df["region_id"] = pd.to_numeric(sales_df["region_id"], errors="raise").astype(int)
    sales_df["units_sold"] = pd.to_numeric(sales_df["units_sold"], errors="raise").astype(float)

    return sales_df


# =========================================================
# Business rules
# =========================================================
def category_discount_bounds(category_norm: str) -> Tuple[float, float]:
    if any(k in category_norm for k in ["grocery", "beverage", "snacks"]):
        return 0.05, 0.18
    if any(k in category_norm for k in ["household", "personal"]):
        return 0.08, 0.22
    if any(k in category_norm for k in ["frozen"]):
        return 0.10, 0.25
    return 0.06, 0.20


def category_campaign_type(category_norm: str) -> str:
    if any(k in category_norm for k in ["frozen"]):
        return weighted_choice(
            ["clearance", "seasonal", "discount"],
            [0.35, 0.20, 0.45],
        )
    if any(k in category_norm for k in ["personal", "household"]):
        return weighted_choice(
            ["discount", "bundle", "loyalty_offer", "seasonal"],
            [0.45, 0.25, 0.15, 0.15],
        )
    return weighted_choice(
        ["discount", "seasonal", "launch_offer", "bundle"],
        [0.55, 0.20, 0.10, 0.15],
    )


def estimate_expected_uplift(discount_pct: float, is_online: bool, priority: str) -> float:
    base = 4.0 + (discount_pct * 1.3)

    if is_online:
        base += 3.0

    if priority == "high":
        base += 4.0
    elif priority == "medium":
        base += 2.0

    noise = random.uniform(-3.0, 6.0)
    return max(2.0, safe_round_2(base + noise))


def estimate_actual_uplift(expected_uplift_pct: float, quarter: int, holiday_flag: bool) -> float:
    seasonal_bonus = 0.0

    if quarter == 4:
        seasonal_bonus += 3.0
    if holiday_flag:
        seasonal_bonus += 2.0

    noise = random.uniform(-8.0, 5.0)
    actual = expected_uplift_pct + seasonal_bonus + noise
    return max(0.0, safe_round_2(actual))


def promo_priority_weights() -> Tuple[List[str], List[float]]:
    return PROMOTION_PRIORITIES, [0.25, 0.50, 0.25]


def promotion_status_for_end_date(end_date: pd.Timestamp, max_calendar_date: pd.Timestamp) -> str:
    if end_date >= max_calendar_date - pd.Timedelta(days=7):
        return weighted_choice(["planned", "approved", "active"], [0.20, 0.35, 0.45])
    if end_date >= max_calendar_date - pd.Timedelta(days=30):
        return weighted_choice(["active", "completed"], [0.40, 0.60])
    return "completed"


def campaign_duration_days(campaign_type: str) -> int:
    if campaign_type == "clearance":
        return random.randint(10, 21)
    if campaign_type == "launch_offer":
        return random.randint(7, 14)
    if campaign_type == "bundle":
        return random.randint(14, 28)
    return random.randint(7, 21)


# =========================================================
# Promotion helpers
# =========================================================
def build_product_weights(product_df: pd.DataFrame, sales_df: pd.DataFrame) -> Dict[int, float]:
    sales_by_product = sales_df.groupby("product_id", as_index=False)["units_sold"].sum()
    sales_by_product = sales_by_product.rename(columns={"units_sold": "sales_units"})

    merged = product_df[["product_id", "list_price"]].merge(
        sales_by_product,
        how="left",
        on="product_id",
    )
    merged["sales_units"] = merged["sales_units"].fillna(1.0)
    merged["weight"] = np.sqrt(merged["sales_units"]) * (
        1.0 / np.power(merged["list_price"].clip(lower=1.0), 0.10)
    )

    weight_map = dict(zip(merged["product_id"], merged["weight"]))
    if not weight_map:
        raise ValueError("No product weights could be built.")
    return weight_map


def build_combo_sales_weight(sales_df: pd.DataFrame) -> pd.DataFrame:
    combo = sales_df.groupby(
        ["product_id", "channel_id", "region_id"],
        as_index=False,
    )["units_sold"].sum()

    combo = combo.rename(columns={"units_sold": "combo_units"})

    if combo.empty:
        combo["combo_units"] = pd.Series(dtype=float)

    return combo


def choose_channel_row(channel_df: pd.DataFrame) -> pd.Series:
    weights = []

    for _, row in channel_df.iterrows():
        name = str(row["channel_name_norm"])
        is_online = bool(row["is_online_flag"])

        if is_online or name in ONLINE_CHANNEL_NAMES:
            weights.append(1.35)
        else:
            weights.append(1.00)

    idx = random.choices(list(channel_df.index), weights=weights, k=1)[0]
    return channel_df.loc[idx]


def date_id_for_timestamp(calendar_df: pd.DataFrame, value: pd.Timestamp) -> int:
    match = calendar_df.loc[calendar_df["full_date"] == value, "date_id"]
    if match.empty:
        raise ValueError(f"No date_id found for date {value}")
    return int(match.iloc[0])


def choose_promo_start(calendar_df: pd.DataFrame, campaign_type: str) -> pd.Timestamp:
    eligible = calendar_df.copy()
    eligible = eligible.iloc[10:-30].copy()

    if eligible.empty:
        raise ValueError("Calendar range is too small for promotions generation.")

    weights = np.ones(len(eligible), dtype=float)
    weights += np.where(eligible["quarter"] == 4, 1.4, 0.0)
    weights += np.where(eligible["holiday_flag"], 1.8, 0.0)
    weights += np.where(eligible["is_month_end"], 0.4, 0.0)

    if campaign_type == "clearance":
        weights += np.where(eligible["month"].isin([1, 7, 12]), 1.0, 0.0)
    elif campaign_type == "launch_offer":
        weights += np.where(eligible["month"].isin([3, 6, 9]), 0.7, 0.0)

    chosen_idx = random.choices(list(eligible.index), weights=weights, k=1)[0]
    return pd.Timestamp(eligible.loc[chosen_idx, "full_date"])


def has_overlap(
    existing_windows: List[Tuple[pd.Timestamp, pd.Timestamp]],
    candidate_start: pd.Timestamp,
    candidate_end: pd.Timestamp,
    min_gap_days: int = 3,
) -> bool:
    for start, end in existing_windows:
        padded_start = start - pd.Timedelta(days=min_gap_days)
        padded_end = end + pd.Timedelta(days=min_gap_days)

        if candidate_start <= padded_end and candidate_end >= padded_start:
            return True

    return False


# =========================================================
# Promotions generation
# =========================================================
def generate_promotions(
    calendar_df: pd.DataFrame,
    channel_df: pd.DataFrame,
    product_df: pd.DataFrame,
    region_df: pd.DataFrame,
    sales_df: pd.DataFrame,
) -> pd.DataFrame:
    product_weight_map = build_product_weights(product_df, sales_df)
    combo_sales_df = build_combo_sales_weight(sales_df)

    combo_lookup: Dict[Tuple[int, int, int], float] = {}
    for _, row in combo_sales_df.iterrows():
        combo_lookup[
            (int(row["product_id"]), int(row["channel_id"]), int(row["region_id"]))
        ] = float(row["combo_units"])

    combo_percentile_75 = (
        float(np.percentile(list(combo_lookup.values()), 75)) if combo_lookup else 0.0
    )

    product_ids = product_df["product_id"].tolist()
    product_weights = [product_weight_map[p] for p in product_ids]

    region_ids = region_df["region_id"].astype(int).tolist()
    region_weights = [1.00 + (0.05 * i) for i in range(len(region_ids))]

    promo_count = random.randint(PROMOTION_TARGET_MIN, PROMOTION_TARGET_MAX)

    promotion_rows: List[Dict] = []
    existing_windows_by_scope: Dict[Tuple[int, int, int], List[Tuple[pd.Timestamp, pd.Timestamp]]] = {}

    max_calendar_date = pd.Timestamp(calendar_df["full_date"].max())

    for promotion_id in range(START_PROMOTION_ID, START_PROMOTION_ID + promo_count):
        for _attempt in range(100):
            product_id = random.choices(product_ids, weights=product_weights, k=1)[0]
            product_row = product_df.loc[product_df["product_id"] == product_id].iloc[0]

            channel_row = choose_channel_row(channel_df)
            channel_id = int(channel_row["channel_id"])
            is_online = bool(channel_row["is_online_flag"])

            region_id = random.choices(region_ids, weights=region_weights, k=1)[0]

            campaign_type = category_campaign_type(str(product_row["category_norm"]))
            start_date = choose_promo_start(calendar_df, campaign_type)
            duration_days = campaign_duration_days(campaign_type)
            end_date = start_date + pd.Timedelta(days=duration_days - 1)

            scope_key = (product_id, channel_id, region_id)
            windows = existing_windows_by_scope.setdefault(scope_key, [])

            if has_overlap(windows, start_date, end_date, min_gap_days=5):
                continue

            base_price = safe_round_2(float(product_row["list_price"]))

            min_disc, max_disc = category_discount_bounds(str(product_row["category_norm"]))
            discount_rate = random.uniform(min_disc, max_disc)

            combo_units = combo_lookup.get(scope_key, 0.0)
            if combo_units > combo_percentile_75:
                discount_rate += 0.02

            discount_rate = min(0.35, max(0.03, discount_rate))
            promo_price = safe_round_2(base_price * (1.0 - discount_rate))
            promo_price = min(promo_price, safe_round_2(base_price - 0.01))
            promo_price = max(0.01, promo_price)

            discount_amount = safe_round_2(base_price - promo_price)
            discount_pct = safe_round_2((discount_amount / base_price) * 100)

            priorities, priority_weights = promo_priority_weights()
            promo_priority = weighted_choice(priorities, priority_weights)

            expected_uplift_pct = estimate_expected_uplift(
                discount_pct=discount_pct,
                is_online=is_online,
                priority=promo_priority,
            )

            holiday_flag = bool(
                calendar_df.loc[calendar_df["full_date"] == start_date, "holiday_flag"].iloc[0]
            )
            actual_uplift_pct = estimate_actual_uplift(
                expected_uplift_pct=expected_uplift_pct,
                quarter=int(start_date.quarter),
                holiday_flag=holiday_flag,
            )

            budget_amount = safe_round_2(
                max(
                    500.0,
                    (discount_amount * random.randint(250, 1800))
                    * (1.25 if promo_priority == "high" else 1.0),
                )
            )

            promotion_status = promotion_status_for_end_date(end_date, max_calendar_date)
            stackable_flag = random.random() < (0.12 if is_online else 0.06)

            promo_reason = weighted_choice(
                [
                    "traffic_growth",
                    "inventory_push",
                    "seasonal_event",
                    "competitive_response",
                    "new_product_awareness",
                    "margin_tradeoff",
                ],
                [0.20, 0.18, 0.22, 0.15, 0.10, 0.15],
            )

            promotion_code = f"PRM-{promotion_id}"
            promotion_name = (
                f"{product_row['product_name']} "
                f"{campaign_type.replace('_', ' ').title()} "
                f"{start_date.strftime('%Y%m')}"
            )

            windows.append((start_date, end_date))

            promotion_rows.append(
                {
                    "promotion_id": int(promotion_id),
                    "promotion_code": promotion_code,
                    "promotion_name": promotion_name[:200],
                    "campaign_type": campaign_type,
                    "promotion_status": promotion_status,
                    "product_id": int(product_id),
                    "channel_id": int(channel_id),
                    "region_id": int(region_id),
                    "start_date_id": date_id_for_timestamp(calendar_df, start_date),
                    "end_date_id": date_id_for_timestamp(calendar_df, end_date),
                    "base_unit_price": base_price,
                    "promo_unit_price": promo_price,
                    "discount_amount": discount_amount,
                    "discount_pct": discount_pct,
                    "expected_uplift_pct": expected_uplift_pct,
                    "actual_uplift_pct": actual_uplift_pct,
                    "budget_amount": budget_amount,
                    "promo_priority": promo_priority,
                    "stackable_flag": bool(stackable_flag),
                    "promo_reason": promo_reason,
                }
            )
            break
        else:
            raise RuntimeError("Could not place a promotion without overlap after many attempts.")

    promotions_df = pd.DataFrame(promotion_rows).sort_values(
        ["product_id", "channel_id", "region_id", "start_date_id", "promotion_id"]
    ).reset_index(drop=True)

    return promotions_df


# =========================================================
# Price history generation
# =========================================================
def build_segments_from_promotions(
    promotions_for_scope: pd.DataFrame,
    full_start: pd.Timestamp,
    full_end: pd.Timestamp,
) -> List[Dict]:
    boundaries = {full_start, full_end + pd.Timedelta(days=1)}

    for _, row in promotions_for_scope.iterrows():
        start = pd.Timestamp(row["start_date"])
        end = pd.Timestamp(row["end_date"])
        boundaries.add(start)
        boundaries.add(end + pd.Timedelta(days=1))

    sorted_points = sorted(boundaries)
    segments: List[Dict] = []

    for i in range(len(sorted_points) - 1):
        seg_start = sorted_points[i]
        seg_end = sorted_points[i + 1] - pd.Timedelta(days=1)

        if seg_start > seg_end:
            continue

        active_promo: Optional[pd.Series] = None
        for _, row in promotions_for_scope.iterrows():
            p_start = pd.Timestamp(row["start_date"])
            p_end = pd.Timestamp(row["end_date"])

            if seg_start >= p_start and seg_end <= p_end:
                active_promo = row
                break

        segments.append(
            {
                "segment_start": seg_start,
                "segment_end": seg_end,
                "promotion_row": active_promo,
            }
        )

    return segments

def build_regular_price_windows(
    calendar_df: pd.DataFrame,
    product_row: pd.Series,
    channel_id: int,
    region_id: int,
    start_price_history_id: int,
) -> Tuple[List[Dict], int]:
    rows: List[Dict] = []
    full_dates = calendar_df["full_date"].tolist()
    max_calendar_date = pd.Timestamp(calendar_df["full_date"].max())

    split_points = sorted(random.sample(range(40, len(full_dates) - 20), k=4))
    starts = [0] + split_points
    ends = split_points + [len(full_dates)]

    current_id = start_price_history_id
    list_price = safe_round_2(float(product_row["list_price"]))
    unit_cost = safe_round_2(float(product_row["unit_cost"]))

    for s_idx, e_idx in zip(starts, ends):
        start_date = pd.Timestamp(full_dates[s_idx])
        end_date = pd.Timestamp(full_dates[e_idx - 1])

        drift = random.uniform(-0.04, 0.00)
        selling_price = safe_round_2(list_price * (1.0 + drift))

        selling_price = max(unit_cost + 0.01, selling_price)
        selling_price = min(selling_price, list_price)
        selling_price = safe_round_2(selling_price)

        markdown_pct = safe_round_2(
            max(0.0, ((list_price - selling_price) / list_price) * 100)
        )

        price_status = (
            "active"
            if end_date >= max_calendar_date - pd.Timedelta(days=7)
            else "expired"
        )

        rows.append(
            {
                "price_history_id": int(current_id),
                "product_id": int(product_row["product_id"]),
                "channel_id": int(channel_id),
                "region_id": int(region_id),
                "effective_start_date": start_date,
                "effective_end_date": end_date,
                "list_price": list_price,
                "selling_price": selling_price,
                "promo_price": np.nan,
                "markdown_pct": markdown_pct,
                "price_change_reason": weighted_choice(
                    ["regular_review", "cost_change", "competitive_response", "seasonal_adjustment"],
                    [0.45, 0.20, 0.15, 0.20],
                ),
                "price_status": price_status,
                "is_promo_price_flag": False,
                "source_promotion_id": np.nan,
            }
        )
        current_id += 1

    return rows, current_id


def generate_price_history(
    calendar_df: pd.DataFrame,
    promotions_df: pd.DataFrame,
    product_df: pd.DataFrame,
    channel_df: pd.DataFrame,
    region_df: pd.DataFrame,
) -> pd.DataFrame:
    require_columns(
        promotions_df,
        ["promotion_id", "product_id", "channel_id", "region_id", "start_date_id", "end_date_id"],
        "fact_promotions",
    )

    date_lookup = dict(zip(calendar_df["date_id"], calendar_df["full_date"]))

    promotions_df = promotions_df.copy()
    promotions_df["start_date"] = promotions_df["start_date_id"].map(date_lookup)
    promotions_df["end_date"] = promotions_df["end_date_id"].map(date_lookup)

    full_start = pd.Timestamp(calendar_df["full_date"].min())
    full_end = pd.Timestamp(calendar_df["full_date"].max())
    max_calendar_date = full_end

    product_lookup = product_df.set_index("product_id")
    channel_lookup = channel_df.set_index("channel_id")
    region_ids = region_df["region_id"].astype(int).tolist()

    rows: List[Dict] = []
    current_price_history_id = START_PRICE_HISTORY_ID

    scope_cols = ["product_id", "channel_id", "region_id"]
    scope_keys = promotions_df[scope_cols].drop_duplicates().sort_values(scope_cols)

    for _, scope in scope_keys.iterrows():
        product_id = int(scope["product_id"])
        channel_id = int(scope["channel_id"])
        region_id = int(scope["region_id"])

        product_row = product_lookup.loc[product_id]
        promotions_for_scope = promotions_df.loc[
            (promotions_df["product_id"] == product_id)
            & (promotions_df["channel_id"] == channel_id)
            & (promotions_df["region_id"] == region_id)
        ].sort_values(["start_date", "promotion_id"])

        segments = build_segments_from_promotions(
            promotions_for_scope=promotions_for_scope,
            full_start=full_start,
            full_end=full_end,
        )

        list_price = safe_round_2(float(product_row["list_price"]))
        unit_cost = safe_round_2(float(product_row["unit_cost"]))
        is_online = bool(channel_lookup.loc[channel_id, "is_online_flag"])

        for segment in segments:
            seg_start = pd.Timestamp(segment["segment_start"])
            seg_end = pd.Timestamp(segment["segment_end"])
            promo_row = segment["promotion_row"]

            if promo_row is not None:
                selling_price = safe_round_2(float(promo_row["promo_unit_price"]))
                promo_price = selling_price
                markdown_pct = safe_round_2(((list_price - selling_price) / list_price) * 100)
                reason = "promotion"
                is_promo = True
                source_promotion_id = int(promo_row["promotion_id"])
            else:
                base_drift = random.uniform(-0.03, 0.03)
                if is_online and random.random() < 0.35:
                    base_drift -= random.uniform(0.00, 0.03)

                selling_price = safe_round_2(list_price * (1.0 + base_drift))
                selling_price = max(unit_cost + 0.01, selling_price)
                selling_price = min(selling_price, list_price)
                selling_price = safe_round_2(selling_price)

                promo_price = np.nan
                markdown_pct = safe_round_2(
                    max(0.0, ((list_price - selling_price) / list_price) * 100)
                )
                reason = weighted_choice(
                    ["regular_review", "seasonal_adjustment", "competitive_response", "cost_change"],
                    [0.45, 0.20, 0.20, 0.15],
                )
                is_promo = False
                source_promotion_id = np.nan

            status = "active" if seg_end >= max_calendar_date - pd.Timedelta(days=7) else "expired"

            rows.append(
                {
                    "price_history_id": int(current_price_history_id),
                    "product_id": product_id,
                    "channel_id": channel_id,
                    "region_id": region_id,
                    "effective_start_date": seg_start,
                    "effective_end_date": seg_end,
                    "list_price": list_price,
                    "selling_price": safe_round_2(selling_price),
                    "promo_price": promo_price,
                    "markdown_pct": markdown_pct,
                    "price_change_reason": reason,
                    "price_status": status,
                    "is_promo_price_flag": bool(is_promo),
                    "source_promotion_id": source_promotion_id,
                }
            )
            current_price_history_id += 1

    promoted_scope_set = {
        (int(r["product_id"]), int(r["channel_id"]), int(r["region_id"]))
        for _, r in scope_keys.iterrows()
    }

    product_sample_size = max(30, int(len(product_df) * 0.12))
    sampled_products = product_df.sample(
        n=min(product_sample_size, len(product_df)),
        random_state=RANDOM_SEED,
        replace=False,
    )

    channel_ids = channel_df["channel_id"].astype(int).tolist()

    # Prevent duplicate extra non-promoted scopes
    extra_scope_set = set()

    for _, product_row in sampled_products.iterrows():
        product_id = int(product_row["product_id"])

        target_scope_count = random.randint(1, 2)
        created_scope_count = 0
        attempt_count = 0
        max_attempts = 20

        while created_scope_count < target_scope_count and attempt_count < max_attempts:
            attempt_count += 1

            channel_id = random.choice(channel_ids)
            region_id = random.choice(region_ids)

            scope_key = (product_id, channel_id, region_id)

            if scope_key in promoted_scope_set:
                continue

            if scope_key in extra_scope_set:
                continue

            extra_rows, current_price_history_id = build_regular_price_windows(
                calendar_df=calendar_df,
                product_row=product_row,
                channel_id=channel_id,
                region_id=region_id,
                start_price_history_id=current_price_history_id,
            )
            rows.extend(extra_rows)

            extra_scope_set.add(scope_key)
            created_scope_count += 1

    price_history_df = pd.DataFrame(rows).sort_values(
        ["product_id", "channel_id", "region_id", "effective_start_date", "price_history_id"]
    ).reset_index(drop=True)

    date_id_lookup = dict(zip(calendar_df["full_date"], calendar_df["date_id"]))
    price_history_df["effective_start_date_id"] = price_history_df["effective_start_date"].map(date_id_lookup).astype(int)
    price_history_df["effective_end_date_id"] = price_history_df["effective_end_date"].map(date_id_lookup).astype(int)

    price_history_df = price_history_df[
        [
            "price_history_id",
            "product_id",
            "channel_id",
            "region_id",
            "effective_start_date_id",
            "effective_end_date_id",
            "list_price",
            "selling_price",
            "promo_price",
            "markdown_pct",
            "price_change_reason",
            "price_status",
            "is_promo_price_flag",
            "source_promotion_id",
        ]
    ]

    return price_history_df


# =========================================================
# Validation
# =========================================================
def validate_promotions(promotions_df: pd.DataFrame) -> None:
    if promotions_df.empty:
        raise ValueError("fact_promotions generation produced zero rows.")

    if promotions_df["promotion_id"].duplicated().any():
        raise ValueError("Duplicate promotion_id values found.")

    if promotions_df["promotion_code"].duplicated().any():
        raise ValueError("Duplicate promotion_code values found.")

    invalid_dates = promotions_df.loc[promotions_df["end_date_id"] < promotions_df["start_date_id"]]
    if not invalid_dates.empty:
        raise ValueError("Promotion date window validation failed.")

    invalid_prices = promotions_df.loc[
        (promotions_df["base_unit_price"] <= 0)
        | (promotions_df["promo_unit_price"] <= 0)
        | (promotions_df["promo_unit_price"] > promotions_df["base_unit_price"])
    ]
    if not invalid_prices.empty:
        raise ValueError("Promotion pricing validation failed.")

    invalid_discount_pct = promotions_df.loc[
        (promotions_df["discount_pct"] < 0) | (promotions_df["discount_pct"] > 100)
    ]
    if not invalid_discount_pct.empty:
        raise ValueError("Promotion discount percent validation failed.")

    work = promotions_df.sort_values(
        ["product_id", "channel_id", "region_id", "start_date_id"]
    ).copy()

    for _, group in work.groupby(["product_id", "channel_id", "region_id"], dropna=False):
        prev_end = None

        for _, row in group.iterrows():
            current_start = int(row["start_date_id"])
            current_end = int(row["end_date_id"])

            if prev_end is not None and current_start <= prev_end:
                raise ValueError(
                    f"Overlapping promotion windows found for scope "
                    f"(product_id={row['product_id']}, channel_id={row['channel_id']}, region_id={row['region_id']})."
                )
            prev_end = current_end


def validate_price_history(price_history_df: pd.DataFrame) -> None:
    if price_history_df.empty:
        raise ValueError("fact_price_history generation produced zero rows.")

    if price_history_df["price_history_id"].duplicated().any():
        raise ValueError("Duplicate price_history_id values found.")

    invalid_dates = price_history_df.loc[
        price_history_df["effective_end_date_id"] < price_history_df["effective_start_date_id"]
    ]
    if not invalid_dates.empty:
        raise ValueError("Price history date window validation failed.")

    invalid_prices = price_history_df.loc[
        (price_history_df["list_price"] <= 0)
        | (price_history_df["selling_price"] <= 0)
        | (price_history_df["selling_price"] > price_history_df["list_price"] + 0.0001)
    ]
    if not invalid_prices.empty:
        raise ValueError("Price history list/selling price validation failed.")

    invalid_promo_prices = price_history_df.loc[
        price_history_df["promo_price"].notna()
        & (
            (price_history_df["promo_price"] <= 0)
            | (price_history_df["promo_price"] > price_history_df["list_price"] + 0.0001)
        )
    ]
    if not invalid_promo_prices.empty:
        raise ValueError("Price history promo price validation failed.")

    invalid_markdown = price_history_df.loc[
        (price_history_df["markdown_pct"] < 0) | (price_history_df["markdown_pct"] > 100)
    ]
    if not invalid_markdown.empty:
        raise ValueError("Price history markdown percent validation failed.")

    work = price_history_df.sort_values(
        ["product_id", "channel_id", "region_id", "effective_start_date_id", "price_history_id"]
    ).copy()

    for _, group in work.groupby(["product_id", "channel_id", "region_id"], dropna=False):
        prev_end = None

        for _, row in group.iterrows():
            start_id = int(row["effective_start_date_id"])
            end_id = int(row["effective_end_date_id"])

            if prev_end is not None and start_id <= prev_end:
                raise ValueError(
                    f"Overlapping price history windows found for scope "
                    f"(product_id={row['product_id']}, channel_id={row['channel_id']}, region_id={row['region_id']})."
                )
            prev_end = end_id

    promo_flag_mismatch = price_history_df.loc[
        (price_history_df["is_promo_price_flag"] == True)
        & (price_history_df["source_promotion_id"].isna())
    ]
    if not promo_flag_mismatch.empty:
        raise ValueError("Promo price rows must have source_promotion_id.")

    nonpromo_source_mismatch = price_history_df.loc[
        (price_history_df["is_promo_price_flag"] == False)
        & (price_history_df["source_promotion_id"].notna())
    ]
    if not nonpromo_source_mismatch.empty:
        raise ValueError("Non-promo price rows must not have source_promotion_id.")


# =========================================================
# Main orchestration
# =========================================================
def generate_phase_2_promotions_price_history(base_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    paths = build_paths(base_dir)

    calendar_df = prepare_calendar(load_csv(paths.calendar_csv))
    channel_df = prepare_channels(load_csv(paths.channel_csv))
    product_df = prepare_products(load_csv(paths.product_csv))
    region_df = prepare_regions(load_csv(paths.region_csv))
    sales_df = prepare_sales(load_csv(paths.sales_csv))

    promotions_df = generate_promotions(
        calendar_df=calendar_df,
        channel_df=channel_df,
        product_df=product_df,
        region_df=region_df,
        sales_df=sales_df,
    )

    price_history_df = generate_price_history(
        calendar_df=calendar_df,
        promotions_df=promotions_df,
        product_df=product_df,
        channel_df=channel_df,
        region_df=region_df,
    )

    validate_promotions(promotions_df)
    validate_price_history(price_history_df)

    return promotions_df, price_history_df


def save_outputs(
    promotions_df: pd.DataFrame,
    price_history_df: pd.DataFrame,
    base_dir: Path,
) -> None:
    paths = build_paths(base_dir)

    # Keep nullable integer columns as proper integers for CSV export
    promotions_df = promotions_df.copy()
    price_history_df = price_history_df.copy()

    price_history_df["source_promotion_id"] = price_history_df["source_promotion_id"].astype("Int64")

    promotions_df.to_csv(paths.promotions_csv, index=False)
    price_history_df.to_csv(paths.price_history_csv, index=False)

    print("Generation completed successfully.")
    print(f"Saved: {paths.promotions_csv} ({len(promotions_df):,} rows)")
    print(f"Saved: {paths.price_history_csv} ({len(price_history_df):,} rows)")


def main() -> None:
    try:
        promotions_df, price_history_df = generate_phase_2_promotions_price_history(BASE_DIR)
        save_outputs(promotions_df, price_history_df, BASE_DIR)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        raise


if __name__ == "__main__":
    main()