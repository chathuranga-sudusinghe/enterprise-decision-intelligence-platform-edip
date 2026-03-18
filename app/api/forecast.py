from __future__ import annotations

import logging
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.forecast_service import ForecastService, build_forecast_service


# =========================================================
# Logging
# =========================================================
logger = logging.getLogger(__name__)


# =========================================================
# Router
# =========================================================
router = APIRouter(
    prefix="/forecast",
    tags=["Forecast"],
)


# =========================================================
# Dependency-like builder
# =========================================================
def get_forecast_service() -> ForecastService:
    return build_forecast_service()


# =========================================================
# Helpers
# =========================================================
def to_dict(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)

    if isinstance(value, list):
        return [to_dict(item) for item in value]

    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}

    return value


def parse_priority_filter(priority: Optional[str]) -> Optional[List[str]]:
    if priority is None or not priority.strip():
        return None

    values = [item.strip().lower() for item in priority.split(",") if item.strip()]
    return values or None


# =========================================================
# Routes
# =========================================================
@router.get("/health")
def forecast_health() -> Dict[str, Any]:
    """
    Health endpoint for forecast service artifact readiness.
    """
    try:
        service = get_forecast_service()
        return service.healthcheck()
    except Exception as exc:
        logger.exception("Forecast healthcheck failed.")
        raise HTTPException(
            status_code=500,
            detail=f"Forecast healthcheck failed: {exc}",
        ) from exc


@router.get("/overview")
def get_forecast_overview() -> Dict[str, Any]:
    """
    Returns forecast scoring and recommendation overview.
    """
    try:
        service = get_forecast_service()
        overview = service.get_forecast_overview()
        return to_dict(overview)
    except Exception as exc:
        logger.exception("Failed to load forecast overview.")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load forecast overview: {exc}",
        ) from exc


@router.get("/recommendations")
def get_forecast_recommendations(
    top_n: int = Query(default=20, ge=1, le=500),
    priority: Optional[str] = Query(
        default=None,
        description="Comma-separated priorities, e.g. high,medium",
    ),
    action_only: bool = Query(
        default=True,
        description="Return only rows with recommended_order_qty > 0",
    ),
) -> Dict[str, Any]:
    """
    Returns top forecast-driven replenishment recommendations.
    """
    try:
        service = get_forecast_service()
        priority_filter = parse_priority_filter(priority)

        recommendations = service.get_recommendations(
            top_n=top_n,
            priority_filter=priority_filter,
            action_only=action_only,
        )

        return {
            "count": len(recommendations),
            "top_n": top_n,
            "priority_filter": priority_filter,
            "action_only": action_only,
            "recommendations": to_dict(recommendations),
        }
    except Exception as exc:
        logger.exception("Failed to load forecast recommendations.")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load forecast recommendations: {exc}",
        ) from exc


@router.get("")
def get_forecast_response(
    top_n: int = Query(default=20, ge=1, le=500),
    priority: Optional[str] = Query(
        default=None,
        description="Comma-separated priorities, e.g. high,medium",
    ),
    action_only: bool = Query(
        default=True,
        description="Return only rows with recommended_order_qty > 0",
    ),
) -> Dict[str, Any]:
    """
    Returns combined forecast overview + recommendations.
    """
    try:
        service = get_forecast_service()
        priority_filter = parse_priority_filter(priority)

        response = service.get_forecast_response(
            top_n=top_n,
            priority_filter=priority_filter,
            action_only=action_only,
        )

        return to_dict(response)
    except Exception as exc:
        logger.exception("Failed to load combined forecast response.")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load combined forecast response: {exc}",
        ) from exc