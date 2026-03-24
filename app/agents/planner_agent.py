# app\agents\planner_agent.py

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# Planning enums
# =========================================================
class TaskType(str, Enum):
    """High-level task categories for EDIP planning."""

    RAG_QA = "rag_qa"
    ANALYTICS = "analytics"
    HYBRID = "hybrid"
    EXECUTION = "execution"
    UNKNOWN = "unknown"


class AgentStep(str, Enum):
    """Possible downstream steps in the EDIP multi-agent workflow."""

    RETRIEVAL = "retrieval"
    REASONING = "reasoning"
    ANALYTICS = "analytics"
    EXECUTION = "execution"


# =========================================================
# Data models
# =========================================================
@dataclass(frozen=True)
class PlannerInput:
    """Input payload for the planner agent."""

    question: str
    user_role: Optional[str] = None
    region_scope: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PlannerPlan:
    """Structured planning output for downstream EDIP agents."""

    original_question: str
    normalized_question: str
    task_type: TaskType
    steps: List[AgentStep]
    needs_retrieval: bool
    needs_reasoning: bool
    needs_analytics: bool
    needs_execution: bool
    knowledge_domains: List[str]
    notes: List[str] = field(default_factory=list)


# =========================================================
# Planner agent
# =========================================================
class PlannerAgent:
    """
    EDIP Planner Agent.

    Purpose:
    - inspect the incoming business question
    - identify the main task type
    - decide which downstream agents should run
    - return a structured plan for orchestration
    """

    def __init__(self) -> None:
        logger.info("PlannerAgent initialized.")

    def plan(self, payload: PlannerInput) -> PlannerPlan:
        """
        Create a routing plan for the current user request.
        """
        normalized_question = self._normalize_text(payload.question)

        if not normalized_question:
            logger.warning("Planner received an empty question.")
            return PlannerPlan(
                original_question=payload.question,
                normalized_question=normalized_question,
                task_type=TaskType.UNKNOWN,
                steps=[],
                needs_retrieval=False,
                needs_reasoning=False,
                needs_analytics=False,
                needs_execution=False,
                knowledge_domains=[],
                notes=["Question is empty or invalid."],
            )

        task_type = self._detect_task_type(normalized_question)
        steps = self._build_steps(task_type)
        knowledge_domains = self._detect_knowledge_domains(normalized_question)
        notes = self._build_notes(task_type, knowledge_domains)

        plan = PlannerPlan(
            original_question=payload.question,
            normalized_question=normalized_question,
            task_type=task_type,
            steps=steps,
            needs_retrieval=AgentStep.RETRIEVAL in steps,
            needs_reasoning=AgentStep.REASONING in steps,
            needs_analytics=AgentStep.ANALYTICS in steps,
            needs_execution=AgentStep.EXECUTION in steps,
            knowledge_domains=knowledge_domains,
            notes=notes,
        )

        logger.info(
            "Planner created plan | task_type=%s | steps=%s | domains=%s",
            plan.task_type.value,
            [step.value for step in plan.steps],
            plan.knowledge_domains,
        )
        return plan

    # =========================================================
    # Internal helpers
    # =========================================================
    def _normalize_text(self, text: str) -> str:
        """
        Normalize user input for planning.
        """
        return " ".join(text.strip().lower().split())

    def _detect_task_type(self, question: str) -> TaskType:
        """
        Detect the main task type using simple enterprise-safe rules.

        This is rule-based in v1.
        Later, we can replace or enhance this with an LLM planner.
        """
        analytics_keywords = {
            "forecast",
            "predict",
            "prediction",
            "demand",
            "replenishment",
            "inventory",
            "stockout",
            "risk",
            "trend",
            "simulate",
            "scenario",
            "what-if",
            "recommendation",
        }

        rag_keywords = {
            "policy",
            "sop",
            "rule",
            "guideline",
            "playbook",
            "why",
            "explain",
            "reason",
            "document",
            "memo",
            "review",
            "approval",
            "escalation",
        }

        execution_keywords = {
            "trigger",
            "send",
            "create action",
            "raise alert",
            "notify",
            "approve",
            "escalate",
            "execute",
            "run workflow",
        }

        has_analytics = any(keyword in question for keyword in analytics_keywords)
        has_rag = any(keyword in question for keyword in rag_keywords)
        has_execution = any(keyword in question for keyword in execution_keywords)

        if has_execution:
            return TaskType.EXECUTION

        if has_analytics and has_rag:
            return TaskType.HYBRID

        if has_analytics:
            return TaskType.ANALYTICS

        if has_rag:
            return TaskType.RAG_QA

        return TaskType.UNKNOWN

    def _build_steps(self, task_type: TaskType) -> List[AgentStep]:
        """
        Convert task type into downstream agent steps.
        """
        if task_type == TaskType.RAG_QA:
            return [
                AgentStep.RETRIEVAL,
                AgentStep.REASONING,
            ]

        if task_type == TaskType.ANALYTICS:
            return [
                AgentStep.ANALYTICS,
                AgentStep.REASONING,
            ]

        if task_type == TaskType.HYBRID:
            return [
                AgentStep.RETRIEVAL,
                AgentStep.ANALYTICS,
                AgentStep.REASONING,
            ]

        if task_type == TaskType.EXECUTION:
            return [
                AgentStep.RETRIEVAL,
                AgentStep.REASONING,
                AgentStep.EXECUTION,
            ]

        return [AgentStep.REASONING]

    def _detect_knowledge_domains(self, question: str) -> List[str]:
        """
        Detect business knowledge domains that may be relevant for retrieval.
        """
        domain_keywords = {
            "replenishment": ["replenishment", "stock", "inventory", "warehouse"],
            "forecasting": ["forecast", "prediction", "demand", "trend"],
            "pricing": ["price", "discount", "promotion"],
            "supplier": ["supplier", "lead time", "shipment", "sla"],
            "governance": ["approval", "policy", "escalation", "override", "audit"],
            "sales": ["sales", "order", "return", "customer"],
        }

        matched_domains: List[str] = []

        for domain, keywords in domain_keywords.items():
            if any(keyword in question for keyword in keywords):
                matched_domains.append(domain)

        return matched_domains

    def _build_notes(self, task_type: TaskType, knowledge_domains: List[str]) -> List[str]:
        """
        Add planning notes for downstream agents or audit visibility.
        """
        notes: List[str] = []

        if task_type == TaskType.UNKNOWN:
            notes.append("No strong task pattern detected; use default reasoning flow.")

        if not knowledge_domains:
            notes.append("No specific business domain detected from question text.")

        if task_type == TaskType.HYBRID:
            notes.append("This request needs both enterprise retrieval and analytics support.")

        if task_type == TaskType.EXECUTION:
            notes.append("Execution requests should pass governance and approval checks first.")

        return notes


# =========================================================
# Builder
# =========================================================
def build_planner_agent() -> PlannerAgent:
    """Factory function for consistent agent creation."""
    return PlannerAgent()