from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# =========================================================
# Logging
# =========================================================
logger = logging.getLogger(__name__)


# =========================================================
# Constants
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
FORECASTS_DIR = ARTIFACTS_DIR / "forecasts"
REPORTS_DIR = ARTIFACTS_DIR / "reports"

SCORING_SUMMARY_PATH = FORECASTS_DIR / "demand_forecast_scoring_summary.json"
SCORING_OUTPUT_PATH = FORECASTS_DIR / "demand_forecast_scored.csv"

RECOMMENDATION_SUMMARY_PATH = FORECASTS_DIR / "replenishment_recommendation_summary.json"
RECOMMENDATION_OUTPUT_PATH = FORECASTS_DIR / "replenishment_recommendations.csv"

EVALUATION_REPORT_PATH = REPORTS_DIR / "demand_forecast_evaluation_report.json"

DEFAULT_TOP_N = 20


# =========================================================
# Data models
# =========================================================
@dataclass
class ForecastOverview:
    model_name: str
    model_version: str
    input_dataset_path: Optional[str]
    forecast_output_path: Optional[str]
    recommendation_output_path: Optional[str]
    row_count_scored: int
    row_count_recommendations: int
    row_count_actionable: int
    mean_predicted_units: Optional[float]
    total_predicted_units: Optional[float]
    total_recommended_order_qty: Optional[int]
    avg_stockout_risk_score: Optional[float]
    warnings: List[str] = field(default_factory=list)


@dataclass
class ForecastRecommendationRecord:
    forecast_date: Optional[str]
    target_date: Optional[str]
    product_id: Optional[int]
    location_id: Optional[int]
    region_id: Optional[int]
    store_id: Optional[int]
    warehouse_id: Optional[int]
    channel_id: Optional[int]
    category: Optional[str]
    subcategory: Optional[str]
    brand: Optional[str]
    supplier_id: Optional[int]
    supplier_name: Optional[str]
    predicted_units: Optional[float]
    current_available_qty: Optional[float]
    open_inbound_qty: Optional[float]
    inventory_position_qty: Optional[float]
    reorder_point_qty: Optional[float]
    safety_stock_qty: Optional[float]
    target_stock_qty: Optional[float]
    recommended_order_qty: Optional[int]
    priority: Optional[str]
    recommended_action: Optional[str]
    reason_code: Optional[str]
    reason_text: Optional[str]
    lead_time_days_avg: Optional[float]
    coverage_ratio: Optional[float]
    stockout_risk_score: Optional[float]
    expected_service_level: Optional[float]
    days_of_cover_post_replenishment: Optional[float]
    model_name: Optional[str]
    model_version: Optional[str]


@dataclass
class ForecastServiceResponse:
    overview: ForecastOverview
    recommendations: List[ForecastRecommendationRecord]


# =========================================================
# Helpers
# =========================================================
def load_json_if_exists(path: Path) -> Dict[str, Any]:
    if not path.exists():
        logger.warning("JSON file not found: %s", path)
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
            return payload if isinstance(payload, dict) else {}
    except Exception as exc:
        logger.exception("Failed to read JSON file: %s", path)
        raise RuntimeError(f"Failed to read JSON file: {path}") from exc


def load_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        logger.warning("CSV file not found: %s", path)
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception as exc:
        logger.exception("Failed to read CSV file: %s", path)
        raise RuntimeError(f"Failed to read CSV file: {path}") from exc


def safe_int(value: Any) -> Optional[int]:
    if pd.isna(value):
        return None
    try:
        return int(value)
    except Exception:
        return None


def safe_float(value: Any) -> Optional[float]:
    if pd.isna(value):
        return None
    try:
        return float(value)
    except Exception:
        return None


def safe_str(value: Any) -> Optional[str]:
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text if text else None


