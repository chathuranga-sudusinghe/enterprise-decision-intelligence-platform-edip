from __future__ import annotations

import logging
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

START_PLANNER_OVERRIDE_ID = 950000000
START_DECISION_LOG_ID = 960000000

OVERRIDE_RATE = 0.34
CRITICAL_OVERRIDE_RATE = 0.70
HIGH_OVERRIDE_RATE = 0.52
NORMAL_OVERRIDE_RATE = 0.28
LOW_OVERRIDE_RATE = 0.12

SERVICE_LEVEL_TARGET_DEFAULT = 0.95

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
    store_csv: Path
    warehouse_csv: Path
    recommendation_csv: Path
    forecast_csv: Path
    planner_override_out_csv: Path
    decision_log_out_csv: Path


def build_paths(base_dir: Path) -> Paths:
    base_dir.mkdir(parents=True, exist_ok=True)

    return Paths(
        base_dir=base_dir,
        calendar_csv=base_dir / "dim_calendar.csv",
        store_csv=base_dir / "dim_store.csv",
        warehouse_csv=base_dir / "dim_warehouse.csv",
        recommendation_csv=base_dir / "fact_replenishment_recommendation.csv",
        forecast_csv=base_dir / "fact_demand_forecast.csv",
        planner_override_out_csv=base_dir / "fact_planner_override.csv",
        decision_log_out_csv=base_dir / "fact_decision_log.csv",
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


def safe_round_4(value: float) -> float:
    return round(float(value), 4)


def to_nullable_int(value: object) -> Optional[int]:
    if pd.isna(value):
        return None
    return int(value)


def choose_weighted(options: List[Tuple[str, float]]) -> str:
    labels = [item[0] for item in options]
    weights = [item[1] for item in options]
    return random.choices(labels, weights=weights, k=1)[0]


# =========================================================
# Preparation
# =========================================================
def prepare_calendar(calendar_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(calendar_df, ["date_id", "full_date"], "dim_calendar")
    calendar_df = calendar_df.copy()
    calendar_df["date_id"] = pd.to_numeric(calendar_df["date_id"], errors="raise").astype(int)
    calendar_df["full_date"] = pd.to_datetime(calendar_df["full_date"], errors="raise")
    return calendar_df.sort_values("full_date").reset_index(drop=True)


def prepare_stores(store_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(store_df, ["store_id", "region_id"], "dim_store")
    store_df = store_df.copy()
    store_df["store_id"] = pd.to_numeric(store_df["store_id"], errors="raise").astype(int)
    store_df["region_id"] = pd.to_numeric(store_df["region_id"], errors="raise").astype(int)
    return store_df


def prepare_warehouses(warehouse_df: pd.DataFrame) -> pd.DataFrame:
    require_columns(warehouse_df, ["warehouse_id", "region_id"], "dim_warehouse")
    warehouse_df = warehouse_df.copy()
    warehouse_df["warehouse_id"] = pd.to_numeric(warehouse_df["warehouse_id"], errors="raise").astype(int)
    warehouse_df["region_id"] = pd.to_numeric(warehouse_df["region_id"], errors="raise").astype(int)
    return warehouse_df


def prepare_recommendations(recommendation_df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "recommendation_id",
        "forecast_run_id",
        "recommendation_date_id",
        "product_id",
        "target_store_id",
        "target_warehouse_id",
        "recommended_order_qty",
        "recommended_transfer_qty",
        "priority_level",
        "reason_code",
        "expected_stockout_risk",
        "expected_service_level",
        "recommended_supplier_id",
        "approval_status",
        "created_timestamp",
    ]
    require_columns(recommendation_df, required, "fact_replenishment_recommendation")

    recommendation_df = recommendation_df.copy()
    for col in [
        "recommendation_id",
        "forecast_run_id",
        "recommendation_date_id",
        "product_id",
        "recommended_order_qty",
        "recommended_transfer_qty",
    ]:
        recommendation_df[col] = pd.to_numeric(recommendation_df[col], errors="raise").astype(int)

    recommendation_df["target_store_id"] = pd.to_numeric(
        recommendation_df["target_store_id"], errors="coerce"
    ).astype("Int64")
    recommendation_df["target_warehouse_id"] = pd.to_numeric(
        recommendation_df["target_warehouse_id"], errors="coerce"
    ).astype("Int64")
    recommendation_df["recommended_supplier_id"] = pd.to_numeric(
        recommendation_df["recommended_supplier_id"], errors="coerce"
    ).astype("Int64")

    recommendation_df["expected_stockout_risk"] = pd.to_numeric(
        recommendation_df["expected_stockout_risk"], errors="raise"
    ).astype(float)
    recommendation_df["expected_service_level"] = pd.to_numeric(
        recommendation_df["expected_service_level"], errors="raise"
    ).astype(float)

    recommendation_df["priority_level"] = recommendation_df["priority_level"].astype(str).str.strip().str.lower()
    recommendation_df["reason_code"] = recommendation_df["reason_code"].astype(str).str.strip().str.lower()
    recommendation_df["approval_status"] = recommendation_df["approval_status"].astype(str).str.strip().str.lower()
    recommendation_df["created_timestamp"] = pd.to_datetime(
        recommendation_df["created_timestamp"], errors="raise"
    )

    return recommendation_df


def prepare_forecasts(forecast_df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "forecast_run_id",
        "product_id",
        "store_id",
        "warehouse_id",
        "forecast_units",
        "confidence_score",
    ]
    require_columns(forecast_df, required, "fact_demand_forecast")

    forecast_df = forecast_df.copy()
    forecast_df["forecast_run_id"] = pd.to_numeric(forecast_df["forecast_run_id"], errors="raise").astype(int)
    forecast_df["product_id"] = pd.to_numeric(forecast_df["product_id"], errors="raise").astype(int)
    forecast_df["store_id"] = pd.to_numeric(forecast_df["store_id"], errors="coerce").astype("Int64")
    forecast_df["warehouse_id"] = pd.to_numeric(forecast_df["warehouse_id"], errors="coerce").astype("Int64")
    forecast_df["forecast_units"] = pd.to_numeric(forecast_df["forecast_units"], errors="raise").astype(float)
    forecast_df["confidence_score"] = pd.to_numeric(forecast_df["confidence_score"], errors="raise").astype(float)

    return forecast_df


# =========================================================
# Feature helpers
# =========================================================
def build_region_maps(
    store_df: pd.DataFrame,
    warehouse_df: pd.DataFrame,
) -> Tuple[Dict[int, int], Dict[int, int]]:
    store_region_map = dict(zip(store_df["store_id"], store_df["region_id"]))
    warehouse_region_map = dict(zip(warehouse_df["warehouse_id"], warehouse_df["region_id"]))
    return store_region_map, warehouse_region_map


def build_forecast_summary_map(
    forecast_df: pd.DataFrame,
) -> Dict[Tuple[int, int, Optional[int], Optional[int]], Dict[str, float]]:
    if forecast_df.empty:
        return {}

    grouped = (
        forecast_df.groupby(["forecast_run_id", "product_id", "store_id", "warehouse_id"], dropna=False)
        .agg(
            total_forecast_units=("forecast_units", "sum"),
            mean_confidence_score=("confidence_score", "mean"),
        )
        .reset_index()
    )

    summary_map: Dict[Tuple[int, int, Optional[int], Optional[int]], Dict[str, float]] = {}
    for _, row in grouped.iterrows():
        key = (
            int(row["forecast_run_id"]),
            int(row["product_id"]),
            to_nullable_int(row["store_id"]),
            to_nullable_int(row["warehouse_id"]),
        )
        summary_map[key] = {
            "total_forecast_units": float(row["total_forecast_units"]),
            "mean_confidence_score": float(row["mean_confidence_score"]),
        }

    return summary_map


def choose_override_probability(priority_level: str) -> float:
    priority_map = {
        "critical": CRITICAL_OVERRIDE_RATE,
        "high": HIGH_OVERRIDE_RATE,
        "normal": NORMAL_OVERRIDE_RATE,
        "low": LOW_OVERRIDE_RATE,
    }
    return priority_map.get(priority_level, OVERRIDE_RATE)


def choose_planner_name(priority_level: str, location_type: str) -> Tuple[str, str]:
    if location_type == "store":
        options = [
            ("N. Perera", "regional_planner"),
            ("S. Fernando", "inventory_planner"),
            ("T. Silva", "store_ops_planner"),
            ("K. Wijesinghe", "supply_planner"),
        ]
    else:
        options = [
            ("M. Gunasekara", "warehouse_planner"),
            ("R. Jayawardena", "network_planner"),
            ("D. Senanayake", "inventory_planner"),
            ("P. Rodrigo", "supply_planner"),
        ]

    if priority_level in {"high", "critical"}:
        options.append(("A. Manager", "planning_manager"))

    return random.choice(options)


def choose_override_type(row: pd.Series) -> str:
    order_qty = int(row["recommended_order_qty"])
    transfer_qty = int(row["recommended_transfer_qty"])
    priority_level = str(row["priority_level"]).lower()
    risk = float(row["expected_stockout_risk"])

    if priority_level == "critical" and risk >= 0.85:
        if order_qty > 0:
            return choose_weighted(
                [
                    ("increase_order", 0.52),
                    ("approve_as_is", 0.20),
                    ("cancel_recommendation", 0.05),
                    ("decrease_order", 0.13),
                    ("reroute_transfer", 0.10),
                ]
            )
        if transfer_qty > 0:
            return choose_weighted(
                [
                    ("increase_transfer", 0.48),
                    ("reroute_transfer", 0.22),
                    ("approve_as_is", 0.15),
                    ("decrease_transfer", 0.10),
                    ("cancel_recommendation", 0.05),
                ]
            )

    if transfer_qty > 0 and order_qty == 0:
        return choose_weighted(
            [
                ("increase_transfer", 0.24),
                ("decrease_transfer", 0.30),
                ("reroute_transfer", 0.24),
                ("approve_as_is", 0.17),
                ("cancel_recommendation", 0.05),
            ]
        )

    if order_qty > 0 and transfer_qty == 0:
        return choose_weighted(
            [
                ("increase_order", 0.26),
                ("decrease_order", 0.34),
                ("approve_as_is", 0.28),
                ("cancel_recommendation", 0.12),
            ]
        )

    return choose_weighted(
        [
            ("approve_as_is", 0.40),
            ("increase_order", 0.18),
            ("decrease_order", 0.18),
            ("increase_transfer", 0.08),
            ("decrease_transfer", 0.08),
            ("reroute_transfer", 0.05),
            ("cancel_recommendation", 0.03),
        ]
    )


def apply_override_quantities(
    original_order_qty: int,
    original_transfer_qty: int,
    override_type: str,
) -> Tuple[int, int]:
    overridden_order_qty = original_order_qty
    overridden_transfer_qty = original_transfer_qty

    if override_type == "increase_order":
        factor = random.uniform(1.08, 1.35)
        overridden_order_qty = max(1, int(round(original_order_qty * factor)))
        overridden_transfer_qty = original_transfer_qty

    elif override_type == "decrease_order":
        factor = random.uniform(0.45, 0.92)
        overridden_order_qty = int(round(original_order_qty * factor))
        overridden_transfer_qty = original_transfer_qty
        if overridden_order_qty <= 0 and original_transfer_qty <= 0:
            overridden_order_qty = 1

    elif override_type == "increase_transfer":
        factor = random.uniform(1.08, 1.30)
        overridden_transfer_qty = max(1, int(round(original_transfer_qty * factor)))
        overridden_order_qty = original_order_qty

    elif override_type == "decrease_transfer":
        factor = random.uniform(0.45, 0.92)
        overridden_transfer_qty = int(round(original_transfer_qty * factor))
        overridden_order_qty = original_order_qty
        if overridden_transfer_qty <= 0 and original_order_qty <= 0:
            overridden_transfer_qty = 1

    elif override_type == "reroute_transfer":
        overridden_transfer_qty = max(
            1,
            original_transfer_qty if original_transfer_qty > 0 else int(round(max(1, original_order_qty) * 0.70)),
        )
        overridden_order_qty = 0

    elif override_type == "cancel_recommendation":
        overridden_order_qty = 0
        overridden_transfer_qty = 0

    elif override_type == "approve_as_is":
        overridden_order_qty = original_order_qty
        overridden_transfer_qty = original_transfer_qty

    else:
        raise ValueError(f"Unsupported override_type: {override_type}")

    return overridden_order_qty, overridden_transfer_qty


def choose_override_reason_code(override_type: str, stockout_risk: float, priority_level: str) -> str:
    if override_type == "increase_order":
        return choose_weighted(
            [
                ("planner_buffer_increase", 0.42),
                ("anticipated_local_demand_spike", 0.33),
                ("supplier_risk_buffer", 0.25),
            ]
        )
    if override_type == "decrease_order":
        return choose_weighted(
            [
                ("budget_constraint", 0.24),
                ("inventory_consolidation", 0.33),
                ("demand_signal_review", 0.43),
            ]
        )
    if override_type == "increase_transfer":
        return choose_weighted(
            [
                ("rebalance_network_inventory", 0.40),
                ("urgent_store_replenishment", 0.35),
                ("regional_service_level_protection", 0.25),
            ]
        )
    if override_type == "decrease_transfer":
        return choose_weighted(
            [
                ("warehouse_capacity_guardrail", 0.26),
                ("transfer_efficiency_review", 0.36),
                ("local_inventory_reassessment", 0.38),
            ]
        )
    if override_type == "reroute_transfer":
        return choose_weighted(
            [
                ("route_optimization", 0.42),
                ("destination_priority_change", 0.28),
                ("network_rebalancing", 0.30),
            ]
        )
    if override_type == "cancel_recommendation":
        if stockout_risk < 0.30:
            return "recommendation_not_required"
        if priority_level in {"high", "critical"}:
            return "manual_exception_review"
        return "inventory_position_rechecked"
    return "planner_confirmed_system_recommendation"


def choose_override_approval_status(priority_level: str, override_type: str) -> str:
    if override_type == "cancel_recommendation":
        return choose_weighted(
            [
                ("pending", 0.30),
                ("approved", 0.55),
                ("rejected", 0.15),
            ]
        )

    if priority_level == "critical":
        return choose_weighted(
            [
                ("pending", 0.38),
                ("approved", 0.52),
                ("rejected", 0.10),
            ]
        )
    if priority_level == "high":
        return choose_weighted(
            [
                ("pending", 0.34),
                ("approved", 0.50),
                ("rejected", 0.16),
            ]
        )

    return choose_weighted(
        [
            ("draft", 0.28),
            ("pending", 0.24),
            ("approved", 0.40),
            ("rejected", 0.08),
        ]
    )


def build_comment_text(
    override_type: str,
    override_reason_code: str,
    priority_level: str,
    stockout_risk: float,
) -> str:
    if override_type == "approve_as_is":
        return (
            f"Planner reviewed recommendation and retained original quantities. "
            f"Priority={priority_level}; risk={stockout_risk:.2f}."
        )

    if override_type == "cancel_recommendation":
        return (
            f"Planner cancelled recommendation after manual review. "
            f"Reason={override_reason_code}; priority={priority_level}."
        )

    return (
        f"Planner adjusted system recommendation via {override_type}. "
        f"Reason={override_reason_code}; priority={priority_level}; risk={stockout_risk:.2f}."
    )


def compute_impact_score(
    original_order_qty: int,
    original_transfer_qty: int,
    overridden_order_qty: int,
    overridden_transfer_qty: int,
    stockout_risk: float,
) -> float:
    original_total = original_order_qty + original_transfer_qty
    overridden_total = overridden_order_qty + overridden_transfer_qty

    if original_total == 0:
        change_ratio = 1.0 if overridden_total > 0 else 0.0
    else:
        change_ratio = abs(overridden_total - original_total) / original_total

    impact_score = min(1.0, (change_ratio * 0.65) + (stockout_risk * 0.35))
    return safe_round_4(impact_score)


def choose_decision_type(
    has_override: bool,
    final_order_qty: int,
    final_transfer_qty: int,
    override_type: Optional[str],
    override_approval_status: Optional[str],
    stockout_risk: float,
) -> str:
    if has_override:
        if override_approval_status == "rejected":
            return "replenishment_rejected"
        if override_type == "reroute_transfer":
            return "transfer_rerouted"
        if override_type == "cancel_recommendation":
            return "replenishment_rejected"
        if stockout_risk >= 0.88 and final_order_qty > 0:
            return "expedite_order"
        return "replenishment_overridden"

    if stockout_risk >= 0.90 and final_order_qty > 0:
        return "exception_escalated"
    return "replenishment_approved"


def choose_decision_status(
    has_override: bool,
    recommendation_status: str,
    override_approval_status: Optional[str],
    decision_type: str,
    final_order_qty: int,
    final_transfer_qty: int,
) -> str:
    if decision_type == "exception_escalated":
        return "escalated"

    # Final action does not exist, so status must not remain pending/draft.
    if final_order_qty <= 0 and final_transfer_qty <= 0:
        return "rejected"

    if has_override and override_approval_status is not None:
        if override_approval_status in {"draft", "pending"}:
            return "approved"
        return override_approval_status

    if recommendation_status in {"approved", "executed", "rejected"}:
        return recommendation_status

    if recommendation_status in {"pending", "draft"}:
        return "approved"

    return "approved"


def choose_decision_source(has_override: bool, priority_level: str) -> str:
    if has_override:
        if priority_level in {"high", "critical"}:
            return choose_weighted(
                [
                    ("planner", 0.45),
                    ("manager", 0.20),
                    ("hybrid", 0.35),
                ]
            )
        return choose_weighted(
            [
                ("planner", 0.64),
                ("hybrid", 0.28),
                ("manager", 0.08),
            ]
        )

    return choose_weighted(
        [
            ("system", 0.62),
            ("hybrid", 0.30),
            ("planner", 0.08),
        ]
    )


def choose_decision_reason_code(
    has_override: bool,
    recommendation_reason_code: str,
    override_reason_code: Optional[str],
    decision_status: str,
    decision_type: str,
) -> str:
    if has_override and override_reason_code:
        if decision_status == "rejected":
            return "override_rejected_after_review"
        return override_reason_code

    if decision_type == "exception_escalated":
        return "critical_risk_escalation"

    if decision_status == "rejected":
        return "recommendation_rejected"

    return recommendation_reason_code


def choose_decided_by(
    has_override: bool,
    planner_name: Optional[str],
    decision_source: str,
) -> str:
    if has_override and planner_name:
        return planner_name
    if decision_source == "system":
        return "edip_planning_engine"
    if decision_source == "hybrid":
        return "edip_planner_workflow"
    if decision_source == "manager":
        return "planning_manager"
    return "inventory_planner"


# =========================================================
# Core generation
# =========================================================
def generate_planner_overrides_and_decision_logs(
    calendar_df: pd.DataFrame,
    store_df: pd.DataFrame,
    warehouse_df: pd.DataFrame,
    recommendation_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    _ = calendar_df  # kept for future extensibility

    store_region_map, warehouse_region_map = build_region_maps(store_df, warehouse_df)
    forecast_summary_map = build_forecast_summary_map(forecast_df)

    override_rows: List[Dict] = []
    decision_rows: List[Dict] = []

    planner_override_id = START_PLANNER_OVERRIDE_ID
    decision_log_id = START_DECISION_LOG_ID

    for _, row in recommendation_df.sort_values("recommendation_id").iterrows():
        recommendation_id = int(row["recommendation_id"])
        forecast_run_id = int(row["forecast_run_id"])
        recommendation_date_id = int(row["recommendation_date_id"])
        product_id = int(row["product_id"])

        target_store_id = to_nullable_int(row["target_store_id"])
        target_warehouse_id = to_nullable_int(row["target_warehouse_id"])

        location_type = "store" if target_store_id is not None else "warehouse"
        region_id = (
            store_region_map.get(target_store_id)
            if target_store_id is not None
            else warehouse_region_map.get(target_warehouse_id)
        )

        if region_id is None:
            raise ValueError(
                f"Could not resolve region_id for recommendation_id={recommendation_id}, "
                f"store_id={target_store_id}, warehouse_id={target_warehouse_id}"
            )

        original_order_qty = int(row["recommended_order_qty"])
        original_transfer_qty = int(row["recommended_transfer_qty"])
        priority_level = str(row["priority_level"]).lower()
        recommendation_reason_code = str(row["reason_code"]).lower()
        stockout_risk = float(row["expected_stockout_risk"])
        expected_service_level = float(row["expected_service_level"])
        recommendation_status = str(row["approval_status"]).lower()

        override_probability = choose_override_probability(priority_level)
        has_override = random.random() < override_probability

        forecast_key = (
            forecast_run_id,
            product_id,
            target_store_id,
            target_warehouse_id,
        )
        forecast_summary = forecast_summary_map.get(
            forecast_key,
            {
                "total_forecast_units": float(original_order_qty + original_transfer_qty),
                "mean_confidence_score": 0.65,
            },
        )
        mean_confidence_score = float(forecast_summary["mean_confidence_score"])

        planner_name: Optional[str] = None
        planner_role: Optional[str] = None
        override_type: Optional[str] = None
        override_reason_code: Optional[str] = None
        override_approval_status: Optional[str] = None
        planner_override_ref: Optional[int] = None

        final_order_qty = original_order_qty
        final_transfer_qty = original_transfer_qty

        if has_override:
            planner_name, planner_role = choose_planner_name(priority_level, location_type)
            override_type = choose_override_type(row)

            overridden_order_qty, overridden_transfer_qty = apply_override_quantities(
                original_order_qty=original_order_qty,
                original_transfer_qty=original_transfer_qty,
                override_type=override_type,
            )

            override_reason_code = choose_override_reason_code(
                override_type=override_type,
                stockout_risk=stockout_risk,
                priority_level=priority_level,
            )

            override_approval_status = choose_override_approval_status(priority_level, override_type)

            impact_score = compute_impact_score(
                original_order_qty=original_order_qty,
                original_transfer_qty=original_transfer_qty,
                overridden_order_qty=overridden_order_qty,
                overridden_transfer_qty=overridden_transfer_qty,
                stockout_risk=stockout_risk,
            )

            comment_text = build_comment_text(
                override_type=override_type,
                override_reason_code=override_reason_code,
                priority_level=priority_level,
                stockout_risk=stockout_risk,
            )

            override_rows.append(
                {
                    "planner_override_id": planner_override_id,
                    "recommendation_id": recommendation_id,
                    "forecast_run_id": forecast_run_id,
                    "override_date_id": recommendation_date_id,
                    "product_id": product_id,
                    "target_store_id": target_store_id,
                    "target_warehouse_id": target_warehouse_id,
                    "original_order_qty": original_order_qty,
                    "original_transfer_qty": original_transfer_qty,
                    "overridden_order_qty": overridden_order_qty,
                    "overridden_transfer_qty": overridden_transfer_qty,
                    "override_type": override_type,
                    "override_reason_code": override_reason_code,
                    "planner_name": planner_name,
                    "planner_role": planner_role,
                    "approval_status": override_approval_status,
                    "impact_score": impact_score,
                    "comment_text": comment_text,
                    "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

            planner_override_ref = planner_override_id
            planner_override_id += 1

            if override_approval_status == "rejected":
                final_order_qty = original_order_qty
                final_transfer_qty = original_transfer_qty
            elif override_type == "cancel_recommendation":
                final_order_qty = 0
                final_transfer_qty = 0
            else:
                final_order_qty = overridden_order_qty
                final_transfer_qty = overridden_transfer_qty

        decision_type = choose_decision_type(
            has_override=has_override,
            final_order_qty=final_order_qty,
            final_transfer_qty=final_transfer_qty,
            override_type=override_type,
            override_approval_status=override_approval_status,
            stockout_risk=stockout_risk,
        )

        decision_status = choose_decision_status(
            has_override=has_override,
            recommendation_status=recommendation_status,
            override_approval_status=override_approval_status,
            decision_type=decision_type,
            final_order_qty=final_order_qty,
            final_transfer_qty=final_transfer_qty,
        )

        decision_source = choose_decision_source(
            has_override=has_override,
            priority_level=priority_level,
        )

        escalation_flag = bool(decision_type == "exception_escalated" or decision_status == "escalated")
        exception_flag = bool(stockout_risk >= 0.85 or mean_confidence_score <= 0.45)

        decision_reason_code = choose_decision_reason_code(
            has_override=has_override,
            recommendation_reason_code=recommendation_reason_code,
            override_reason_code=override_reason_code,
            decision_status=decision_status,
            decision_type=decision_type,
        )

        decided_by = choose_decided_by(
            has_override=has_override,
            planner_name=planner_name,
            decision_source=decision_source,
        )

        decision_rows.append(
            {
                "decision_log_id": decision_log_id,
                "decision_date_id": recommendation_date_id,
                "forecast_run_id": forecast_run_id,
                "recommendation_id": recommendation_id,
                "planner_override_id": planner_override_ref,
                "product_id": product_id,
                "region_id": region_id,
                "target_store_id": target_store_id,
                "target_warehouse_id": target_warehouse_id,
                "decision_type": decision_type,
                "decision_status": decision_status,
                "decision_source": decision_source,
                "final_order_qty": final_order_qty,
                "final_transfer_qty": final_transfer_qty,
                "service_level_target": safe_round_4(SERVICE_LEVEL_TARGET_DEFAULT),
                "expected_stockout_risk": safe_round_4(stockout_risk),
                "expected_service_level": safe_round_4(expected_service_level),
                "escalation_flag": escalation_flag,
                "exception_flag": exception_flag,
                "decision_reason_code": decision_reason_code,
                "decided_by": decided_by,
                "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        decision_log_id += 1

    planner_override_df = pd.DataFrame(override_rows)
    decision_log_df = pd.DataFrame(decision_rows)

    if planner_override_df.empty:
        raise ValueError("Planner override generation produced 0 rows. Review the override logic.")
    if decision_log_df.empty:
        raise ValueError("Decision log generation produced 0 rows.")

    planner_override_df = cast_required_int_columns(
        planner_override_df,
        [
            "planner_override_id",
            "recommendation_id",
            "forecast_run_id",
            "override_date_id",
            "product_id",
            "original_order_qty",
            "original_transfer_qty",
            "overridden_order_qty",
            "overridden_transfer_qty",
        ],
    )
    planner_override_df = cast_nullable_int_columns(
        planner_override_df,
        ["target_store_id", "target_warehouse_id"],
    )
    planner_override_df["impact_score"] = pd.to_numeric(
        planner_override_df["impact_score"], errors="raise"
    ).astype(float)

    decision_log_df = cast_required_int_columns(
        decision_log_df,
        [
            "decision_log_id",
            "decision_date_id",
            "product_id",
            "region_id",
            "final_order_qty",
            "final_transfer_qty",
        ],
    )
    decision_log_df = cast_nullable_int_columns(
        decision_log_df,
        ["forecast_run_id", "recommendation_id", "planner_override_id", "target_store_id", "target_warehouse_id"],
    )
    for metric_col in ["service_level_target", "expected_stockout_risk", "expected_service_level"]:
        decision_log_df[metric_col] = pd.to_numeric(decision_log_df[metric_col], errors="raise").astype(float)

    return planner_override_df, decision_log_df


# =========================================================
# Save
# =========================================================
def save_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


# =========================================================
# Main
# =========================================================
def main() -> None:
    try:
        paths = build_paths(BASE_DIR)

        logger.info("Loading Phase 4 source files.")
        calendar_df = prepare_calendar(load_csv(paths.calendar_csv))
        store_df = prepare_stores(load_csv(paths.store_csv))
        warehouse_df = prepare_warehouses(load_csv(paths.warehouse_csv))
        recommendation_df = prepare_recommendations(load_csv(paths.recommendation_csv))
        forecast_df = prepare_forecasts(load_csv(paths.forecast_csv))

        logger.info("Generating planner overrides and decision logs.")
        planner_override_df, decision_log_df = generate_planner_overrides_and_decision_logs(
            calendar_df=calendar_df,
            store_df=store_df,
            warehouse_df=warehouse_df,
            recommendation_df=recommendation_df,
            forecast_df=forecast_df,
        )

        save_csv(planner_override_df, paths.planner_override_out_csv)
        save_csv(decision_log_df, paths.decision_log_out_csv)

        logger.info("Phase 4 generation completed successfully.")
        logger.info("Planner override rows: %s", f"{len(planner_override_df):,}")
        logger.info("Decision log rows: %s", f"{len(decision_log_df):,}")
        logger.info("Planner override output: %s", paths.planner_override_out_csv)
        logger.info("Decision log output: %s", paths.decision_log_out_csv)

    except Exception as exc:
        logger.exception("Phase 4 planner override / decision log generation failed: %s", exc)
        raise
    finally:
        logger.info("Phase 4 generator script finished.")


if __name__ == "__main__":
    main()