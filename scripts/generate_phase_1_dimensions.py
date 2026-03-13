from __future__ import annotations

from pathlib import Path
from datetime import date
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic"

RNG = np.random.default_rng(42)


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def season_from_month(month: int) -> str:
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    return "Autumn"


def generate_dim_calendar(start_date: str = "2024-01-01", end_date: str = "2025-12-31") -> pd.DataFrame:
    dates = pd.date_range(start=start_date, end=end_date, freq="D")

    holiday_dates = {
        "2024-01-01", "2024-12-25", "2024-11-29", "2024-07-04",
        "2025-01-01", "2025-12-25", "2025-11-28", "2025-07-04"
    }

    df = pd.DataFrame({"full_date": dates})
    df["date_id"] = df["full_date"].dt.strftime("%Y%m%d").astype(int)
    df["day_of_week"] = df["full_date"].dt.day_name()
    df["week_of_year"] = df["full_date"].dt.isocalendar().week.astype(int)
    df["month"] = df["full_date"].dt.month
    df["month_name"] = df["full_date"].dt.month_name()
    df["quarter"] = df["full_date"].dt.quarter
    df["year"] = df["full_date"].dt.year
    df["is_weekend"] = df["full_date"].dt.dayofweek >= 5
    df["is_month_end"] = df["full_date"].dt.is_month_end
    df["season_name"] = df["month"].apply(season_from_month)
    df["holiday_flag"] = df["full_date"].dt.strftime("%Y-%m-%d").isin(holiday_dates)

    return df[
        [
            "date_id", "full_date", "day_of_week", "week_of_year", "month",
            "month_name", "quarter", "year", "is_weekend",
            "is_month_end", "season_name", "holiday_flag"
        ]
    ]


def generate_dim_region() -> pd.DataFrame:
    rows = [
        [1, "NORTH", "North Region", "USA", "urban_mixed", "cold", "medium", True],
        [2, "SOUTH", "South Region", "USA", "suburban_growth", "warm", "high", True],
        [3, "EAST", "East Region", "USA", "dense_metro", "temperate", "low", True],
        [4, "WEST", "West Region", "USA", "coastal_mixed", "dry", "high", True],
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "region_id", "region_code", "region_name", "country_name",
            "market_type", "climate_zone", "demand_volatility", "active_flag"
        ],
    )


def generate_dim_channel() -> pd.DataFrame:
    rows = [
        [1, "STORE", "Store", "offline", False],
        [2, "ECOM", "E-commerce", "online", True],
        [3, "APP", "Mobile App", "online", True],
        [4, "MKTPLC", "Marketplace", "partner_online", True],
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "channel_id", "channel_code", "channel_name", "channel_group", "is_online_flag"
        ],
    )


def generate_dim_store(regions_df: pd.DataFrame) -> pd.DataFrame:
    store_types = ["flagship", "mall", "neighborhood"]
    city_map = {
        1: ["Chicago", "Detroit", "Minneapolis"],
        2: ["Dallas", "Houston", "Atlanta"],
        3: ["New York", "Boston", "Philadelphia"],
        4: ["Los Angeles", "Phoenix", "Seattle"],
    }

    rows = []
    store_id = 1

    for region_id in regions_df["region_id"]:
        for idx, store_type in enumerate(store_types, start=1):
            floor_area = {"flagship": 25000, "mall": 15000, "neighborhood": 8000}[store_type]
            capacity = {"flagship": 4500, "mall": 2800, "neighborhood": 1400}[store_type]

            rows.append(
                [
                    store_id,
                    f"STR{store_id:03d}",
                    f"{regions_df.loc[regions_df.region_id == region_id, 'region_code'].iloc[0]}_{store_type.title()}_{idx}",
                    region_id,
                    store_type,
                    city_map[region_id][idx - 1],
                    pd.Timestamp("2021-01-01") + pd.Timedelta(days=int(RNG.integers(0, 1200))),
                    "active",
                    floor_area + int(RNG.integers(-1200, 1500)),
                    capacity + int(RNG.integers(-250, 300)),
                    f"Manager_{store_id:03d}",
                ]
            )
            store_id += 1

    return pd.DataFrame(
        rows,
        columns=[
            "store_id", "store_code", "store_name", "region_id", "store_type", "city",
            "opening_date", "store_status", "floor_area_sqft", "daily_capacity_units", "manager_name"
        ],
    )


def generate_dim_warehouse(regions_df: pd.DataFrame) -> pd.DataFrame:
    rows = [
        [1, "WH001", "National Distribution Center", 3, "Philadelphia", "national_dc", 250000, "active", "WH_Manager_001"],
        [2, "WH002", "South Regional Warehouse", 2, "Dallas", "regional_dc", 140000, "active", "WH_Manager_002"],
        [3, "WH003", "West Regional Warehouse", 4, "Phoenix", "regional_dc", 135000, "active", "WH_Manager_003"],
    ]

    return pd.DataFrame(
        rows,
        columns=[
            "warehouse_id", "warehouse_code", "warehouse_name", "region_id", "city",
            "warehouse_type", "storage_capacity_units", "operating_status", "manager_name"
        ],
    )


