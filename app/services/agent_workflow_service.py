# app/services/agent_workflow_service.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.agents.analytics_agent import (
    ForecastServiceProtocol,
    build_analytics_agent,
)
from app.agents.execution_agent import build_execution_agent
from app.agents.langgraph_workflow import (
    EDIPLangGraphWorkflow,
    build_edip_langgraph_workflow,
    build_initial_workflow_state,
    summarize_workflow_result,
)
from app.agents.planner_agent import build_planner_agent
from app.agents.reasoning_agent import build_reasoning_agent
from app.agents.retrieval_agent import (
    RetrievalServiceProtocol,
    build_retrieval_agent,
)
from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# Request model
# =========================================================
@dataclass(frozen=True)
class AgentWorkflowRequest:
    """
    Input payload for one EDIP agent workflow execution.

    This keeps the service interface clean and stable for:
    - API routes
    - scripts
    - tests
    - future orchestration layers
    """

    question: str
    user_role: Optional[str] = None
    region_scope: Optional[str] = None

    product_id: Optional[int] = None
    store_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    region_id: Optional[int] = None

    horizon_days: int = 7
    include_recommendations: bool = True
    require_approval: bool = False

    metadata: Dict[str, Any] = field(default_factory=dict)


# =========================================================
# Service
# =========================================================
class AgentWorkflowService:
    """
    Service-layer wrapper for the EDIP LangGraph workflow.

    Responsibilities:
    - build all workflow agents from existing project builders
    - construct the LangGraph workflow object
    - run one end-to-end agent workflow request
    - return a clean serializable summary for API or app usage
    """

    def __init__(
        self,
        *,
        retrieval_service: RetrievalServiceProtocol,
        forecast_service: ForecastServiceProtocol,
    ) -> None:
        """
        Initialize the workflow service with required downstream services.

        Required dependencies:
        - retrieval_service: must support retrieve_context(...)
        - forecast_service: must support run_forecast_workflow(...)
        """
        self.retrieval_service = retrieval_service
        self.forecast_service = forecast_service

        # Build agents using the project's existing factory functions.
        self.planner_agent = build_planner_agent()
        self.retrieval_agent = build_retrieval_agent(
            retrieval_service=self.retrieval_service
        )
        self.reasoning_agent = build_reasoning_agent()
        self.analytics_agent = build_analytics_agent(
            forecast_service=self.forecast_service
        )
        self.execution_agent = build_execution_agent()

        # Build the LangGraph workflow using the real agent objects.
        self.workflow: EDIPLangGraphWorkflow = build_edip_langgraph_workflow(
            planner_agent=self.planner_agent,
            retrieval_agent=self.retrieval_agent,
            reasoning_agent=self.reasoning_agent,
            analytics_agent=self.analytics_agent,
            execution_agent=self.execution_agent,
        )

        logger.info("AgentWorkflowService initialized successfully.")

    def run_workflow(self, request: AgentWorkflowRequest) -> Dict[str, Any]:
        """
        Run one end-to-end EDIP agent workflow and return a serialized summary.

        Returns a clean dictionary that is easy to:
        - return from FastAPI
        - inspect in tests
        - log in scripts
        """
        self._validate_request(request)

        logger.info(
            "Agent workflow execution started | question=%s | user_role=%s | region_scope=%s",
            request.question,
            request.user_role,
            request.region_scope,
        )

        initial_state = build_initial_workflow_state(
            question=request.question,
            user_role=request.user_role,
            region_scope=request.region_scope,
            product_id=request.product_id,
            store_id=request.store_id,
            warehouse_id=request.warehouse_id,
            region_id=request.region_id,
            horizon_days=request.horizon_days,
            include_recommendations=request.include_recommendations,
            require_approval=request.require_approval,
            metadata=request.metadata,
        )

        final_state = self.workflow.invoke(initial_state)
        raw_summary = summarize_workflow_result(final_state)
        shaped_summary = self._build_business_response(
            request=request,
            raw_summary=raw_summary,
        )

        logger.info(
            "Agent workflow execution completed | trace=%s | warnings=%s | status=%s",
            shaped_summary.get("workflow_overview", {}).get("workflow_trace", []),
            len(shaped_summary.get("workflow_overview", {}).get("warnings", [])),
            shaped_summary.get("decision_summary", {}).get("status"),
        )
        return shaped_summary

    def run_workflow_state(self, request: AgentWorkflowRequest) -> Dict[str, Any]:
        """
        Run the workflow and return the raw final workflow state.

        Useful for:
        - debugging
        - deep inspection
        - internal testing

        In most application paths, run_workflow(...) is the better method.
        """
        self._validate_request(request)

        logger.info(
            "Agent workflow raw-state execution started | question=%s",
            request.question,
        )

        initial_state = build_initial_workflow_state(
            question=request.question,
            user_role=request.user_role,
            region_scope=request.region_scope,
            product_id=request.product_id,
            store_id=request.store_id,
            warehouse_id=request.warehouse_id,
            region_id=request.region_id,
            horizon_days=request.horizon_days,
            include_recommendations=request.include_recommendations,
            require_approval=request.require_approval,
            metadata=request.metadata,
        )

        final_state = self.workflow.invoke(initial_state)

        logger.info(
            "Agent workflow raw-state execution completed | trace=%s",
            final_state.get("workflow_trace", []),
        )
        return dict(final_state)

    # =========================================================
    # Internal helpers
    # =========================================================
    def _validate_request(self, request: AgentWorkflowRequest) -> None:
        """
        Validate the incoming service request before workflow execution.
        """
        normalized_question = " ".join(request.question.strip().split())
        if not normalized_question:
            raise ValueError("question cannot be empty for agent workflow execution.")

        if request.horizon_days <= 0:
            raise ValueError("horizon_days must be greater than 0.")

    def _build_business_response(
        self,
        *,
        request: AgentWorkflowRequest,
        raw_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Shape the raw summarized workflow output into a cleaner business-facing response.

        Important:
        - keeps backward-compatible raw sections for the current UI
        - adds cleaner grouped sections for the next UI cleanup step
        - keeps debug payload separate from user-facing sections
        """
        planner_plan = self._as_dict(raw_summary.get("planner_plan"))
        reasoning_result = self._as_dict(raw_summary.get("reasoning_result"))
        analytics_result = self._as_dict(raw_summary.get("analytics_result"))
        execution_result = self._as_dict(raw_summary.get("execution_result"))
        business_answer = self._as_dict(raw_summary.get("business_answer"))

        forecast_payload = self._as_dict(analytics_result.get("forecast_payload"))
        recommendation_payload = self._as_dict(
            analytics_result.get("recommendation_payload")
        )

        workflow_trace = self._as_list(raw_summary.get("workflow_trace"))
        warnings = self._as_list(raw_summary.get("warnings"))
        risk_flags = self._as_list(reasoning_result.get("risk_flags"))
        rationale_points = self._as_list(reasoning_result.get("rationale_points"))
        knowledge_domains = self._as_list(planner_plan.get("knowledge_domains"))

        why_text = self._clean_text(
            business_answer.get("why")
            or reasoning_result.get("reasoning_summary")
            or execution_result.get("final_message")
            or "No explanation was generated."
        )

        decision_text = self._clean_text(
            business_answer.get("decision")
            or execution_result.get("final_message")
            or "No final decision message was generated."
        )

        status = self._clean_text(
            execution_result.get("status") or "unknown"
        )
        output_type = self._clean_text(
            execution_result.get("output_type") or "unknown"
        )
        task_type = self._clean_text(
            planner_plan.get("task_type") or "unknown"
        )

        response: Dict[str, Any] = {
            # =====================================================
            # Clean response contract for the next UI version
            # =====================================================
            "question": raw_summary.get("question", request.question),
            "business_answer": {
                "why": why_text,
                "decision": decision_text,
            },
            "decision_summary": {
                "status": status,
                "output_type": output_type,
                "final_message": self._clean_text(
                    execution_result.get("final_message") or decision_text
                ),
                "risk_flags": risk_flags,
                "knowledge_domains": knowledge_domains,
            },
            "forecast_summary": {
                "forecast_units": self._safe_number(
                    forecast_payload.get("forecast_units")
                ),
                "forecast_lower_bound": self._safe_number(
                    forecast_payload.get("forecast_lower_bound")
                ),
                "forecast_upper_bound": self._safe_number(
                    forecast_payload.get("forecast_upper_bound")
                ),
                "confidence_score": self._safe_number(
                    forecast_payload.get("confidence_score")
                ),
            },
            "recommendation_summary": {
                "recommended_order_qty": self._safe_number(
                    recommendation_payload.get("recommended_order_qty")
                ),
                "recommended_transfer_qty": self._safe_number(
                    recommendation_payload.get("recommended_transfer_qty")
                ),
                "priority_level": self._clean_text(
                    recommendation_payload.get("priority_level")
                ),
                "reason_code": self._clean_text(
                    recommendation_payload.get("reason_code")
                ),
                "expected_stockout_risk": self._safe_number(
                    recommendation_payload.get("expected_stockout_risk")
                ),
                "expected_service_level": self._safe_number(
                    recommendation_payload.get("expected_service_level")
                ),
            },
            "workflow_overview": {
                "task_type": task_type,
                "workflow_trace": workflow_trace,
                "warnings": warnings,
                "rationale_points": rationale_points,
            },
            "debug": {
                "request": {
                    "question": request.question,
                    "user_role": request.user_role,
                    "region_scope": request.region_scope,
                    "product_id": request.product_id,
                    "store_id": request.store_id,
                    "warehouse_id": request.warehouse_id,
                    "region_id": request.region_id,
                    "horizon_days": request.horizon_days,
                    "include_recommendations": request.include_recommendations,
                    "require_approval": request.require_approval,
                    "metadata": request.metadata,
                },
                "raw_summary": raw_summary,
            },
            # =====================================================
            # Backward-compatible keys for current UI
            # Keep these until the React page is cleaned.
            # =====================================================
            "workflow_trace": workflow_trace,
            "warnings": warnings,
            "planner_plan": planner_plan,
            "reasoning_result": reasoning_result,
            "analytics_result": analytics_result,
            "execution_result": execution_result,
        }

        return response

    def _as_dict(self, value: Any) -> Dict[str, Any]:
        """Safely normalize any value into a dictionary."""
        return value if isinstance(value, dict) else {}

    def _as_list(self, value: Any) -> List[Any]:
        """Safely normalize any value into a list."""
        return value if isinstance(value, list) else []

    def _clean_text(self, value: Any) -> Optional[str]:
        """Normalize text values for API output."""
        if value is None:
            return None

        if not isinstance(value, str):
            value = str(value)

        normalized = " ".join(value.strip().split())
        return normalized or None

    def _safe_number(self, value: Any) -> Optional[float]:
        """Normalize numeric-like values to float where possible."""
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None


# =========================================================
# Builder
# =========================================================
def build_agent_workflow_service(
    *,
    retrieval_service: RetrievalServiceProtocol,
    forecast_service: ForecastServiceProtocol,
) -> AgentWorkflowService:
    """
    Factory function for consistent AgentWorkflowService creation.
    """
    return AgentWorkflowService(
        retrieval_service=retrieval_service,
        forecast_service=forecast_service,
    )