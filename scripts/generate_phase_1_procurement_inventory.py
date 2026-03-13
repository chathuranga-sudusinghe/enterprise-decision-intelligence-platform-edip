from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd


# =========================================================
# Configuration
# =========================================================
RANDOM_SEED = 42
START_DATE = "2024-01-01"
END_DATE = "2025-12-31"

PO_TARGET_ROWS = 18000
SNAPSHOT_FREQUENCY = "MS"   # Month-start snapshots keep Phase 1 volume manageable
BASE_OUTPUT_DIR = Path("data") / "synthetic"

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


@dataclass
class Paths:
    base_dir: Path
    po_csv: Path
    inbound_csv: Path
    movement_csv: Path
    snapshot_csv: Path


def build_paths() -> Paths:
    base_dir = BASE_OUTPUT_DIR
    base_dir.mkdir(parents=True, exist_ok=True)

    return Paths(
        base_dir=base_dir,
        po_csv=base_dir / "fact_purchase_orders.csv",
        inbound_csv=base_dir / "fact_inbound_shipments.csv",
        movement_csv=base_dir / "fact_stock_movements.csv",
        snapshot_csv=base_dir / "fact_inventory_snapshot.csv",
    )


def load_dimensions(base_dir: Path) -> Dict[str, pd.DataFrame]:
    # These dimension CSVs must exist before fact generation starts
    required_files = {
        "calendar": base_dir / "dim_calendar.csv",
        "supplier": base_dir / "dim_supplier.csv",
        "product": base_dir / "dim_product.csv",
        "warehouse": base_dir / "dim_warehouse.csv",
        "store": base_dir / "dim_store.csv",
    }

    missing = [str(path) for path in required_files.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required dimension CSV files:\n" + "\n".join(missing)
        )

    dims = {name: pd.read_csv(path) for name, path in required_files.items()}
    dims["calendar"]["full_date"] = pd.to_datetime(dims["calendar"]["full_date"])
    return dims


def weighted_choice(values: List[int], weights: List[float]) -> int:
    return random.choices(values, weights=weights, k=1)[0]


def cast_required_int_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    # Enforce strict integer types for columns that must never be null
    for col in columns:
        if df[col].isna().any():
            raise ValueError(f"Required integer column '{col}' contains NULL values.")
        df[col] = df[col].astype("int64")
    return df


def cast_nullable_int_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    # Use pandas nullable Int64 so CSV exports 2 instead of 2.0 for optional IDs
    for col in columns:
        df[col] = pd.array(df[col], dtype="Int64")
    return df


def validate_no_float_like_ids(df: pd.DataFrame, columns: List[str], df_name: str) -> None:
    # Guard against float-like ID text such as 2.0 before PostgreSQL loading
    for col in columns:
        non_null_values = df[col].dropna().astype(str)
        bad_values = non_null_values[non_null_values.str.endswith(".0")]
        if not bad_values.empty:
            sample = bad_values.iloc[0]
            raise ValueError(
                f"{df_name}.{col} contains float-like integer text such as '{sample}'."
            )


