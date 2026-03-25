# app\agents\analytics_agent.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from app.agents.planner_agent import PlannerPlan, TaskType
from app.agents.reasoning_agent import ReasoningAgentResult
from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# Protocols
# =========================================================
class ForecastServiceProtocol(Protocol):
    """
    Minimal protocol for the existing forecast service.

    The Analytics Agent should call a service layer, not raw model code.
    """

    def run_forecast_workflow(
        self,
        *,
        product_id: Optional[int] = None,
        store_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        region_id: Optional[int] = None,
        horizon_days: int = 7,
        include_recommendations: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute forecast + recommendation workflow and return structured output.
        """
        ...


# =========================================================
# Data models
# =========================================================
@dataclass(frozen=True)
class AnalyticsAgentInput:
    """Input payload for the Analytics Agent."""

    question: str
    plan: PlannerPlan
    reasoning_result: Optional[ReasoningAgentResult] = None

    product_id: Optional[int] = None
    store_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    region_id: Optional[int] = None

    horizon_days: int = 7
    include_recommendations: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalyticsSignal:
    """Normalized analytics signal returned by the Analytics Agent."""

    signal_name: str
    signal_value: Any
    signal_type: str = "analytics"
    source: str = "forecast_service"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalyticsAgentResult:
    """Final structured output from the Analytics Agent."""

    question: str
    analytics_used: bool
    analytics_mode: str
    summary: str
    forecast_payload: Dict[str, Any]
    recommendation_payload: Dict[str, Any]
    structured_signals: List[AnalyticsSignal]
    warnings: List[str] = field(default_factory=list)


# =========================================================
# Analytics agent
# =========================================================
class AnalyticsAgent:
    """
    EDIP Analytics Agent.

    Responsibilities:
    - decide whether predictive/prescriptive analytics should run
    - call the forecast/recommendation service layer
    - normalize outputs for downstream execution
    """

    def __init__(self, forecast_service: ForecastServiceProtocol) -> None:
        self.forecast_service = forecast_service
        logger.info("AnalyticsAgent initialized.")

    def analyze(self, payload: AnalyticsAgentInput) -> AnalyticsAgentResult:
        """
        Run analytics workflow when the plan requires predictive/prescriptive support.
        """
        normalized_question = self._validate_question(payload.question)
        warnings: List[str] = []

        if not self._needs_analytics(payload.plan):
            warnings.append("Planner did not require analytics for this request.")
            logger.info("AnalyticsAgent skipped because analytics was not required.")

            return AnalyticsAgentResult(
                question=normalized_question,
                analytics_used=False,
                analytics_mode="skipped",
                summary="Analytics workflow was skipped because the current plan does not require forecasting or prescriptive logic.",
                forecast_payload={},
                recommendation_payload={},
                structured_signals=[],
                warnings=warnings,
            )

        request_context = self._build_request_context(payload)
        logger.info(
            "AnalyticsAgent started | horizon_days=%s | include_recommendations=%s | context=%s",
            payload.horizon_days,
            payload.include_recommendations,
            request_context,
        )

        service_output = self.forecast_service.run_forecast_workflow(
            product_id=payload.product_id,
            store_id=payload.store_id,
            warehouse_id=payload.warehouse_id,
            region_id=payload.region_id,
            horizon_days=payload.horizon_days,
            include_recommendations=payload.include_recommendations,
            metadata=request_context,
        )

        forecast_payload = self._extract_forecast_payload(service_output)
        recommendation_payload = self._extract_recommendation_payload(service_output)
        structured_signals = self._build_structured_signals(
            forecast_payload=forecast_payload,
            recommendation_payload=recommendation_payload,
        )
        summary = self._build_summary(
            forecast_payload=forecast_payload,
            recommendation_payload=recommendation_payload,
            structured_signals=structured_signals,
        )

        if not forecast_payload:
            warnings.append("Forecast payload was empty.")
        if payload.include_recommendations and not recommendation_payload:
            warnings.append("Recommendation payload was empty.")

        result = AnalyticsAgentResult(
            question=normalized_question,
            analytics_used=True,
            analytics_mode=self._resolve_analytics_mode(payload.include_recommendations),
            summary=summary,
            forecast_payload=forecast_payload,
            recommendation_payload=recommendation_payload,
            structured_signals=structured_signals,
            warnings=warnings,
        )

        logger.info(
            "AnalyticsAgent completed | analytics_mode=%s | signal_count=%s",
            result.analytics_mode,
            len(result.structured_signals),
        )
        return result

    # =========================================================
    # Internal helpers
    # =========================================================
    def _validate_question(self, question: str) -> str:
        """
        Validate and normalize the incoming question.
        """
        normalized = " ".join(question.strip().split())
        if not normalized:
            raise ValueError("Question cannot be empty for analytics.")
        return normalized

    def _needs_analytics(self, plan: PlannerPlan) -> bool:
        """
        Decide whether the current workflow needs analytics.
        """
        if plan.task_type in {TaskType.ANALYTICS, TaskType.HYBRID}:
            return True

        return plan.needs_analytics

    def _build_request_context(self, payload: AnalyticsAgentInput) -> Dict[str, Any]:
        """
        Build a clean analytics request context for the forecast service.
        """
        context: Dict[str, Any] = {
            "question": payload.question,
            "task_type": payload.plan.task_type.value,
            "knowledge_domains": payload.plan.knowledge_domains,
            "notes": payload.plan.notes,
        }

        if payload.reasoning_result is not None:
            context["reasoning_summary"] = payload.reasoning_result.reasoning_summary
            context["risk_flags"] = payload.reasoning_result.risk_flags
            context["rationale_points"] = payload.reasoning_result.rationale_points

        context.update(payload.metadata)
        return context

    def _extract_forecast_payload(self, service_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract forecast section from service output.
        """
        if "forecast" in service_output and isinstance(service_output["forecast"], dict):
            return service_output["forecast"]

        if "forecast_payload" in service_output and isinstance(service_output["forecast_payload"], dict):
            return service_output["forecast_payload"]

        return {}

    def _extract_recommendation_payload(self, service_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract recommendation section from service output.
        """
        if "recommendations" in service_output and isinstance(service_output["recommendations"], dict):
            return service_output["recommendations"]

        if "recommendation_payload" in service_output and isinstance(service_output["recommendation_payload"], dict):
            return service_output["recommendation_payload"]

        return {}

    def _build_structured_signals(
        self,
        *,
        forecast_payload: Dict[str, Any],
        recommendation_payload: Dict[str, Any],
    ) -> List[AnalyticsSignal]:
        """
        Convert service outputs into normalized analytics signals.
        """
        signals: List[AnalyticsSignal] = []

        signal_candidates = [
            ("forecast_units", forecast_payload.get("forecast_units")),
            ("forecast_lower_bound", forecast_payload.get("forecast_lower_bound")),
            ("forecast_upper_bound", forecast_payload.get("forecast_upper_bound")),
            ("confidence_score", forecast_payload.get("confidence_score")),
            ("expected_stockout_risk", recommendation_payload.get("expected_stockout_risk")),
            ("expected_service_level", recommendation_payload.get("expected_service_level")),
            ("recommended_order_qty", recommendation_payload.get("recommended_order_qty")),
            ("recommended_transfer_qty", recommendation_payload.get("recommended_transfer_qty")),
            ("priority_level", recommendation_payload.get("priority_level")),
            ("reason_code", recommendation_payload.get("reason_code")),
        ]

        for signal_name, signal_value in signal_candidates:
            if signal_value is None:
                continue

            signals.append(
                AnalyticsSignal(
                    signal_name=signal_name,
                    signal_value=signal_value,
                    metadata={"origin": "forecast_service_output"},
                )
            )

        return signals

    def _build_summary(
        self,
        *,
        forecast_payload: Dict[str, Any],
        recommendation_payload: Dict[str, Any],
        structured_signals: List[AnalyticsSignal],
    ) -> str:
        """
        Build one clean analytics summary.
        """
        parts: List[str] = []

        forecast_units = forecast_payload.get("forecast_units")
        if forecast_units is not None:
            parts.append(f"Forecast workflow produced demand units estimate: {forecast_units}.")

        expected_stockout_risk = recommendation_payload.get("expected_stockout_risk")
        if expected_stockout_risk is not None:
            parts.append(f"Expected stockout risk was estimated as {expected_stockout_risk}.")

        recommended_order_qty = recommendation_payload.get("recommended_order_qty")
        if recommended_order_qty is not None:
            parts.append(f"Recommended order quantity: {recommended_order_qty}.")

        recommended_transfer_qty = recommendation_payload.get("recommended_transfer_qty")
        if recommended_transfer_qty is not None:
            parts.append(f"Recommended transfer quantity: {recommended_transfer_qty}.")

        if not parts:
            parts.append(
                f"Analytics workflow completed and produced {len(structured_signals)} normalized signals."
            )

        return " ".join(parts)

    def _resolve_analytics_mode(self, include_recommendations: bool) -> str:
        """
        Resolve high-level analytics mode label.
        """
        if include_recommendations:
            return "forecast_and_recommendation"
        return "forecast_only"


# =========================================================
# Builder
# =========================================================
def build_analytics_agent(
    forecast_service: ForecastServiceProtocol,
) -> AnalyticsAgent:
    """Factory function for consistent Analytics Agent creation."""
    return AnalyticsAgent(forecast_service=forecast_service)