def normalize_recommendation_df(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    numeric_columns = [
        "product_id",
        "location_id",
        "region_id",
        "store_id",
        "warehouse_id",
        "channel_id",
        "supplier_id",
        "predicted_units",
        "current_available_qty",
        "open_inbound_qty",
        "inventory_position_qty",
        "reorder_point_qty",
        "safety_stock_qty",
        "target_stock_qty",
        "recommended_order_qty",
        "lead_time_days_avg",
        "coverage_ratio",
        "stockout_risk_score",
        "expected_service_level",
        "days_of_cover_post_replenishment",
    ]

    for col in numeric_columns:
        if col in working.columns:
            working[col] = pd.to_numeric(working[col], errors="coerce")

    for col in ["forecast_date", "target_date"]:
        if col in working.columns:
            working[col] = pd.to_datetime(working[col], errors="coerce")

    return working


def build_overview(
    scoring_summary: Dict[str, Any],
    recommendation_summary: Dict[str, Any],
) -> ForecastOverview:
    prediction_summary = scoring_summary.get("prediction_summary", {}) or {}

    return ForecastOverview(
        model_name=str(
            scoring_summary.get("model_name")
            or recommendation_summary.get("model_name")
            or "unknown"
        ),
        model_version=str(
            scoring_summary.get("model_version")
            or recommendation_summary.get("model_version")
            or "unknown"
        ),
        input_dataset_path=safe_str(scoring_summary.get("input_dataset_path")),
        forecast_output_path=safe_str(scoring_summary.get("forecast_output_path")),
        recommendation_output_path=safe_str(
            recommendation_summary.get("recommendation_output_path")
        ),
        row_count_scored=int(scoring_summary.get("row_count_scored", 0) or 0),
        row_count_recommendations=int(
            recommendation_summary.get("row_count_total", 0) or 0
        ),
        row_count_actionable=int(
            recommendation_summary.get("row_count_actionable", 0) or 0
        ),
        mean_predicted_units=safe_float(
            prediction_summary.get("mean_predicted_units")
        ),
        total_predicted_units=safe_float(
            prediction_summary.get("total_predicted_units")
        ),
        total_recommended_order_qty=safe_int(
            recommendation_summary.get("total_recommended_order_qty")
        ),
        avg_stockout_risk_score=safe_float(
            recommendation_summary.get("avg_stockout_risk_score")
        ),
        warnings=[
            str(item)
            for item in (
                list(scoring_summary.get("warnings", []) or [])
                + list(recommendation_summary.get("warnings", []) or [])
            )
        ],
    )


def build_recommendation_records(
    recommendation_df: pd.DataFrame,
    top_n: int,
    priority_filter: Optional[List[str]] = None,
    action_only: bool = True,
) -> List[ForecastRecommendationRecord]:
    if recommendation_df.empty:
        return []

    working = recommendation_df.copy()

    if action_only and "recommended_order_qty" in working.columns:
        working = working.loc[
            pd.to_numeric(working["recommended_order_qty"], errors="coerce").fillna(0) > 0
        ].copy()

    if priority_filter and "priority" in working.columns:
        normalized_filter = {str(item).strip().lower() for item in priority_filter}
        working = working.loc[
            working["priority"].astype(str).str.strip().str.lower().isin(normalized_filter)
        ].copy()

    if working.empty:
        return []

    sort_columns: List[str] = []
    ascending: List[bool] = []

    if "priority" in working.columns:
        priority_order = {"high": 0, "medium": 1, "low": 2, "none": 3}
        working["_priority_sort"] = (
            working["priority"].astype(str).str.strip().str.lower().map(priority_order).fillna(9)
        )
        sort_columns.append("_priority_sort")
        ascending.append(True)

    if "recommended_order_qty" in working.columns:
        sort_columns.append("recommended_order_qty")
        ascending.append(False)

    if "stockout_risk_score" in working.columns:
        sort_columns.append("stockout_risk_score")
        ascending.append(False)

    if sort_columns:
        working = working.sort_values(by=sort_columns, ascending=ascending)

    working = working.head(top_n).copy()

    records: List[ForecastRecommendationRecord] = []
    for _, row in working.iterrows():
        records.append(
            ForecastRecommendationRecord(
                forecast_date=(
                    row["forecast_date"].strftime("%Y-%m-%d")
                    if "forecast_date" in working.columns and pd.notna(row.get("forecast_date"))
                    else safe_str(row.get("forecast_date"))
                ),
                target_date=(
                    row["target_date"].strftime("%Y-%m-%d")
                    if "target_date" in working.columns and pd.notna(row.get("target_date"))
                    else safe_str(row.get("target_date"))
                ),
                product_id=safe_int(row.get("product_id")),
                location_id=safe_int(row.get("location_id")),
                region_id=safe_int(row.get("region_id")),
                store_id=safe_int(row.get("store_id")),
                warehouse_id=safe_int(row.get("warehouse_id")),
                channel_id=safe_int(row.get("channel_id")),
                category=safe_str(row.get("category")),
                subcategory=safe_str(row.get("subcategory")),
                brand=safe_str(row.get("brand")),
                supplier_id=safe_int(row.get("supplier_id")),
                supplier_name=safe_str(row.get("supplier_name")),
                predicted_units=safe_float(row.get("predicted_units")),
                current_available_qty=safe_float(row.get("current_available_qty")),
                open_inbound_qty=safe_float(row.get("open_inbound_qty")),
                inventory_position_qty=safe_float(row.get("inventory_position_qty")),
                reorder_point_qty=safe_float(row.get("reorder_point_qty")),
                safety_stock_qty=safe_float(row.get("safety_stock_qty")),
                target_stock_qty=safe_float(row.get("target_stock_qty")),
                recommended_order_qty=safe_int(row.get("recommended_order_qty")),
                priority=safe_str(row.get("priority")),
                recommended_action=safe_str(row.get("recommended_action")),
                reason_code=safe_str(row.get("reason_code")),
                reason_text=safe_str(row.get("reason_text")),
                lead_time_days_avg=safe_float(row.get("lead_time_days_avg")),
                coverage_ratio=safe_float(row.get("coverage_ratio")),
                stockout_risk_score=safe_float(row.get("stockout_risk_score")),
                expected_service_level=safe_float(row.get("expected_service_level")),
                days_of_cover_post_replenishment=safe_float(
                    row.get("days_of_cover_post_replenishment")
                ),
                model_name=safe_str(row.get("model_name")),
                model_version=safe_str(row.get("model_version")),
            )
        )

    return records


# =========================================================
# Main service
# =========================================================
class ForecastService:
    def __init__(
        self,
        scoring_summary_path: Path = SCORING_SUMMARY_PATH,
        scoring_output_path: Path = SCORING_OUTPUT_PATH,
        recommendation_summary_path: Path = RECOMMENDATION_SUMMARY_PATH,
        recommendation_output_path: Path = RECOMMENDATION_OUTPUT_PATH,
        evaluation_report_path: Path = EVALUATION_REPORT_PATH,
    ) -> None:
        self.scoring_summary_path = scoring_summary_path
        self.scoring_output_path = scoring_output_path
        self.recommendation_summary_path = recommendation_summary_path
        self.recommendation_output_path = recommendation_output_path
        self.evaluation_report_path = evaluation_report_path

    def get_forecast_overview(self) -> ForecastOverview:
        scoring_summary = load_json_if_exists(self.scoring_summary_path)
        recommendation_summary = load_json_if_exists(self.recommendation_summary_path)
        return build_overview(scoring_summary, recommendation_summary)

    def get_recommendations(
        self,
        *,
        top_n: int = DEFAULT_TOP_N,
        priority_filter: Optional[List[str]] = None,
        action_only: bool = True,
    ) -> List[ForecastRecommendationRecord]:
        recommendation_df = load_csv_if_exists(self.recommendation_output_path)
        recommendation_df = normalize_recommendation_df(recommendation_df)

        return build_recommendation_records(
            recommendation_df=recommendation_df,
            top_n=top_n,
            priority_filter=priority_filter,
            action_only=action_only,
        )

    def get_forecast_response(
        self,
        *,
        top_n: int = DEFAULT_TOP_N,
        priority_filter: Optional[List[str]] = None,
        action_only: bool = True,
    ) -> ForecastServiceResponse:
        overview = self.get_forecast_overview()
        recommendations = self.get_recommendations(
            top_n=top_n,
            priority_filter=priority_filter,
            action_only=action_only,
        )

        return ForecastServiceResponse(
            overview=overview,
            recommendations=recommendations,
        )

    def healthcheck(self) -> Dict[str, Any]:
        return {
            "service": "forecast_service",
            "status": "ok",
            "artifacts_ready": {
                "evaluation_report": self.evaluation_report_path.exists(),
                "scoring_summary": self.scoring_summary_path.exists(),
                "scoring_output": self.scoring_output_path.exists(),
                "recommendation_summary": self.recommendation_summary_path.exists(),
                "recommendation_output": self.recommendation_output_path.exists(),
            },
        }


def build_forecast_service() -> ForecastService:
    return ForecastService()