from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional, TypedDict

from app.agents.analytics_agent import (
    AnalyticsAgent,
    AnalyticsAgentInput,
    AnalyticsAgentResult,
)
from app.agents.execution_agent import (
    ExecutionAgent,
    ExecutionAgentInput,
    ExecutionAgentResult,
)
from app.agents.planner_agent import (
    AgentStep,
    PlannerAgent,
    PlannerInput,
    PlannerPlan,
)
from app.agents.reasoning_agent import (
    ReasoningAgent,
    ReasoningAgentInput,
    ReasoningAgentResult,
    StructuredSignal,
)
from app.agents.retrieval_agent import (
    RetrievalAgent,
    RetrievalAgentInput,
    RetrievalAgentResult,
)
from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# Optional LangGraph import
# =========================================================
try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover
    END = "__end__"
    StateGraph = None


# =========================================================
# Workflow state
# =========================================================
class WorkflowState(TypedDict, total=False):
    """
    Shared graph state for the EDIP multi-agent workflow.
    """

    # Original request
    question: str
    user_role: Optional[str]
    region_scope: Optional[str]
    product_id: Optional[int]
    store_id: Optional[int]
    warehouse_id: Optional[int]
    region_id: Optional[int]
    horizon_days: int
    include_recommendations: bool
    require_approval: bool
    metadata: Dict[str, Any]

    # Agent results
    planner_plan: Optional[PlannerPlan]
    retrieval_result: Optional[RetrievalAgentResult]
    reasoning_result: Optional[ReasoningAgentResult]
    analytics_result: Optional[AnalyticsAgentResult]
    execution_result: Optional[ExecutionAgentResult]

    # Runtime information
    workflow_trace: List[str]
    warnings: List[str]


# =========================================================
# Input / output helpers
# =========================================================
def build_initial_workflow_state(
    *,
    question: str,
    user_role: Optional[str] = None,
    region_scope: Optional[str] = None,
    product_id: Optional[int] = None,
    store_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    region_id: Optional[int] = None,
    horizon_days: int = 7,
    include_recommendations: bool = True,
    require_approval: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
) -> WorkflowState:
    """
    Build the initial workflow state for one EDIP request.
    """
    return {
        "question": question,
        "user_role": user_role,
        "region_scope": region_scope,
        "product_id": product_id,
        "store_id": store_id,
        "warehouse_id": warehouse_id,
        "region_id": region_id,
        "horizon_days": horizon_days,
        "include_recommendations": include_recommendations,
        "require_approval": require_approval,
        "metadata": metadata or {},
        "planner_plan": None,
        "retrieval_result": None,
        "reasoning_result": None,
        "analytics_result": None,
        "execution_result": None,
        "workflow_trace": [],
        "warnings": [],
    }