def generate_dim_supplier(n_suppliers: int = 25) -> pd.DataFrame:
    tiers = ["strategic", "preferred", "standard"]
    regions_served = ["North", "South", "East", "West", "National"]

    rows = []
    for supplier_id in range(1, n_suppliers + 1):
        tier = RNG.choice(tiers, p=[0.20, 0.35, 0.45])

        if tier == "strategic":
            lead_time = int(RNG.integers(4, 9))
            on_time = round(float(RNG.uniform(94, 99.5)), 2)
            quality = round(float(RNG.uniform(92, 99)), 2)
        elif tier == "preferred":
            lead_time = int(RNG.integers(7, 15))
            on_time = round(float(RNG.uniform(88, 97)), 2)
            quality = round(float(RNG.uniform(86, 96)), 2)
        else:
            lead_time = int(RNG.integers(10, 22))
            on_time = round(float(RNG.uniform(80, 93)), 2)
            quality = round(float(RNG.uniform(78, 92)), 2)

        contract_start = pd.Timestamp("2023-01-01") + pd.Timedelta(days=int(RNG.integers(0, 500)))
        contract_end = contract_start + pd.Timedelta(days=int(RNG.integers(365, 1095)))

        rows.append(
            [
                supplier_id,
                f"SUP{supplier_id:03d}",
                f"Supplier_{supplier_id:03d}",
                tier,
                RNG.choice(regions_served),
                lead_time,
                on_time,
                quality,
                contract_start.date(),
                contract_end.date(),
                True,
            ]
        )

    return pd.DataFrame(
        rows,
        columns=[
            "supplier_id", "supplier_code", "supplier_name", "supplier_tier", "region_served",
            "lead_time_days_avg", "on_time_rate", "quality_score", "contract_start_date",
            "contract_end_date", "active_flag"
        ],
    )


def generate_dim_product(suppliers_df: pd.DataFrame, n_products: int = 800) -> pd.DataFrame:
    category_map = {
        "Grocery": {
            "subcats": ["Rice", "Pasta", "Canned Goods"],
            "brands": ["NorthFresh", "DailyChoice", "HomeHarvest"],
            "cost_range": (1.50, 8.00),
            "shelf_life": (120, 540),
            "reorder": (40, 120),
            "safety": (20, 60),
        },
        "Beverage": {
            "subcats": ["Juice", "Soda", "Water"],
            "brands": ["SparkSip", "PureDrop", "FreshWave"],
            "cost_range": (0.60, 5.00),
            "shelf_life": (90, 365),
            "reorder": (60, 180),
            "safety": (25, 80),
        },
        "Personal Care": {
            "subcats": ["Soap", "Shampoo", "Toothpaste"],
            "brands": ["CareNest", "GlowLab", "SmilePro"],
            "cost_range": (1.20, 10.00),
            "shelf_life": (365, 1095),
            "reorder": (20, 90),
            "safety": (10, 45),
        },
        "Household": {
            "subcats": ["Cleaner", "Detergent", "Tissues"],
            "brands": ["HomeGuard", "CleanEdge", "SoftNest"],
            "cost_range": (2.00, 12.00),
            "shelf_life": (365, 1095),
            "reorder": (25, 100),
            "safety": (12, 50),
        },
        "Snacks": {
            "subcats": ["Chips", "Biscuits", "Nuts"],
            "brands": ["CrunchBox", "SnackJoy", "NutriPop"],
            "cost_range": (0.80, 6.50),
            "shelf_life": (60, 270),
            "reorder": (50, 160),
            "safety": (20, 70),
        },
        "Frozen": {
            "subcats": ["Frozen Meals", "Ice Cream", "Frozen Vegetables"],
            "brands": ["FrostBite", "ColdKitchen", "FreezeFarm"],
            "cost_range": (2.50, 14.00),
            "shelf_life": (90, 365),
            "reorder": (15, 70),
            "safety": (8, 35),
        },
    }

    categories = list(category_map.keys())
    supplier_ids = suppliers_df["supplier_id"].tolist()

    rows = []
    for product_id in range(1, n_products + 1):
        category = RNG.choice(categories, p=[0.22, 0.18, 0.15, 0.15, 0.20, 0.10])
        meta = category_map[category]

        subcategory = RNG.choice(meta["subcats"])
        brand = RNG.choice(meta["brands"])
        unit_cost = round(float(RNG.uniform(*meta["cost_range"])), 2)

        margin_multiplier = float(RNG.uniform(1.20, 1.75))
        list_price = round(unit_cost * margin_multiplier, 2)

        reorder_point = int(RNG.integers(meta["reorder"][0], meta["reorder"][1] + 1))
        safety_stock = int(RNG.integers(meta["safety"][0], meta["safety"][1] + 1))
        shelf_life = int(RNG.integers(meta["shelf_life"][0], meta["shelf_life"][1] + 1))

        launch_date = pd.Timestamp("2022-01-01") + pd.Timedelta(days=int(RNG.integers(0, 1400)))

        rows.append(
            [
                product_id,
                f"SKU{product_id:05d}",
                f"{brand} {subcategory} {product_id:05d}",
                category,
                subcategory,
                brand,
                unit_cost,
                list_price,
                int(RNG.choice(supplier_ids)),
                shelf_life,
                reorder_point,
                safety_stock,
                launch_date.date(),
                True,
            ]
        )

    return pd.DataFrame(
        rows,
        columns=[
            "product_id", "sku_code", "product_name", "category", "subcategory", "brand",
            "unit_cost", "list_price", "supplier_id", "shelf_life_days", "reorder_point_default",
            "safety_stock_default", "launch_date", "active_flag"
        ],
    )


