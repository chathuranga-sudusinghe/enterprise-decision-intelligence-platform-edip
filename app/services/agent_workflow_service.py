# app/services/agent_workflow_service.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

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
        summary = summarize_workflow_result(final_state)

        logger.info(
            "Agent workflow execution completed | trace=%s | warnings=%s",
            summary.get("workflow_trace", []),
            len(summary.get("warnings", [])),
        )
        return summary

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