from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# =========================================================
# Logging
# =========================================================
logger = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


# =========================================================
# Constants
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
FORECASTS_DIR = ARTIFACTS_DIR / "forecasts"
REPORTS_DIR = ARTIFACTS_DIR / "reports"

DATA_DIR = PROJECT_ROOT / "data"
SYNTHETIC_DIR = DATA_DIR / "synthetic"

FORECAST_INPUT_CANDIDATES = [
    FORECASTS_DIR / "demand_forecast_scored.csv",
]

INVENTORY_CANDIDATES = [
    SYNTHETIC_DIR / "fact_inventory_snapshot.csv",
]

INBOUND_CANDIDATES = [
    SYNTHETIC_DIR / "fact_inbound_shipments.csv",
]

PRODUCT_CANDIDATES = [
    SYNTHETIC_DIR / "dim_product.csv",
]

SUPPLIER_CANDIDATES = [
    SYNTHETIC_DIR / "dim_supplier.csv",
]

OUTPUT_RECOMMENDATIONS_PATH = FORECASTS_DIR / "replenishment_recommendations.csv"
OUTPUT_SUMMARY_PATH = FORECASTS_DIR / "replenishment_recommendation_summary.json"


# =========================================================
# Policy assumptions
# =========================================================
DEFAULT_COVERAGE_TARGET_DAYS = 14.0
MIN_ORDER_QTY = 1
LOW_PRIORITY_THRESHOLD = 0.95
MEDIUM_PRIORITY_THRESHOLD = 0.80
HIGH_PRIORITY_THRESHOLD = 0.50


# =========================================================
# Dataclasses
# =========================================================
@dataclass
class PipelinePaths:
    forecast_path: Path
    inventory_path: Path
    inbound_path: Optional[Path]
    product_path: Optional[Path]
    supplier_path: Optional[Path]
    output_recommendations_path: Path
    output_summary_path: Path


# =========================================================
# File helpers
# =========================================================
def ensure_output_dirs() -> None:
    FORECASTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def first_existing_path(candidates: List[Path], required: bool = True) -> Optional[Path]:
    for candidate in candidates:
        if candidate.exists():
            return candidate

    if required:
        raise FileNotFoundError(
            "Expected one of these files, but none were found: "
            + ", ".join(str(path) for path in candidates)
        )

    return None


def build_paths() -> PipelinePaths:
    return PipelinePaths(
        forecast_path=first_existing_path(FORECAST_INPUT_CANDIDATES, required=True),
        inventory_path=first_existing_path(INVENTORY_CANDIDATES, required=True),
        inbound_path=first_existing_path(INBOUND_CANDIDATES, required=False),
        product_path=first_existing_path(PRODUCT_CANDIDATES, required=False),
        supplier_path=first_existing_path(SUPPLIER_CANDIDATES, required=False),
        output_recommendations_path=OUTPUT_RECOMMENDATIONS_PATH,
        output_summary_path=OUTPUT_SUMMARY_PATH,
    )


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