def generate_purchase_orders(dims: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    calendar = dims["calendar"].copy()
    product = dims["product"].copy()
    warehouse = dims["warehouse"].copy()

    calendar = calendar[
        (calendar["full_date"] >= pd.Timestamp(START_DATE))
        & (calendar["full_date"] <= pd.Timestamp(END_DATE))
    ].copy()

    # Product-level sourcing and replenishment defaults drive PO generation
    product_supplier_map = (
        product[
            [
                "product_id",
                "supplier_id",
                "unit_cost",
                "reorder_point_default",
                "safety_stock_default",
            ]
        ]
        .set_index("product_id")
        .to_dict("index")
    )

    warehouse_ids = warehouse["warehouse_id"].tolist()
    warehouse_weights = [0.50, 0.30, 0.20][: len(warehouse_ids)]
    if len(warehouse_weights) < len(warehouse_ids):
        warehouse_weights = [1 / len(warehouse_ids)] * len(warehouse_ids)

    calendar_dates = calendar["full_date"].tolist()
    calendar_date_ids = dict(zip(calendar["full_date"], calendar["date_id"]))

    po_rows: List[dict] = []
    purchase_order_id = 100000
    po_line_id = 100000000

    status_choices = ["approved", "sent", "partially_received", "received"]
    status_weights = [0.10, 0.20, 0.25, 0.45]

    priority_choices = ["low", "normal", "high", "critical"]
    priority_weights = [0.10, 0.60, 0.22, 0.08]

    buyer_names = ["A. Perera", "K. Silva", "N. Fernando", "M. Jayasuriya"]
    contract_refs = [f"CTR-{i:03d}" for i in range(1, 31)]

    sampled_products = np.random.choice(
        product["product_id"].to_numpy(),
        size=PO_TARGET_ROWS,
        replace=True,
    )
    sampled_dates = np.random.choice(calendar_dates, size=PO_TARGET_ROWS, replace=True)

    for idx in range(PO_TARGET_ROWS):
        product_id = int(sampled_products[idx])
        po_date = pd.Timestamp(sampled_dates[idx])

        prod = product_supplier_map[product_id]
        supplier_id = int(prod["supplier_id"])
        unit_cost = float(prod["unit_cost"])
        reorder_point = int(prod["reorder_point_default"])
        safety_stock = int(prod["safety_stock_default"])

        wh_id = weighted_choice(warehouse_ids, warehouse_weights)
        ordered_qty = max(
            10,
            int(
                np.random.normal(
                    loc=reorder_point + safety_stock,
                    scale=max(5, reorder_point * 0.25),
                )
            ),
        )

        expected_days = random.randint(3, 21)
        expected_receipt_date = po_date + pd.Timedelta(days=expected_days)

        # Clamp to the available calendar range
        if expected_receipt_date not in calendar_date_ids:
            expected_receipt_date = max(
                min(expected_receipt_date, max(calendar_date_ids.keys())),
                min(calendar_date_ids.keys()),
            )

        order_status = random.choices(status_choices, weights=status_weights, k=1)[0]
        priority_level = random.choices(priority_choices, weights=priority_weights, k=1)[0]
        line_amount = round(ordered_qty * unit_cost, 2)

        po_rows.append(
            {
                "po_line_id": po_line_id,
                "purchase_order_id": purchase_order_id,
                "po_number": f"PO-{purchase_order_id}",
                "po_date_id": int(calendar_date_ids[po_date]),
                "expected_receipt_date_id": int(calendar_date_ids[expected_receipt_date]),
                "supplier_id": supplier_id,
                "warehouse_id": int(wh_id),
                "product_id": product_id,
                "ordered_qty": ordered_qty,
                "unit_cost": round(unit_cost, 2),
                "line_amount": line_amount,
                "currency_code": "USD",
                "order_status": order_status,
                "priority_level": priority_level,
                "buyer_name": random.choice(buyer_names),
                "contract_reference": random.choice(contract_refs),
                "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        po_line_id += 1
        if random.random() < 0.72:
            purchase_order_id += 1

    po_df = pd.DataFrame(po_rows).sort_values(["po_date_id", "po_line_id"]).reset_index(drop=True)

    po_df = cast_required_int_columns(
        po_df,
        [
            "po_line_id",
            "purchase_order_id",
            "po_date_id",
            "expected_receipt_date_id",
            "supplier_id",
            "warehouse_id",
            "product_id",
            "ordered_qty",
        ],
    )

    return po_df

def generate_inbound_shipments(po_df: pd.DataFrame, dims: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    calendar = dims["calendar"].copy()
    date_lookup = dict(zip(calendar["date_id"], calendar["full_date"]))
    reverse_lookup = dict(zip(calendar["full_date"], calendar["date_id"]))

    inbound_rows: List[dict] = []
    inbound_shipment_id = 200000
    inbound_line_id = 200000000

    min_calendar_date = min(reverse_lookup.keys())
    max_calendar_date = max(reverse_lookup.keys())

    for _, row in po_df.iterrows():
        po_date = pd.Timestamp(date_lookup[int(row["po_date_id"])])
        expected_arrival_date = pd.Timestamp(date_lookup[int(row["expected_receipt_date_id"])])

        shipped_qty = int(row["ordered_qty"])

        delay_days = max(
            0,
            int(
                np.random.choice(
                    [0, 0, 0, 1, 2, 3, 5, 7],
                    p=[0.30, 0.20, 0.15, 0.12, 0.10, 0.07, 0.04, 0.02],
                )
            ),
        )

        actual_arrival_date = expected_arrival_date + pd.Timedelta(days=delay_days)

        # Keep actual arrival date inside calendar range
        if actual_arrival_date not in reverse_lookup:
            actual_arrival_date = min(max(actual_arrival_date, min_calendar_date), max_calendar_date)

        shipped_date = min(po_date + pd.Timedelta(days=random.randint(1, 4)), actual_arrival_date)

        # Keep shipped date inside calendar lookup
        if shipped_date not in reverse_lookup:
            shipped_date = po_date
            if shipped_date not in reverse_lookup:
                shipped_date = min(max(shipped_date, min_calendar_date), max_calendar_date)

        reject_rate = np.random.choice(
            [0.00, 0.00, 0.01, 0.02, 0.03],
            p=[0.45, 0.25, 0.15, 0.10, 0.05],
        )
        damage_rate = np.random.choice(
            [0.00, 0.00, 0.01, 0.02],
            p=[0.60, 0.20, 0.15, 0.05],
        )

        rejected_qty = min(shipped_qty, int(round(shipped_qty * reject_rate)))
        damaged_qty = min(shipped_qty - rejected_qty, int(round(shipped_qty * damage_rate)))
        received_qty = max(0, shipped_qty - rejected_qty)

        if rejected_qty > 0:
            shipment_status = "rejected"
            qc_pass_flag = False
        elif delay_days > 0 and received_qty < shipped_qty:
            shipment_status = "partially_received"
            qc_pass_flag = True
        elif delay_days > 0:
            shipment_status = "delayed"
            qc_pass_flag = True
        else:
            shipment_status = "received"
            qc_pass_flag = True

        inbound_rows.append(
            {
                "inbound_shipment_line_id": inbound_line_id,
                "inbound_shipment_id": inbound_shipment_id,
                "shipment_number": f"SHIP-{inbound_shipment_id}",
                "purchase_order_id": int(row["purchase_order_id"]),
                "po_line_id": int(row["po_line_id"]),
                "supplier_id": int(row["supplier_id"]),
                "warehouse_id": int(row["warehouse_id"]),
                "product_id": int(row["product_id"]),
                "shipped_date_id": int(reverse_lookup[pd.Timestamp(shipped_date)]),
                "expected_arrival_date_id": int(row["expected_receipt_date_id"]),
                "actual_arrival_date_id": int(reverse_lookup[pd.Timestamp(actual_arrival_date)]),
                "received_date_id": int(reverse_lookup[pd.Timestamp(actual_arrival_date)]),
                "shipped_qty": shipped_qty,
                "received_qty": received_qty,
                "rejected_qty": rejected_qty,
                "damaged_qty": damaged_qty,
                "shipment_status": shipment_status,
                "delay_days": delay_days,
                "carrier_name": random.choice(
                    ["DHL Supply", "Maersk Logistics", "UPS Freight", "FedEx Trade"]
                ),
                "transport_mode": random.choice(["road", "sea", "air"]),
                "qc_pass_flag": qc_pass_flag,
                "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        inbound_line_id += 1
        inbound_shipment_id += 1

    inbound_df = (
        pd.DataFrame(inbound_rows)
        .sort_values(["expected_arrival_date_id", "inbound_shipment_line_id"])
        .reset_index(drop=True)
    )

    inbound_df = cast_required_int_columns(
        inbound_df,
        [
            "inbound_shipment_line_id",
            "inbound_shipment_id",
            "purchase_order_id",
            "po_line_id",
            "supplier_id",
            "warehouse_id",
            "product_id",
            "shipped_date_id",
            "expected_arrival_date_id",
            "actual_arrival_date_id",
            "received_date_id",
            "shipped_qty",
            "received_qty",
            "rejected_qty",
            "damaged_qty",
            "delay_days",
        ],
    )

    return inbound_df

def generate_stock_movements(
    inbound_df: pd.DataFrame,
    dims: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    stores = dims["store"].copy()

    store_ids = stores["store_id"].tolist()

    movement_rows: List[dict] = []
    stock_movement_id = 300000000

    for _, row in inbound_df.iterrows():
        received_qty = int(row["received_qty"])
        damaged_qty = int(row["damaged_qty"])

        # Receipt increases warehouse stock
        if received_qty > 0:
            movement_rows.append(
                {
                    "stock_movement_id": stock_movement_id,
                    "movement_date_id": int(row["received_date_id"]),
                    "product_id": int(row["product_id"]),
                    "location_type": "warehouse",
                    "store_id": None,
                    "warehouse_id": int(row["warehouse_id"]),
                    "movement_type": "receipt",
                    "movement_reason": "supplier_receipt",
                    "quantity_change": received_qty,
                    "reference_type": "inbound_shipment",
                    "reference_id": int(row["inbound_shipment_id"]),
                    "source_location_type": None,
                    "source_store_id": None,
                    "source_warehouse_id": None,
                    "target_location_type": "warehouse",
                    "target_store_id": None,
                    "target_warehouse_id": int(row["warehouse_id"]),
                    "unit_cost": None,
                    "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            stock_movement_id += 1

        # Damage reduces available warehouse stock
        if damaged_qty > 0:
            movement_rows.append(
                {
                    "stock_movement_id": stock_movement_id,
                    "movement_date_id": int(row["received_date_id"]),
                    "product_id": int(row["product_id"]),
                    "location_type": "warehouse",
                    "store_id": None,
                    "warehouse_id": int(row["warehouse_id"]),
                    "movement_type": "damage",
                    "movement_reason": "inbound_damage",
                    "quantity_change": -damaged_qty,
                    "reference_type": "inbound_shipment",
                    "reference_id": int(row["inbound_shipment_id"]),
                    "source_location_type": "warehouse",
                    "source_store_id": None,
                    "source_warehouse_id": int(row["warehouse_id"]),
                    "target_location_type": None,
                    "target_store_id": None,
                    "target_warehouse_id": None,
                    "unit_cost": None,
                    "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            stock_movement_id += 1

        # A portion of received stock is pushed from warehouse to store
        if received_qty > 0 and random.random() < 0.75:
            transfer_qty = max(1, int(round(received_qty * np.random.uniform(0.25, 0.75))))
            target_store = int(random.choice(store_ids))

            movement_rows.append(
                {
                    "stock_movement_id": stock_movement_id,
                    "movement_date_id": int(row["received_date_id"]),
                    "product_id": int(row["product_id"]),
                    "location_type": "warehouse",
                    "store_id": None,
                    "warehouse_id": int(row["warehouse_id"]),
                    "movement_type": "transfer_out",
                    "movement_reason": "warehouse_to_store_replenishment",
                    "quantity_change": -transfer_qty,
                    "reference_type": "inbound_shipment",
                    "reference_id": int(row["inbound_shipment_id"]),
                    "source_location_type": "warehouse",
                    "source_store_id": None,
                    "source_warehouse_id": int(row["warehouse_id"]),
                    "target_location_type": "store",
                    "target_store_id": target_store,
                    "target_warehouse_id": None,
                    "unit_cost": None,
                    "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            stock_movement_id += 1

            movement_rows.append(
                {
                    "stock_movement_id": stock_movement_id,
                    "movement_date_id": int(row["received_date_id"]),
                    "product_id": int(row["product_id"]),
                    "location_type": "store",
                    "store_id": target_store,
                    "warehouse_id": None,
                    "movement_type": "transfer_in",
                    "movement_reason": "warehouse_to_store_replenishment",
                    "quantity_change": transfer_qty,
                    "reference_type": "inbound_shipment",
                    "reference_id": int(row["inbound_shipment_id"]),
                    "source_location_type": "warehouse",
                    "source_store_id": None,
                    "source_warehouse_id": int(row["warehouse_id"]),
                    "target_location_type": "store",
                    "target_store_id": target_store,
                    "target_warehouse_id": None,
                    "unit_cost": None,
                    "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            stock_movement_id += 1

    movement_df = pd.DataFrame(movement_rows).sort_values(
        ["movement_date_id", "stock_movement_id"]
    ).reset_index(drop=True)

    movement_df = cast_required_int_columns(
        movement_df,
        [
            "stock_movement_id",
            "movement_date_id",
            "product_id",
            "quantity_change",
        ],
    )

    movement_df = cast_nullable_int_columns(
        movement_df,
        [
            "store_id",
            "warehouse_id",
            "reference_id",
            "source_store_id",
            "source_warehouse_id",
            "target_store_id",
            "target_warehouse_id",
        ],
    )

    return movement_df


def build_inventory_snapshots(
    inbound_df: pd.DataFrame,
    movement_df: pd.DataFrame,
    dims: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    calendar = dims["calendar"].copy()
    products = dims["product"].copy()
    stores = dims["store"].copy()
    warehouses = dims["warehouse"].copy()

    products_small = products[
        ["product_id", "reorder_point_default", "safety_stock_default"]
    ].copy()

    snapshot_dates = pd.date_range(START_DATE, END_DATE, freq=SNAPSHOT_FREQUENCY)
    date_to_id = dict(zip(calendar["full_date"], calendar["date_id"]))

    movement_store = movement_df[
        movement_df["location_type"] == "store"
    ].groupby(["movement_date_id", "product_id", "store_id"], as_index=False)["quantity_change"].sum()

    movement_wh = movement_df[
        movement_df["location_type"] == "warehouse"
    ].groupby(["movement_date_id", "product_id", "warehouse_id"], as_index=False)["quantity_change"].sum()

    snapshot_rows: List[dict] = []
    snapshot_id = 400000000

    chosen_products = products_small["product_id"].sample(
        n=min(250, len(products_small)),
        random_state=RANDOM_SEED,
    ).tolist()

    for snapshot_date in snapshot_dates:
        snapshot_date = pd.Timestamp(snapshot_date)
        if snapshot_date not in date_to_id:
            continue

        snapshot_date_id = int(date_to_id[snapshot_date])

        for wh_id in warehouses["warehouse_id"].tolist():
            wh_moves = movement_wh[
                (movement_wh["movement_date_id"] <= snapshot_date_id)
                & (movement_wh["warehouse_id"] == wh_id)
            ]

            wh_bal = wh_moves.groupby("product_id")["quantity_change"].sum().reindex(
                chosen_products, fill_value=0
            )

            for product_id in chosen_products:
                prod = products_small.loc[products_small["product_id"] == product_id].iloc[0]

                on_hand = max(0, int(wh_bal.get(product_id, 0) + np.random.randint(0, 20)))
                reserved = max(0, int(on_hand * np.random.uniform(0.00, 0.15)))
                available = max(0, on_hand - reserved)
                in_transit = max(0, int(np.random.choice([0, 0, 0, 5, 10, 20])))
                damaged = max(0, int(np.random.choice([0, 0, 1, 2, 3])))
                reorder_point = int(prod["reorder_point_default"])
                safety_stock = int(prod["safety_stock_default"])

                if available == 0:
                    status = "stockout"
                elif available <= safety_stock:
                    status = "low_stock"
                elif available >= reorder_point * 2:
                    status = "overstock"
                else:
                    status = "healthy"

                snapshot_rows.append(
                    {
                        "inventory_snapshot_id": snapshot_id,
                        "snapshot_date_id": snapshot_date_id,
                        "product_id": int(product_id),
                        "location_type": "warehouse",
                        "store_id": None,
                        "warehouse_id": int(wh_id),
                        "on_hand_qty": on_hand,
                        "reserved_qty": reserved,
                        "available_qty": available,
                        "in_transit_qty": in_transit,
                        "damaged_qty": damaged,
                        "reorder_point_qty": reorder_point,
                        "safety_stock_qty": safety_stock,
                        "inventory_status": status,
                        "stockout_flag": available == 0,
                        "days_of_cover_estimate": round(float(np.random.uniform(3, 45)), 2),
                        "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
                snapshot_id += 1

        for store_id in stores["store_id"].tolist():
            st_moves = movement_store[
                (movement_store["movement_date_id"] <= snapshot_date_id)
                & (movement_store["store_id"] == store_id)
            ]

            st_bal = st_moves.groupby("product_id")["quantity_change"].sum().reindex(
                chosen_products, fill_value=0
            )

            for product_id in chosen_products:
                prod = products_small.loc[products_small["product_id"] == product_id].iloc[0]

                baseline = max(0, int(st_bal.get(product_id, 0)))
                synthetic_sales_drain = max(0, int(np.random.poisson(lam=8)))
                on_hand = max(0, baseline - synthetic_sales_drain + np.random.randint(0, 8))
                reserved = max(0, int(on_hand * np.random.uniform(0.00, 0.08)))
                available = max(0, on_hand - reserved)
                in_transit = max(0, int(np.random.choice([0, 0, 3, 5])))
                damaged = max(0, int(np.random.choice([0, 0, 1, 2])))
                reorder_point = int(prod["reorder_point_default"])
                safety_stock = int(prod["safety_stock_default"])

                if available == 0:
                    status = "stockout"
                elif available <= safety_stock:
                    status = "low_stock"
                elif available >= reorder_point * 2:
                    status = "overstock"
                else:
                    status = "healthy"

                snapshot_rows.append(
                    {
                        "inventory_snapshot_id": snapshot_id,
                        "snapshot_date_id": snapshot_date_id,
                        "product_id": int(product_id),
                        "location_type": "store",
                        "store_id": int(store_id),
                        "warehouse_id": None,
                        "on_hand_qty": on_hand,
                        "reserved_qty": reserved,
                        "available_qty": available,
                        "in_transit_qty": in_transit,
                        "damaged_qty": damaged,
                        "reorder_point_qty": reorder_point,
                        "safety_stock_qty": safety_stock,
                        "inventory_status": status,
                        "stockout_flag": available == 0,
                        "days_of_cover_estimate": round(float(np.random.uniform(1, 25)), 2),
                        "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
                snapshot_id += 1

    snapshot_df = pd.DataFrame(snapshot_rows).sort_values(
        ["snapshot_date_id", "location_type", "inventory_snapshot_id"]
    ).reset_index(drop=True)

    snapshot_df = cast_required_int_columns(
        snapshot_df,
        [
            "inventory_snapshot_id",
            "snapshot_date_id",
            "product_id",
            "on_hand_qty",
            "reserved_qty",
            "available_qty",
            "in_transit_qty",
            "damaged_qty",
            "reorder_point_qty",
            "safety_stock_qty",
        ],
    )

    snapshot_df = cast_nullable_int_columns(
        snapshot_df,
        ["store_id", "warehouse_id"],
    )

    return snapshot_df


def validate_outputs(
    po_df: pd.DataFrame,
    inbound_df: pd.DataFrame,
    movement_df: pd.DataFrame,
    snapshot_df: pd.DataFrame,
) -> None:
    validate_no_float_like_ids(
        po_df,
        ["po_line_id", "purchase_order_id", "supplier_id", "warehouse_id", "product_id"],
        "fact_purchase_orders",
    )

    validate_no_float_like_ids(
        inbound_df,
        [
            "inbound_shipment_line_id",
            "inbound_shipment_id",
            "purchase_order_id",
            "po_line_id",
            "supplier_id",
            "warehouse_id",
            "product_id",
        ],
        "fact_inbound_shipments",
    )

    validate_no_float_like_ids(
        movement_df,
        [
            "stock_movement_id",
            "movement_date_id",
            "product_id",
            "store_id",
            "warehouse_id",
            "reference_id",
            "source_store_id",
            "source_warehouse_id",
            "target_store_id",
            "target_warehouse_id",
        ],
        "fact_stock_movements",
    )

    validate_no_float_like_ids(
        snapshot_df,
        [
            "inventory_snapshot_id",
            "snapshot_date_id",
            "product_id",
            "store_id",
            "warehouse_id",
        ],
        "fact_inventory_snapshot",
    )


def save_outputs(
    po_df: pd.DataFrame,
    inbound_df: pd.DataFrame,
    movement_df: pd.DataFrame,
    snapshot_df: pd.DataFrame,
    paths: Paths,
) -> None:
    po_df.to_csv(paths.po_csv, index=False)
    inbound_df.to_csv(paths.inbound_csv, index=False)
    movement_df.to_csv(paths.movement_csv, index=False)
    snapshot_df.to_csv(paths.snapshot_csv, index=False)


def print_summary(
    po_df: pd.DataFrame,
    inbound_df: pd.DataFrame,
    movement_df: pd.DataFrame,
    snapshot_df: pd.DataFrame,
    paths: Paths,
) -> None:
    print("\nPhase 1.5B generation completed successfully.")
    print(f"Output folder: {paths.base_dir}")
    print(f"fact_purchase_orders.csv      : {len(po_df):,}")
    print(f"fact_inbound_shipments.csv    : {len(inbound_df):,}")
    print(f"fact_stock_movements.csv      : {len(movement_df):,}")
    print(f"fact_inventory_snapshot.csv   : {len(snapshot_df):,}")


def main() -> None:
    try:
        paths = build_paths()
        dims = load_dimensions(paths.base_dir)

        po_df = generate_purchase_orders(dims)
        inbound_df = generate_inbound_shipments(po_df, dims)
        movement_df = generate_stock_movements(inbound_df, dims)
        snapshot_df = build_inventory_snapshots(inbound_df, movement_df, dims)

        validate_outputs(po_df, inbound_df, movement_df, snapshot_df)
        save_outputs(po_df, inbound_df, movement_df, snapshot_df, paths)
        print_summary(po_df, inbound_df, movement_df, snapshot_df, paths)

    except Exception as exc:
        print(f"Error during Phase 1.5B generation: {exc}")
        raise
    finally:
        print("Phase 1.5B generator script finished.")


if __name__ == "__main__":
    main()