# =========================================================
# Workflow runner
# =========================================================
class EDIPLangGraphWorkflow:
    """
    EDIP LangGraph workflow runner.

    This class orchestrates:
    planner -> retrieval? -> reasoning -> analytics? -> execution
    """

    def __init__(
        self,
        *,
        planner_agent: PlannerAgent,
        retrieval_agent: RetrievalAgent,
        reasoning_agent: ReasoningAgent,
        analytics_agent: AnalyticsAgent,
        execution_agent: ExecutionAgent,
    ) -> None:
        self.planner_agent = planner_agent
        self.retrieval_agent = retrieval_agent
        self.reasoning_agent = reasoning_agent
        self.analytics_agent = analytics_agent
        self.execution_agent = execution_agent

        if StateGraph is None:
            raise ImportError(
                "LangGraph is not installed. Install it before using EDIPLangGraphWorkflow."
            )

        self.graph = self._build_graph()
        logger.info("EDIPLangGraphWorkflow initialized.")

    def _build_graph(self):
        """
        Build and compile the LangGraph workflow.
        """
        graph_builder = StateGraph(WorkflowState)

        graph_builder.add_node("planner", self._planner_node)
        graph_builder.add_node("retrieval", self._retrieval_node)
        graph_builder.add_node("reasoning", self._reasoning_node)
        graph_builder.add_node("analytics", self._analytics_node)
        graph_builder.add_node("execution", self._execution_node)

        graph_builder.set_entry_point("planner")

        graph_builder.add_conditional_edges(
            "planner",
            self._route_after_planner,
            {
                "retrieval": "retrieval",
                "reasoning": "reasoning",
            },
        )

        graph_builder.add_edge("retrieval", "reasoning")

        graph_builder.add_conditional_edges(
            "reasoning",
            self._route_after_reasoning,
            {
                "analytics": "analytics",
                "execution": "execution",
            },
        )

        graph_builder.add_edge("analytics", "execution")
        graph_builder.add_edge("execution", END)

        return graph_builder.compile()

    def invoke(self, state: WorkflowState) -> WorkflowState:
        """
        Run the full workflow.
        """
        logger.info("EDIP LangGraph workflow started.")
        final_state = self.graph.invoke(state)
        logger.info("EDIP LangGraph workflow completed.")
        return final_state

    # =========================================================
    # Graph nodes
    # =========================================================
    def _planner_node(self, state: WorkflowState) -> WorkflowState:
        """
        Planner node:
        classify the request and create the workflow plan.
        """
        question = state["question"]
        plan = self.planner_agent.plan(
            PlannerInput(
                question=question,
                user_role=state.get("user_role"),
                region_scope=state.get("region_scope"),
                metadata=self._safe_metadata(state),
            )
        )

        state["planner_plan"] = plan
        state["workflow_trace"] = state.get("workflow_trace", []) + ["planner"]
        logger.info(
            "Planner node completed | task_type=%s | steps=%s",
            plan.task_type.value,
            [step.value for step in plan.steps],
        )
        return state

    def _retrieval_node(self, state: WorkflowState) -> WorkflowState:
        """
        Retrieval node:
        fetch grounded enterprise context when the plan requires it.
        """
        plan = self._require_plan(state)
        question = state["question"]

        retrieval_result = self.retrieval_agent.retrieve(
            RetrievalAgentInput(
                question=question,
                plan=plan,
                user_role=state.get("user_role"),
                region_scope=state.get("region_scope"),
                top_k=5,
                min_score=0.0,
                extra_filters={},
            )
        )

        state["retrieval_result"] = retrieval_result
        state["workflow_trace"] = state.get("workflow_trace", []) + ["retrieval"]

        if retrieval_result.warnings:
            state["warnings"] = state.get("warnings", []) + retrieval_result.warnings

        logger.info(
            "Retrieval node completed | retrieval_count=%s",
            retrieval_result.retrieval_count,
        )
        return state

    def _reasoning_node(self, state: WorkflowState) -> WorkflowState:
        """
        Reasoning node:
        combine retrieval evidence and any structured signals to produce
        grounded business reasoning.
        """
        plan = self._require_plan(state)
        question = state["question"]

        structured_signals = self._build_reasoning_signals_from_analytics(state)

        reasoning_result = self.reasoning_agent.reason(
            ReasoningAgentInput(
                question=question,
                plan=plan,
                retrieval_result=state.get("retrieval_result"),
                structured_signals=structured_signals,
            )
        )

        state["reasoning_result"] = reasoning_result
        state["workflow_trace"] = state.get("workflow_trace", []) + ["reasoning"]

        if reasoning_result.warnings:
            state["warnings"] = state.get("warnings", []) + reasoning_result.warnings

        logger.info(
            "Reasoning node completed | risk_flags=%s",
            reasoning_result.risk_flags,
        )
        return state

    def _analytics_node(self, state: WorkflowState) -> WorkflowState:
        """
        Analytics node:
        call forecast/recommendation service when the workflow needs
        predictive or prescriptive support.
        """
        plan = self._require_plan(state)
        question = state["question"]

        analytics_result = self.analytics_agent.analyze(
            AnalyticsAgentInput(
                question=question,
                plan=plan,
                reasoning_result=state.get("reasoning_result"),
                product_id=state.get("product_id"),
                store_id=state.get("store_id"),
                warehouse_id=state.get("warehouse_id"),
                region_id=state.get("region_id"),
                horizon_days=state.get("horizon_days", 7),
                include_recommendations=state.get("include_recommendations", True),
                metadata=self._safe_metadata(state),
            )
        )

        state["analytics_result"] = analytics_result
        state["workflow_trace"] = state.get("workflow_trace", []) + ["analytics"]

        if analytics_result.warnings:
            state["warnings"] = state.get("warnings", []) + analytics_result.warnings

        logger.info(
            "Analytics node completed | analytics_mode=%s",
            analytics_result.analytics_mode,
        )
        return state

    def _execution_node(self, state: WorkflowState) -> WorkflowState:
        """
        Execution node:
        package final outputs, actions, alerts, and audit-friendly results.
        """
        plan = self._require_plan(state)
        question = state["question"]

        execution_result = self.execution_agent.execute(
            ExecutionAgentInput(
                question=question,
                plan=plan,
                reasoning_result=state.get("reasoning_result"),
                analytics_result=state.get("analytics_result"),
                user_role=state.get("user_role"),
                require_approval=state.get("require_approval", False),
                metadata=self._safe_metadata(state),
            )
        )

        state["execution_result"] = execution_result
        state["workflow_trace"] = state.get("workflow_trace", []) + ["execution"]

        if execution_result.warnings:
            state["warnings"] = state.get("warnings", []) + execution_result.warnings

        logger.info(
            "Execution node completed | output_type=%s | status=%s",
            execution_result.output_type.value,
            execution_result.status.value,
        )
        return state

    # =========================================================
    # Routing
    # =========================================================
    def _route_after_planner(self, state: WorkflowState) -> str:
        """
        Decide whether to go to retrieval or directly to reasoning.
        """
        plan = self._require_plan(state)

        if plan.needs_retrieval or AgentStep.RETRIEVAL in plan.steps:
            return "retrieval"

        return "reasoning"

    def _route_after_reasoning(self, state: WorkflowState) -> str:
        """
        Decide whether analytics is needed after reasoning.
        """
        plan = self._require_plan(state)

        if plan.needs_analytics or AgentStep.ANALYTICS in plan.steps:
            return "analytics"

        return "execution"

    # =========================================================
    # Internal helpers
    # =========================================================
    def _require_plan(self, state: WorkflowState) -> PlannerPlan:
        """
        Ensure planner output exists before downstream nodes run.
        """
        plan = state.get("planner_plan")
        if plan is None:
            raise ValueError("Workflow state is missing planner_plan.")
        return plan

    def _safe_metadata(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Safely return metadata dictionary.
        """
        return state.get("metadata", {}) or {}

    def _build_reasoning_signals_from_analytics(
        self,
        state: WorkflowState,
    ) -> List[StructuredSignal]:
        """
        Convert analytics signals into reasoning-compatible signals if needed.

        In v1 this usually returns an empty list before analytics runs,
        but the helper is here for safe future extension.
        """
        analytics_result = state.get("analytics_result")
        if analytics_result is None:
            return []

        signals: List[StructuredSignal] = []
        for signal in analytics_result.structured_signals:
            signals.append(
                StructuredSignal(
                    signal_name=signal.signal_name,
                    signal_value=signal.signal_value,
                    signal_type=signal.signal_type,
                    metadata=signal.metadata,
                )
            )
        return signals


# =========================================================
# Final result helper
# =========================================================
def summarize_workflow_result(state: WorkflowState) -> Dict[str, Any]:
    """
    Convert final workflow state into a clean serializable summary.
    """
    planner_plan = state.get("planner_plan")
    retrieval_result = state.get("retrieval_result")
    reasoning_result = state.get("reasoning_result")
    analytics_result = state.get("analytics_result")
    execution_result = state.get("execution_result")

    return {
        "question": state.get("question"),
        "workflow_trace": state.get("workflow_trace", []),
        "warnings": state.get("warnings", []),
        "planner_plan": asdict(planner_plan) if planner_plan else None,
        "retrieval_result": asdict(retrieval_result) if retrieval_result else None,
        "reasoning_result": asdict(reasoning_result) if reasoning_result else None,
        "analytics_result": asdict(analytics_result) if analytics_result else None,
        "execution_result": asdict(execution_result) if execution_result else None,
    }


# =========================================================
# Builder
# =========================================================
def build_edip_langgraph_workflow(
    *,
    planner_agent: PlannerAgent,
    retrieval_agent: RetrievalAgent,
    reasoning_agent: ReasoningAgent,
    analytics_agent: AnalyticsAgent,
    execution_agent: ExecutionAgent,
) -> EDIPLangGraphWorkflow:
    """
    Factory for consistent EDIP LangGraph workflow creation.
    """
    return EDIPLangGraphWorkflow(
        planner_agent=planner_agent,
        retrieval_agent=retrieval_agent,
        reasoning_agent=reasoning_agent,
        analytics_agent=analytics_agent,
        execution_agent=execution_agent,
    )