# =========================================================
# Load + normalize
# =========================================================
def normalize_forecast_df(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    required_columns = ["product_id", "predicted_units"]
    missing = [col for col in required_columns if col not in working.columns]
    if missing:
        raise ValueError(f"Forecast file is missing required columns: {missing}")

    if "location_id" not in working.columns:
        if "store_id" in working.columns:
            working["location_id"] = working["store_id"]
        elif "warehouse_id" in working.columns:
            working["location_id"] = working["warehouse_id"]
        else:
            raise ValueError(
                "Forecast file must contain one of: location_id, store_id, warehouse_id"
            )

    if "forecast_date" in working.columns:
        working["forecast_date"] = pd.to_datetime(working["forecast_date"], errors="coerce")
    elif "date" in working.columns:
        working["forecast_date"] = pd.to_datetime(working["date"], errors="coerce")
    else:
        working["forecast_date"] = pd.NaT

    working["predicted_units"] = pd.to_numeric(
        working["predicted_units"], errors="coerce"
    ).fillna(0.0)

    keep_cols = [
        col
        for col in [
            "forecast_date",
            "target_date",
            "product_id",
            "location_id",
            "region_id",
            "store_id",
            "warehouse_id",
            "channel_id",
            "predicted_units",
            "model_name",
            "model_version",
        ]
        if col in working.columns
    ]

    working = working[keep_cols].copy()
    working["product_id"] = pd.to_numeric(working["product_id"], errors="coerce")
    working["location_id"] = pd.to_numeric(working["location_id"], errors="coerce")
    working = working.dropna(subset=["product_id", "location_id"]).reset_index(drop=True)

    working["product_id"] = working["product_id"].astype(int)
    working["location_id"] = working["location_id"].astype(int)

    return working


def normalize_inventory_df(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    date_candidates = [
        "snapshot_date",
        "inventory_date",
        "date",
        "as_of_date",
    ]
    quantity_candidates = [
        "available_qty",
        "on_hand_qty",
        "ending_on_hand_qty",
    ]

    location_col = None
    for candidate in ["location_id", "store_id", "warehouse_id"]:
        if candidate in working.columns:
            location_col = candidate
            break

    if location_col is None:
        raise ValueError(
            "Inventory file must contain one of: location_id, store_id, warehouse_id"
        )

    qty_col = None
    for candidate in quantity_candidates:
        if candidate in working.columns:
            qty_col = candidate
            break

    if qty_col is None:
        raise ValueError(
            "Inventory file must contain one of: available_qty, on_hand_qty, ending_on_hand_qty"
        )

    date_col = None
    for candidate in date_candidates:
        if candidate in working.columns:
            date_col = candidate
            break

    if "product_id" not in working.columns:
        raise ValueError("Inventory file must contain product_id")

    if location_col != "location_id":
        working["location_id"] = working[location_col]

    working["product_id"] = pd.to_numeric(working["product_id"], errors="coerce")
    working["location_id"] = pd.to_numeric(working["location_id"], errors="coerce")
    working["current_available_qty"] = pd.to_numeric(working[qty_col], errors="coerce").fillna(0.0)

    if date_col is not None:
        working["snapshot_date"] = pd.to_datetime(working[date_col], errors="coerce")
        working = working.sort_values(["product_id", "location_id", "snapshot_date"])
        working = working.groupby(["product_id", "location_id"], as_index=False).tail(1)
    else:
        working["snapshot_date"] = pd.NaT

    keep_cols = [
        col
        for col in [
            "snapshot_date",
            "product_id",
            "location_id",
            "current_available_qty",
            "reorder_point_qty",
            "safety_stock_qty",
            "days_of_cover_estimate",
            "region_id",
            "store_id",
            "warehouse_id",
        ]
        if col in working.columns
    ]

    working = working[keep_cols].dropna(subset=["product_id", "location_id"]).reset_index(drop=True)
    working["product_id"] = working["product_id"].astype(int)
    working["location_id"] = working["location_id"].astype(int)

    return working


def normalize_inbound_df(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    if "product_id" not in working.columns:
        raise ValueError("Inbound shipments file must contain product_id")

    location_col = None
    for candidate in ["location_id", "warehouse_id", "store_id"]:
        if candidate in working.columns:
            location_col = candidate
            break

    qty_col = None
    for candidate in ["expected_qty", "inbound_qty", "shipment_qty", "received_qty"]:
        if candidate in working.columns:
            qty_col = candidate
            break

    eta_col = None
    for candidate in ["expected_arrival_date", "arrival_date", "eta_date", "receipt_date"]:
        if candidate in working.columns:
            eta_col = candidate
            break

    if location_col is None or qty_col is None:
        logger.warning("Inbound shipment file does not have expected location/quantity fields.")
        return pd.DataFrame(columns=["product_id", "location_id", "open_inbound_qty"])

    if location_col != "location_id":
        working["location_id"] = working[location_col]

    working["product_id"] = pd.to_numeric(working["product_id"], errors="coerce")
    working["location_id"] = pd.to_numeric(working["location_id"], errors="coerce")
    working["open_inbound_qty"] = pd.to_numeric(working[qty_col], errors="coerce").fillna(0.0)

    if eta_col is not None:
        working["eta_date"] = pd.to_datetime(working[eta_col], errors="coerce")
        today = pd.Timestamp.utcnow().normalize()
        working = working.loc[(working["eta_date"].isna()) | (working["eta_date"] >= today)].copy()

    grouped = (
        working.dropna(subset=["product_id", "location_id"])
        .groupby(["product_id", "location_id"], as_index=False)["open_inbound_qty"]
        .sum()
    )

    grouped["product_id"] = grouped["product_id"].astype(int)
    grouped["location_id"] = grouped["location_id"].astype(int)

    return grouped


def normalize_product_df(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    if "product_id" not in working.columns:
        return pd.DataFrame(columns=["product_id"])

    keep_cols = [
        col
        for col in [
            "product_id",
            "product_name",
            "category",
            "subcategory",
            "brand",
            "supplier_id",
            "reorder_point_qty",
            "safety_stock_qty",
        ]
        if col in working.columns
    ]

    working = working[keep_cols].copy()
    working["product_id"] = pd.to_numeric(working["product_id"], errors="coerce")
    working = working.dropna(subset=["product_id"]).reset_index(drop=True)
    working["product_id"] = working["product_id"].astype(int)

    return working


def normalize_supplier_df(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    if "supplier_id" not in working.columns:
        return pd.DataFrame(columns=["supplier_id"])

    keep_cols = [
        col
        for col in [
            "supplier_id",
            "supplier_name",
            "lead_time_days_avg",
        ]
        if col in working.columns
    ]

    working = working[keep_cols].copy()
    working["supplier_id"] = pd.to_numeric(working["supplier_id"], errors="coerce")
    working = working.dropna(subset=["supplier_id"]).reset_index(drop=True)
    working["supplier_id"] = working["supplier_id"].astype(int)

    if "lead_time_days_avg" in working.columns:
        working["lead_time_days_avg"] = pd.to_numeric(
            working["lead_time_days_avg"], errors="coerce"
        )

    return working


# =========================================================
# Recommendation logic
# =========================================================
def attach_reference_data(
    forecast_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    inbound_df: pd.DataFrame,
    product_df: Optional[pd.DataFrame],
    supplier_df: Optional[pd.DataFrame],
) -> pd.DataFrame:
    merged = forecast_df.merge(
        inventory_df,
        how="left",
        on=["product_id", "location_id"],
        suffixes=("", "_inventory"),
    )

    merged = merged.merge(
        inbound_df,
        how="left",
        on=["product_id", "location_id"],
    )

    if product_df is not None and not product_df.empty:
        merged = merged.merge(product_df, how="left", on="product_id")

    if supplier_df is not None and not supplier_df.empty and "supplier_id" in merged.columns:
        merged = merged.merge(supplier_df, how="left", on="supplier_id", suffixes=("", "_supplier"))

    merged["current_available_qty"] = pd.to_numeric(
        merged.get("current_available_qty"), errors="coerce"
    ).fillna(0.0)

    merged["open_inbound_qty"] = pd.to_numeric(
        merged.get("open_inbound_qty"), errors="coerce"
    ).fillna(0.0)

    merged["predicted_units"] = pd.to_numeric(
        merged.get("predicted_units"), errors="coerce"
    ).fillna(0.0)

    merged["reorder_point_qty"] = pd.to_numeric(
        merged.get("reorder_point_qty"), errors="coerce"
    )
    merged["safety_stock_qty"] = pd.to_numeric(
        merged.get("safety_stock_qty"), errors="coerce"
    )
    merged["lead_time_days_avg"] = pd.to_numeric(
        merged.get("lead_time_days_avg"), errors="coerce"
    )

    merged["reorder_point_qty"] = merged["reorder_point_qty"].fillna(
        np.maximum(merged["predicted_units"] * 0.8, 1.0)
    )
    merged["safety_stock_qty"] = merged["safety_stock_qty"].fillna(
        np.maximum(merged["predicted_units"] * 0.5, 1.0)
    )
    merged["lead_time_days_avg"] = merged["lead_time_days_avg"].fillna(7.0)

    merged["inventory_position_qty"] = (
        merged["current_available_qty"] + merged["open_inbound_qty"]
    )

    merged["net_inventory_after_forecast_qty"] = (
        merged["inventory_position_qty"] - merged["predicted_units"]
    )

    merged["target_stock_qty"] = (
        np.maximum(merged["predicted_units"], 0.0)
        + merged["safety_stock_qty"]
    )

    merged["recommended_order_qty"] = np.ceil(
        np.maximum(
            merged["target_stock_qty"] - merged["inventory_position_qty"],
            0.0,
        )
    )

    merged["recommended_order_qty"] = merged["recommended_order_qty"].astype(int)
    merged.loc[
        (merged["recommended_order_qty"] > 0)
        & (merged["recommended_order_qty"] < MIN_ORDER_QTY),
        "recommended_order_qty",
    ] = MIN_ORDER_QTY

    merged["coverage_ratio"] = np.where(
        merged["target_stock_qty"] > 0,
        merged["inventory_position_qty"] / merged["target_stock_qty"],
        1.0,
    )

    merged["stockout_risk_score"] = np.clip(
        1.0 - np.clip(merged["coverage_ratio"], 0.0, 1.0),
        0.0,
        1.0,
    )

    merged["expected_service_level"] = np.clip(
        merged["coverage_ratio"],
        0.0,
        1.0,
    )

    merged["days_of_cover_post_replenishment"] = np.where(
        merged["predicted_units"] > 0,
        (
            merged["inventory_position_qty"] + merged["recommended_order_qty"]
        ) / np.maximum(merged["predicted_units"], 1e-6),
        DEFAULT_COVERAGE_TARGET_DAYS,
    )

    return merged


def assign_priority_and_reason(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    priority_list: List[str] = []
    action_list: List[str] = []
    reason_code_list: List[str] = []
    reason_text_list: List[str] = []

    for _, row in working.iterrows():
        recommended_qty = int(row["recommended_order_qty"])
        coverage_ratio = float(row["coverage_ratio"])
        lead_time_days = float(row["lead_time_days_avg"])
        stockout_risk = float(row["stockout_risk_score"])
        inventory_position = float(row["inventory_position_qty"])
        reorder_point = float(row["reorder_point_qty"])

        if recommended_qty <= 0:
            priority = "none"
            action = "monitor"
            reason_code = "SUFFICIENT_COVERAGE"
            reason_text = (
                "Inventory position and inbound supply are sufficient for the current forecast."
            )
        elif inventory_position <= 0 or stockout_risk >= HIGH_PRIORITY_THRESHOLD:
            priority = "high"
            action = "urgent_replenish"
            reason_code = "IMMEDIATE_STOCKOUT_RISK"
            reason_text = (
                "Inventory position is critically low versus forecast demand and safety stock."
            )
        elif coverage_ratio < MEDIUM_PRIORITY_THRESHOLD or lead_time_days >= 10:
            priority = "medium"
            action = "replenish"
            reason_code = "BELOW_TARGET_COVERAGE"
            reason_text = (
                "Projected inventory coverage is below target and replenishment is recommended."
            )
        elif inventory_position < reorder_point:
            priority = "medium"
            action = "replenish"
            reason_code = "BELOW_REORDER_POINT"
            reason_text = "Inventory position has fallen below reorder point."
        else:
            priority = "low"
            action = "review"
            reason_code = "PLANNER_REVIEW_RECOMMENDED"
            reason_text = (
                "A small replenishment gap exists, but the item should be planner-reviewed first."
            )

        priority_list.append(priority)
        action_list.append(action)
        reason_code_list.append(reason_code)
        reason_text_list.append(reason_text)

    working["priority"] = priority_list
    working["recommended_action"] = action_list
    working["reason_code"] = reason_code_list
    working["reason_text"] = reason_text_list

    return working


def build_recommendation_output(df: pd.DataFrame) -> pd.DataFrame:
    output_columns = [
        "forecast_date",
        "target_date",
        "product_id",
        "location_id",
        "region_id",
        "store_id",
        "warehouse_id",
        "channel_id",
        "category",
        "subcategory",
        "brand",
        "supplier_id",
        "supplier_name",
        "predicted_units",
        "current_available_qty",
        "open_inbound_qty",
        "inventory_position_qty",
        "reorder_point_qty",
        "safety_stock_qty",
        "target_stock_qty",
        "recommended_order_qty",
        "priority",
        "recommended_action",
        "reason_code",
        "reason_text",
        "lead_time_days_avg",
        "coverage_ratio",
        "stockout_risk_score",
        "expected_service_level",
        "days_of_cover_post_replenishment",
        "model_name",
        "model_version",
    ]

    existing = [col for col in output_columns if col in df.columns]
    output_df = df[existing].copy()

    for numeric_col in [
        "predicted_units",
        "current_available_qty",
        "open_inbound_qty",
        "inventory_position_qty",
        "reorder_point_qty",
        "safety_stock_qty",
        "target_stock_qty",
        "lead_time_days_avg",
        "coverage_ratio",
        "stockout_risk_score",
        "expected_service_level",
        "days_of_cover_post_replenishment",
    ]:
        if numeric_col in output_df.columns:
            output_df[numeric_col] = pd.to_numeric(output_df[numeric_col], errors="coerce")

    if "recommended_order_qty" in output_df.columns:
        output_df["recommended_order_qty"] = (
            pd.to_numeric(output_df["recommended_order_qty"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    if "priority" in output_df.columns:
        priority_order = {"high": 0, "medium": 1, "low": 2, "none": 3}
        output_df["_priority_sort"] = output_df["priority"].map(priority_order).fillna(9)
        output_df = output_df.sort_values(
            by=["_priority_sort", "recommended_order_qty"],
            ascending=[True, False],
        ).drop(columns="_priority_sort")

    return output_df.reset_index(drop=True)


# =========================================================
# Summary
# =========================================================
def sanitize_for_json(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    serializable = {key: sanitize_for_json(value) for key, value in payload.items()}
    with path.open("w", encoding="utf-8") as file:
        json.dump(serializable, file, indent=2, ensure_ascii=False)


def build_summary(recommendation_df: pd.DataFrame, paths: PipelinePaths) -> Dict[str, Any]:
    actionable_df = recommendation_df.loc[
        recommendation_df["recommended_order_qty"] > 0
    ].copy()

    priority_counts = (
        recommendation_df["priority"].value_counts(dropna=False).to_dict()
        if "priority" in recommendation_df.columns
        else {}
    )

    summary: Dict[str, Any] = {
        "project": "EDIP",
        "company_name": "NorthStar Retail & Distribution",
        "use_case": "Forecast-driven replenishment recommendations",
        "forecast_input_path": str(paths.forecast_path.relative_to(PROJECT_ROOT)),
        "inventory_input_path": str(paths.inventory_path.relative_to(PROJECT_ROOT)),
        "inbound_input_path": (
            str(paths.inbound_path.relative_to(PROJECT_ROOT))
            if paths.inbound_path is not None
            else None
        ),
        "recommendation_output_path": str(
            paths.output_recommendations_path.relative_to(PROJECT_ROOT)
        ),
        "row_count_total": int(len(recommendation_df)),
        "row_count_actionable": int(len(actionable_df)),
        "total_recommended_order_qty": int(
            actionable_df["recommended_order_qty"].sum()
        ) if not actionable_df.empty else 0,
        "avg_stockout_risk_score": float(
            recommendation_df["stockout_risk_score"].mean()
        ) if "stockout_risk_score" in recommendation_df.columns else 0.0,
        "priority_counts": priority_counts,
        "warnings": [],
    }

    if actionable_df.empty:
        summary["warnings"].append("No actionable replenishment recommendations were generated.")

    return summary


# =========================================================
# Main flow
# =========================================================
def generate_recommendations() -> Dict[str, Any]:
    ensure_output_dirs()
    paths = build_paths()

    forecast_df = normalize_forecast_df(load_csv(paths.forecast_path))
    inventory_df = normalize_inventory_df(load_csv(paths.inventory_path))

    inbound_df = (
        normalize_inbound_df(load_csv(paths.inbound_path))
        if paths.inbound_path is not None
        else pd.DataFrame(columns=["product_id", "location_id", "open_inbound_qty"])
    )
    product_df = (
        normalize_product_df(load_csv(paths.product_path))
        if paths.product_path is not None
        else pd.DataFrame(columns=["product_id"])
    )
    supplier_df = (
        normalize_supplier_df(load_csv(paths.supplier_path))
        if paths.supplier_path is not None
        else pd.DataFrame(columns=["supplier_id"])
    )

    merged_df = attach_reference_data(
        forecast_df=forecast_df,
        inventory_df=inventory_df,
        inbound_df=inbound_df,
        product_df=product_df,
        supplier_df=supplier_df,
    )

    enriched_df = assign_priority_and_reason(merged_df)
    recommendation_df = build_recommendation_output(enriched_df)

    recommendation_df.to_csv(paths.output_recommendations_path, index=False)

    summary_payload = build_summary(recommendation_df, paths)
    save_json(paths.output_summary_path, summary_payload)

    logger.info("Forecast input rows: %s", len(forecast_df))
    logger.info("Recommendation rows: %s", len(recommendation_df))
    logger.info(
        "Actionable recommendation rows: %s",
        int((recommendation_df["recommended_order_qty"] > 0).sum()),
    )
    logger.info("Recommendations saved: %s", paths.output_recommendations_path)
    logger.info("Recommendation summary saved: %s", paths.output_summary_path)

    return summary_payload


def main() -> None:
    setup_logging()

    try:
        summary = generate_recommendations()
        logger.info(
            "Replenishment recommendation generation completed successfully. "
            "Actionable rows: %s",
            summary["row_count_actionable"],
        )
    except Exception:
        logger.exception("Replenishment recommendation generation failed.")
        raise
    finally:
        logger.info("generate_recommendations.py finished.")


if __name__ == "__main__":
    main()