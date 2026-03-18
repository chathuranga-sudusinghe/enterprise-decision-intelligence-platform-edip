from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


# =========================================================
# Logging
# =========================================================
logger = logging.getLogger(__name__)


# =========================================================
# Configuration
# =========================================================
@dataclass(frozen=True)
class TrainingDatasetConfig:
    """
    Configuration for building the base daily training dataset.

    The output of this script is a daily, model-ready base table that will
    later be transformed by pipelines/features/demand_features.py.
    """

    base_dir: Path = Path("data") / "synthetic"
    output_dir: Path = Path("data") / "processed" / "training_base"

    calendar_file: str = "dim_calendar.csv"
    product_file: str = "dim_product.csv"
    store_file: str = "dim_store.csv"
    warehouse_file: str = "dim_warehouse.csv"
    channel_file: str = "dim_channel.csv"
    supplier_file: str = "dim_supplier.csv"

    sales_file: str = "fact_sales.csv"
    inventory_file: str = "fact_inventory_snapshot.csv"
    promotions_file: str = "fact_promotions.csv"
    price_history_file: str = "fact_price_history.csv"

    output_file: str = "demand_base.parquet"


# =========================================================
# Helpers
# =========================================================
def _setup_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )


def _load_csv(path: Path, file_label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file for {file_label}: {path}")

    logger.info("Loading %s from %s", file_label, path)
    return pd.read_csv(path)


def _require_columns(df: pd.DataFrame, required_columns: list[str], df_name: str) -> None:
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(
            f"{df_name} is missing required columns: {missing_columns}"
        )


def _safe_to_datetime(series: pd.Series, column_name: str) -> pd.Series:
    output = pd.to_datetime(series, errors="coerce")
    if output.isna().any():
        invalid_count = int(output.isna().sum())
        raise ValueError(
            f"Failed to parse datetime values for '{column_name}'. "
            f"Invalid row count: {invalid_count}"
        )
    return output


def _safe_to_numeric(df: pd.DataFrame, column_name: str, dtype: Optional[str] = None) -> pd.DataFrame:
    df[column_name] = pd.to_numeric(df[column_name], errors="coerce")
    if dtype is not None:
        df[column_name] = df[column_name].astype(dtype)
    return df


def _rename_if_exists(df: pd.DataFrame, old_name: str, new_name: str) -> pd.DataFrame:
    output_df = df.copy()

    if old_name not in output_df.columns:
        return output_df

    if new_name in output_df.columns:
        return output_df

    return output_df.rename(columns={old_name: new_name})


# =========================================================
# Dimension preparation
# =========================================================
def prepare_calendar(calendar_df: pd.DataFrame) -> pd.DataFrame:
    _require_columns(calendar_df, ["date_id", "full_date"], "dim_calendar")

    output_df = calendar_df.copy()
    output_df["full_date"] = _safe_to_datetime(output_df["full_date"], "full_date")
    output_df["date_id"] = pd.to_numeric(output_df["date_id"], errors="raise").astype(int)

    return output_df.rename(columns={"full_date": "date"})


def prepare_products(product_df: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        product_df,
        [
            "product_id",
            "supplier_id",
            "category",
            "unit_cost",
            "list_price",
            "reorder_point_default",
            "safety_stock_default",
        ],
        "dim_product",
    )

    output_df = product_df.copy()
    numeric_columns = [
        "product_id",
        "supplier_id",
        "unit_cost",
        "list_price",
        "reorder_point_default",
        "safety_stock_default",
    ]
    for column in numeric_columns:
        output_df[column] = pd.to_numeric(output_df[column], errors="raise")

    if "active_flag" in output_df.columns:
        output_df["active_flag"] = output_df["active_flag"].astype(bool)
        output_df = output_df.loc[output_df["active_flag"]].copy()

    return output_df[
        [
            "product_id",
            "supplier_id",
            "category",
            "subcategory",
            "brand",
            "unit_cost",
            "list_price",
            "reorder_point_default",
            "safety_stock_default",
        ]
    ].copy()


def prepare_suppliers(supplier_df: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        supplier_df,
        ["supplier_id", "lead_time_days_avg"],
        "dim_supplier",
    )

    output_df = supplier_df.copy()
    output_df["supplier_id"] = pd.to_numeric(output_df["supplier_id"], errors="raise").astype(int)
    output_df["lead_time_days_avg"] = pd.to_numeric(
        output_df["lead_time_days_avg"], errors="raise"
    )

    return output_df[["supplier_id", "lead_time_days_avg"]].copy()


# =========================================================
# Fact preparation
# =========================================================
def prepare_sales(sales_df: pd.DataFrame, calendar_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build daily realized demand by product-location-channel-region-date.
    """
    _require_columns(
        sales_df,
        [
            "sale_date_id",
            "product_id",
            "channel_id",
            "region_id",
            "units_sold",
        ],
        "fact_sales",
    )

    output_df = sales_df.copy()

    numeric_columns = [
        "sale_date_id",
        "product_id",
        "channel_id",
        "region_id",
        "units_sold",
    ]
    optional_numeric_columns = [
        "store_id",
        "gross_sales_amount",
        "net_sales_amount",
        "discount_amount",
        "promotion_id",
    ]

    for column in numeric_columns:
        output_df[column] = pd.to_numeric(output_df[column], errors="raise")

    for column in optional_numeric_columns:
        if column in output_df.columns:
            output_df[column] = pd.to_numeric(output_df[column], errors="coerce")

    if "gross_sales_amount" not in output_df.columns and "gross_sales" in output_df.columns:
        output_df = output_df.rename(columns={"gross_sales": "gross_sales_amount"})

    if "net_sales_amount" not in output_df.columns and "net_sales" in output_df.columns:
        output_df = output_df.rename(columns={"net_sales": "net_sales_amount"})

    if "discount_amount" not in output_df.columns and "discount_value" in output_df.columns:
        output_df = output_df.rename(columns={"discount_value": "discount_amount"})

    if "store_id" not in output_df.columns:
        output_df["store_id"] = pd.NA

    if "promotion_id" not in output_df.columns:
        output_df["promotion_id"] = pd.NA

    if "gross_sales_amount" not in output_df.columns:
        output_df["gross_sales_amount"] = 0.0

    if "net_sales_amount" not in output_df.columns:
        output_df["net_sales_amount"] = 0.0

    if "discount_amount" not in output_df.columns:
        output_df["discount_amount"] = 0.0

    output_df = output_df.merge(
        calendar_df[["date_id", "date"]],
        left_on="sale_date_id",
        right_on="date_id",
        how="left",
        validate="many_to_one",
    )

    if output_df["date"].isna().any():
        raise ValueError("Sales records contain invalid sale_date_id values.")

    output_df["location_type"] = "store"
    output_df["location_id"] = output_df["store_id"]

    daily_sales_df = (
        output_df.groupby(
            [
                "date",
                "product_id",
                "region_id",
                "channel_id",
                "location_type",
                "location_id",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            units_sold=("units_sold", "sum"),
            gross_sales_amount=("gross_sales_amount", "sum"),
            net_sales_amount=("net_sales_amount", "sum"),
            discount_amount=("discount_amount", "sum"),
            promotion_id=("promotion_id", "max"),
        )
    )

    daily_sales_df["location_id"] = daily_sales_df["location_id"].astype("Int64")
    return daily_sales_df


def prepare_inventory(inventory_df: pd.DataFrame, calendar_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build daily inventory base by product-location-date.
    """
    _require_columns(
        inventory_df,
        [
            "snapshot_date_id",
            "product_id",
            "location_type",
            "available_qty",
            "reorder_point_qty",
            "safety_stock_qty",
            "stockout_flag",
        ],
        "fact_inventory_snapshot",
    )

    output_df = inventory_df.copy()

    numeric_columns = [
        "snapshot_date_id",
        "product_id",
        "available_qty",
        "reorder_point_qty",
        "safety_stock_qty",
    ]
    optional_numeric_columns = [
        "store_id",
        "warehouse_id",
        "on_hand_qty",
        "reserved_qty",
        "in_transit_qty",
        "damaged_qty",
        "days_of_cover_estimate",
    ]

    for column in numeric_columns:
        output_df[column] = pd.to_numeric(output_df[column], errors="raise")

    for column in optional_numeric_columns:
        if column in output_df.columns:
            output_df[column] = pd.to_numeric(output_df[column], errors="coerce")

    output_df["stockout_flag"] = output_df["stockout_flag"].astype(bool)
    output_df["location_type"] = output_df["location_type"].astype(str).str.strip().str.lower()

    if "store_id" not in output_df.columns:
        output_df["store_id"] = pd.NA
    if "warehouse_id" not in output_df.columns:
        output_df["warehouse_id"] = pd.NA
    if "on_hand_qty" not in output_df.columns:
        output_df["on_hand_qty"] = output_df["available_qty"]
    if "reserved_qty" not in output_df.columns:
        output_df["reserved_qty"] = 0
    if "in_transit_qty" not in output_df.columns:
        output_df["in_transit_qty"] = 0
    if "damaged_qty" not in output_df.columns:
        output_df["damaged_qty"] = 0
    if "days_of_cover_estimate" not in output_df.columns:
        output_df["days_of_cover_estimate"] = pd.NA

    output_df["location_id"] = output_df["store_id"]
    warehouse_mask = output_df["location_type"] == "warehouse"
    output_df.loc[warehouse_mask, "location_id"] = output_df.loc[warehouse_mask, "warehouse_id"]

    output_df = output_df.merge(
        calendar_df[["date_id", "date"]],
        left_on="snapshot_date_id",
        right_on="date_id",
        how="left",
        validate="many_to_one",
    )

    if output_df["date"].isna().any():
        raise ValueError("Inventory records contain invalid snapshot_date_id values.")

    output_df["location_id"] = output_df["location_id"].astype("Int64")

    return output_df[
        [
            "date",
            "product_id",
            "location_type",
            "location_id",
            "store_id",
            "warehouse_id",
            "available_qty",
            "on_hand_qty",
            "reserved_qty",
            "in_transit_qty",
            "damaged_qty",
            "reorder_point_qty",
            "safety_stock_qty",
            "stockout_flag",
            "days_of_cover_estimate",
        ]
    ].copy()


def prepare_promotions(
    promotions_df: pd.DataFrame,
    calendar_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Expand promotions into daily flags by product-channel-region-date.
    """
    _require_columns(
        promotions_df,
        [
            "promotion_id",
            "product_id",
            "channel_id",
            "start_date_id",
            "end_date_id",
        ],
        "fact_promotions",
    )

    output_df = promotions_df.copy()

    numeric_columns = [
        "promotion_id",
        "product_id",
        "channel_id",
        "start_date_id",
        "end_date_id",
    ]
    optional_numeric_columns = [
        "region_id",
        "discount_pct",
        "discount_amount",
        "base_unit_price",
        "promo_unit_price",
    ]

    for column in numeric_columns:
        output_df[column] = pd.to_numeric(output_df[column], errors="raise")

    for column in optional_numeric_columns:
        if column in output_df.columns:
            output_df[column] = pd.to_numeric(output_df[column], errors="coerce")

    if "region_id" not in output_df.columns:
        output_df["region_id"] = pd.NA

    if "discount_pct" not in output_df.columns:
        output_df["discount_pct"] = 0.0

    output_df = output_df.merge(
        calendar_df[["date_id", "date"]],
        left_on="start_date_id",
        right_on="date_id",
        how="left",
        validate="many_to_one",
    ).rename(columns={"date": "start_date"})

    output_df = output_df.merge(
        calendar_df[["date_id", "date"]],
        left_on="end_date_id",
        right_on="date_id",
        how="left",
        validate="many_to_one",
        suffixes=("", "_end"),
    ).rename(columns={"date": "end_date"})

    if output_df["start_date"].isna().any() or output_df["end_date"].isna().any():
        raise ValueError("Promotion records contain invalid date IDs.")

    expanded_rows: list[dict] = []

    for _, row in output_df.iterrows():
        promo_dates = pd.date_range(start=row["start_date"], end=row["end_date"], freq="D")

        for promo_date in promo_dates:
            expanded_rows.append(
                {
                    "date": promo_date,
                    "product_id": int(row["product_id"]),
                    "channel_id": int(row["channel_id"]),
                    "region_id": int(row["region_id"]) if pd.notna(row["region_id"]) else pd.NA,
                    "promotion_id": int(row["promotion_id"]),
                    "promotion_flag": 1,
                    "discount_pct": float(row["discount_pct"]) if pd.notna(row["discount_pct"]) else 0.0,
                }
            )

    if not expanded_rows:
        return pd.DataFrame(
            columns=[
                "date",
                "product_id",
                "channel_id",
                "region_id",
                "promotion_id",
                "promotion_flag",
                "discount_pct",
            ]
        )

    expanded_df = pd.DataFrame(expanded_rows)

    return (
        expanded_df.groupby(
            ["date", "product_id", "channel_id", "region_id"],
            dropna=False,
            as_index=False,
        )
        .agg(
            promotion_id=("promotion_id", "max"),
            promotion_flag=("promotion_flag", "max"),
            discount_pct=("discount_pct", "max"),
        )
    )


def prepare_price_history(
    price_history_df: pd.DataFrame,
    calendar_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Expand price history into daily price rows by product-channel-region-date.
    """
    _require_columns(
        price_history_df,
        [
            "product_id",
            "channel_id",
            "effective_start_date_id",
            "effective_end_date_id",
        ],
        "fact_price_history",
    )

    output_df = price_history_df.copy()

    if "list_price" not in output_df.columns and "base_price" in output_df.columns:
        output_df["list_price"] = output_df["base_price"]

    if "selling_price" not in output_df.columns and "promo_price" in output_df.columns:
        output_df["selling_price"] = output_df["promo_price"]

    duplicate_columns = output_df.columns[output_df.columns.duplicated()].tolist()
    if duplicate_columns:
            raise ValueError(
                 f"Duplicate columns found in fact_price_history after column standardization: {duplicate_columns}"
            )

    numeric_columns = [
        "product_id",
        "channel_id",
        "effective_start_date_id",
        "effective_end_date_id",
    ]
    optional_numeric_columns = [
        "region_id",
        "list_price",
        "selling_price",
    ]

    for column in numeric_columns:
        output_df[column] = pd.to_numeric(output_df[column], errors="raise")

    for column in optional_numeric_columns:
        if column in output_df.columns:
            output_df[column] = pd.to_numeric(output_df[column], errors="coerce")

    if "region_id" not in output_df.columns:
        output_df["region_id"] = pd.NA
    if "list_price" not in output_df.columns:
        output_df["list_price"] = pd.NA
    if "selling_price" not in output_df.columns:
        output_df["selling_price"] = pd.NA

    output_df = output_df.merge(
        calendar_df[["date_id", "date"]],
        left_on="effective_start_date_id",
        right_on="date_id",
        how="left",
        validate="many_to_one",
    ).rename(columns={"date": "start_date"})

    output_df = output_df.merge(
        calendar_df[["date_id", "date"]],
        left_on="effective_end_date_id",
        right_on="date_id",
        how="left",
        validate="many_to_one",
        suffixes=("", "_end"),
    ).rename(columns={"date": "end_date"})

    if output_df["start_date"].isna().any() or output_df["end_date"].isna().any():
        raise ValueError("Price history records contain invalid date IDs.")

    expanded_rows: list[dict] = []

    for _, row in output_df.iterrows():
        daily_dates = pd.date_range(start=row["start_date"], end=row["end_date"], freq="D")

        for daily_date in daily_dates:
            expanded_rows.append(
                {
                    "date": daily_date,
                    "product_id": int(row["product_id"]),
                    "channel_id": int(row["channel_id"]),
                    "region_id": int(row["region_id"]) if pd.notna(row["region_id"]) else pd.NA,
                    "list_price": float(row["list_price"]) if pd.notna(row["list_price"]) else pd.NA,
                    "selling_price": float(row["selling_price"]) if pd.notna(row["selling_price"]) else pd.NA,
                }
            )

    if not expanded_rows:
        return pd.DataFrame(
            columns=[
                "date",
                "product_id",
                "channel_id",
                "region_id",
                "list_price",
                "selling_price",
            ]
        )

    expanded_df = pd.DataFrame(expanded_rows)

    expanded_df = (
        expanded_df.sort_values(
            ["date", "product_id", "channel_id", "region_id", "selling_price"],
            na_position="last",
        )
        .groupby(
            ["date", "product_id", "channel_id", "region_id"],
            dropna=False,
            as_index=False,
        )
        .tail(1)
    )

    return expanded_df.reset_index(drop=True)


# =========================================================
# Main dataset builder
# =========================================================
def build_training_dataset(config: TrainingDatasetConfig | None = None) -> pd.DataFrame:
    cfg = config or TrainingDatasetConfig()

    calendar_df = prepare_calendar(
        _load_csv(cfg.base_dir / cfg.calendar_file, "dim_calendar")
    )
    product_df = prepare_products(
        _load_csv(cfg.base_dir / cfg.product_file, "dim_product")
    )
    supplier_df = prepare_suppliers(
        _load_csv(cfg.base_dir / cfg.supplier_file, "dim_supplier")
    )
    sales_df = prepare_sales(
        _load_csv(cfg.base_dir / cfg.sales_file, "fact_sales"),
        calendar_df,
    )
    inventory_df = prepare_inventory(
        _load_csv(cfg.base_dir / cfg.inventory_file, "fact_inventory_snapshot"),
        calendar_df,
    )
    promotions_df = prepare_promotions(
        _load_csv(cfg.base_dir / cfg.promotions_file, "fact_promotions"),
        calendar_df,
    )
    price_history_df = prepare_price_history(
        _load_csv(cfg.base_dir / cfg.price_history_file, "fact_price_history"),
        calendar_df,
    )

    logger.info("Building base daily training dataset from sales + inventory backbone.")

    base_df = inventory_df.merge(
        sales_df,
        on=["date", "product_id", "location_type", "location_id"],
        how="left",
        suffixes=("", "_sales"),
    )

    # Resolve region/channel after join
    if "region_id" not in base_df.columns and "region_id_sales" in base_df.columns:
        base_df["region_id"] = base_df["region_id_sales"]

    if "region_id" in base_df.columns and "region_id_sales" in base_df.columns:
        base_df["region_id"] = base_df["region_id"].fillna(base_df["region_id_sales"])

    if "channel_id" not in base_df.columns and "channel_id" in sales_df.columns:
        pass

    if "channel_id" not in base_df.columns:
        base_df["channel_id"] = pd.NA

    if "channel_id_sales" in base_df.columns:
        base_df["channel_id"] = base_df["channel_id"].fillna(base_df["channel_id_sales"])

    if "store_id_sales" in base_df.columns and "store_id" not in base_df.columns:
        base_df["store_id"] = base_df["store_id_sales"]

    for column in [
        "units_sold",
        "gross_sales_amount",
        "net_sales_amount",
        "discount_amount",
    ]:
        if column not in base_df.columns:
            base_df[column] = 0.0
        else:
            base_df[column] = base_df[column].fillna(0.0)

    if "promotion_id" not in base_df.columns:
        base_df["promotion_id"] = pd.NA

    base_df = base_df.merge(
        promotions_df,
        on=["date", "product_id", "channel_id", "region_id"],
        how="left",
        suffixes=("", "_promo"),
    )

    if "promotion_flag" not in base_df.columns:
        base_df["promotion_flag"] = 0
    else:
        base_df["promotion_flag"] = base_df["promotion_flag"].fillna(0).astype(int)

    if "discount_pct" not in base_df.columns:
        base_df["discount_pct"] = 0.0
    else:
        base_df["discount_pct"] = base_df["discount_pct"].fillna(0.0)

    base_df = base_df.merge(
        price_history_df,
        on=["date", "product_id", "channel_id", "region_id"],
        how="left",
    )

    base_df = base_df.merge(
        product_df,
        on="product_id",
        how="left",
        validate="many_to_one",
    )

    base_df = base_df.merge(
        supplier_df,
        on="supplier_id",
        how="left",
        validate="many_to_one",
    )

    if base_df["supplier_id"].isna().any():
        raise ValueError("Some training rows could not map to dim_product / dim_supplier.")

    # =========================================================
    # Standardize price columns after merges
    # =========================================================
    if "list_price" not in base_df.columns:
        if "list_price_x" in base_df.columns and "list_price_y" in base_df.columns:
            base_df["list_price"] = base_df["list_price_x"].fillna(base_df["list_price_y"])
        elif "list_price_x" in base_df.columns:
            base_df["list_price"] = base_df["list_price_x"]
        elif "list_price_y" in base_df.columns:
            base_df["list_price"] = base_df["list_price_y"]

    if "selling_price" not in base_df.columns:
        if "selling_price_x" in base_df.columns and "selling_price_y" in base_df.columns:
            base_df["selling_price"] = base_df["selling_price_x"].fillna(base_df["selling_price_y"])
        elif "selling_price_x" in base_df.columns:
            base_df["selling_price"] = base_df["selling_price_x"]
        elif "selling_price_y" in base_df.columns:
            base_df["selling_price"] = base_df["selling_price_y"]

    if "list_price" not in base_df.columns:
        raise ValueError(
            "Missing standardized 'list_price' after merging price history and product data."
        )

    if "selling_price" not in base_df.columns:
        base_df["selling_price"] = pd.NA

    base_df["selling_price"] = base_df["selling_price"].fillna(base_df["list_price"])

    # Business helper columns
    base_df["is_inventory_row"] = 1
    base_df["inventory_gap_to_reorder"] = (
        base_df["available_qty"] - base_df["reorder_point_qty"]
    )
    base_df["inventory_gap_to_safety_stock"] = (
        base_df["available_qty"] - base_df["safety_stock_qty"]
    )
    base_df["inventory_pressure_flag"] = (
        base_df["available_qty"] <= base_df["reorder_point_qty"]
    ).astype(int)

    base_df["realized_discount_pct"] = 0.0
    valid_price_mask = base_df["list_price"].fillna(0) > 0
    base_df.loc[valid_price_mask, "realized_discount_pct"] = (
        (base_df.loc[valid_price_mask, "list_price"] - base_df.loc[valid_price_mask, "selling_price"])
        / base_df.loc[valid_price_mask, "list_price"]
    ) * 100.0

    # Final column alignment for feature engineering
    final_df = base_df[
        [
            "date",
            "product_id",
            "region_id",
            "channel_id",
            "location_type",
            "location_id",
            "store_id",
            "warehouse_id",
            "units_sold",
            "gross_sales_amount",
            "net_sales_amount",
            "discount_amount",
            "promotion_id",
            "promotion_flag",
            "discount_pct",
            "realized_discount_pct",
            "available_qty",
            "on_hand_qty",
            "reserved_qty",
            "in_transit_qty",
            "damaged_qty",
            "reorder_point_qty",
            "safety_stock_qty",
            "stockout_flag",
            "days_of_cover_estimate",
            "selling_price",
            "list_price",
            "unit_cost",
            "supplier_id",
            "lead_time_days_avg",
            "category",
            "subcategory",
            "brand",
            "inventory_gap_to_reorder",
            "inventory_gap_to_safety_stock",
            "inventory_pressure_flag",
        ]
    ].copy()

    final_df["location_id"] = final_df["location_id"].astype("Int64")
    final_df["store_id"] = final_df["store_id"].astype("Int64")
    final_df["warehouse_id"] = final_df["warehouse_id"].astype("Int64")
    final_df["channel_id"] = final_df["channel_id"].astype("Int64")
    final_df["region_id"] = final_df["region_id"].astype("Int64")
    final_df["supplier_id"] = final_df["supplier_id"].astype("Int64")

    final_df = final_df.sort_values(
        ["product_id", "location_type", "location_id", "channel_id", "date"]
    ).reset_index(drop=True)

    logger.info("Base training dataset built successfully with %s rows.", len(final_df))
    return final_df


def save_training_dataset(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info("Saved training dataset to %s", output_path)


def run(config: TrainingDatasetConfig | None = None) -> Path:
    cfg = config or TrainingDatasetConfig()
    training_df = build_training_dataset(cfg)

    output_path = cfg.output_dir / cfg.output_file
    save_training_dataset(training_df, output_path)
    return output_path


if __name__ == "__main__":
    _setup_logging()
    saved_path = run()
    logger.info("Training base dataset completed: %s", saved_path)