def generate_dim_customer(regions_df: pd.DataFrame, n_customers: int = 30000) -> pd.DataFrame:
    segments = ["retail_regular", "premium", "wholesale_small", "online_only"]
    segment_probs = [0.52, 0.14, 0.09, 0.25]

    loyalty_by_segment = {
        "retail_regular": ["bronze", "silver"],
        "premium": ["gold", "platinum"],
        "wholesale_small": ["silver", "gold"],
        "online_only": ["bronze", "silver", "gold"],
    }

    ltv_by_segment = {
        "retail_regular": ["low", "medium"],
        "premium": ["high", "very_high"],
        "wholesale_small": ["medium", "high"],
        "online_only": ["low", "medium", "high"],
    }

    preferred_channel_rules = {
        "retail_regular": [1, 2, 3],
        "premium": [1, 2, 3],
        "wholesale_small": [1, 2],
        "online_only": [2, 3, 4],
    }

    region_ids = regions_df["region_id"].tolist()

    rows = []
    for customer_id in range(1, n_customers + 1):
        segment = str(RNG.choice(segments, p=segment_probs))
        region_id = int(RNG.choice(region_ids))
        signup = pd.Timestamp("2022-01-01") + pd.Timedelta(days=int(RNG.integers(0, 1460)))
        loyalty = str(RNG.choice(loyalty_by_segment[segment]))
        ltv_band = str(RNG.choice(ltv_by_segment[segment]))
        preferred_channel_id = int(RNG.choice(preferred_channel_rules[segment]))
        active_flag = bool(RNG.choice([True, False], p=[0.92, 0.08]))

        rows.append(
            [
                customer_id,
                f"CUST{customer_id:07d}",
                segment,
                region_id,
                signup.date(),
                loyalty,
                preferred_channel_id,
                ltv_band,
                active_flag,
            ]
        )

    return pd.DataFrame(
        rows,
        columns=[
            "customer_id", "customer_code", "customer_segment", "region_id",
            "signup_date", "loyalty_tier", "preferred_channel_id",
            "lifetime_value_band", "active_flag"
        ],
    )


def save_csv(df: pd.DataFrame, filename: str) -> None:
    path = OUTPUT_DIR / filename
    df.to_csv(path, index=False)


def main() -> None:
    try:
        ensure_output_dir()

        dim_calendar = generate_dim_calendar()
        dim_region = generate_dim_region()
        dim_channel = generate_dim_channel()
        dim_store = generate_dim_store(dim_region)
        dim_warehouse = generate_dim_warehouse(dim_region)
        dim_supplier = generate_dim_supplier()
        dim_product = generate_dim_product(dim_supplier)
        dim_customer = generate_dim_customer(dim_region)

        save_csv(dim_calendar, "dim_calendar.csv")
        save_csv(dim_region, "dim_region.csv")
        save_csv(dim_store, "dim_store.csv")
        save_csv(dim_warehouse, "dim_warehouse.csv")
        save_csv(dim_channel, "dim_channel.csv")
        save_csv(dim_supplier, "dim_supplier.csv")
        save_csv(dim_product, "dim_product.csv")
        save_csv(dim_customer, "dim_customer.csv")

        print("Phase 1.2 dimension CSV generation completed successfully.")
        print(f"Output directory: {OUTPUT_DIR}")

        print("\nRow counts:")
        print(f"dim_calendar   : {len(dim_calendar):,}")
        print(f"dim_region     : {len(dim_region):,}")
        print(f"dim_store      : {len(dim_store):,}")
        print(f"dim_warehouse  : {len(dim_warehouse):,}")
        print(f"dim_channel    : {len(dim_channel):,}")
        print(f"dim_supplier   : {len(dim_supplier):,}")
        print(f"dim_product    : {len(dim_product):,}")
        print(f"dim_customer   : {len(dim_customer):,}")

    except Exception as exc:
        print(f"Error during Phase 1.2 generation: {exc}")
        raise
    finally:
        print("Phase 1.2 generator script finished.")


if __name__ == "__main__":
    main()