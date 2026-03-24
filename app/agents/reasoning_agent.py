from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from yaml import warnings

from app.agents.planner_agent import AgentStep, PlannerPlan, TaskType
from app.agents.retrieval_agent import RetrievalAgentResult, RetrievedChunk
from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# Data models
# =========================================================
@dataclass(frozen=True)
class StructuredSignal:
    """
    Optional structured business signal passed into reasoning.

    Example sources:
    - forecast service output
    - recommendation service output
    - event processing output
    - API-calculated business metrics
    """

    signal_name: str
    signal_value: Any
    signal_type: str = "generic"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReasoningAgentInput:
    """Input payload for the Reasoning Agent."""

    question: str
    plan: PlannerPlan
    retrieval_result: Optional[RetrievalAgentResult] = None
    structured_signals: List[StructuredSignal] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceItem:
    """Normalized evidence item used inside reasoning output."""

    chunk_id: Optional[str]
    document_title: Optional[str]
    document_type: Optional[str]
    business_domain: Optional[str]
    topic: Optional[str]
    score: float
    excerpt: str


@dataclass(frozen=True)
class ReasoningAgentResult:
    """Final structured reasoning output."""

    question: str
    task_type: TaskType
    reasoning_summary: str
    rationale_points: List[str]
    risk_flags: List[str]
    suggested_next_steps: List[AgentStep]
    evidence: List[EvidenceItem]
    structured_signal_summary: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)


# =========================================================
# Reasoning agent
# =========================================================
class ReasoningAgent:
    """
    EDIP Reasoning Agent.

    Responsibilities:
    - interpret grounded retrieval evidence
    - combine evidence with structured business signals
    - produce a clean reasoning layer for downstream analytics/execution
    """

    def __init__(self) -> None:
        logger.info("ReasoningAgent initialized.")

    def reason(self, payload: ReasoningAgentInput) -> ReasoningAgentResult:
        """
        Produce grounded reasoning from retrieved context and optional structured signals.
        """
        normalized_question = self._validate_question(payload.question)
        warnings: List[str] = []

        evidence = self._build_evidence_items(payload.retrieval_result)
        signal_summary = self._summarize_structured_signals(payload.structured_signals)
        rationale_points = self._build_rationale_points(
            plan=payload.plan,
            evidence=evidence,
            signal_summary=signal_summary,
        )
        risk_flags = self._detect_risk_flags(
            plan=payload.plan,
            evidence=evidence,
            signal_summary=signal_summary,
        )
        suggested_next_steps = self._build_suggested_next_steps(
            plan=payload.plan,
            evidence=evidence,
            signal_summary=signal_summary,
        )
        reasoning_summary = self._build_reasoning_summary(
            plan=payload.plan,
            evidence=evidence,
            signal_summary=signal_summary,
            risk_flags=risk_flags,
        )

        if not evidence:
            warnings.append("No retrieval evidence was available for reasoning.")

        if payload.plan.task_type == TaskType.ANALYTICS and not payload.structured_signals:
            warnings.append("No structured business signals were supplied to reasoning.")

        result = ReasoningAgentResult(
            question=normalized_question,
            task_type=payload.plan.task_type,
            reasoning_summary=reasoning_summary,
            rationale_points=rationale_points,
            risk_flags=risk_flags,
            suggested_next_steps=suggested_next_steps,
            evidence=evidence,
            structured_signal_summary=signal_summary,
            warnings=warnings,
        )

        logger.info(
            "ReasoningAgent completed | task_type=%s | evidence_count=%s | risks=%s",
            result.task_type.value,
            len(result.evidence),
            result.risk_flags,
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
            raise ValueError("Question cannot be empty for reasoning.")
        return normalized

    def _build_evidence_items(
        self,
        retrieval_result: Optional[RetrievalAgentResult],
    ) -> List[EvidenceItem]:
        """
        Convert retrieval chunks into reasoning evidence items.
        """
        if retrieval_result is None:
            return []

        evidence_items: List[EvidenceItem] = []

        for chunk in retrieval_result.chunks:
            evidence_items.append(
                EvidenceItem(
                    chunk_id=chunk.chunk_id,
                    document_title=chunk.document_title,
                    document_type=chunk.document_type,
                    business_domain=chunk.business_domain,
                    topic=chunk.topic,
                    score=chunk.score,
                    excerpt=self._build_excerpt(chunk),
                )
            )

        return evidence_items

    def _build_excerpt(self, chunk: RetrievedChunk, max_chars: int = 220) -> str:
        """
        Build a compact excerpt from retrieved chunk text.
        """
        text = " ".join(chunk.chunk_text.split())
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3].rstrip() + "..."

    def _summarize_structured_signals(
        self,
        structured_signals: List[StructuredSignal],
    ) -> Dict[str, Any]:
        """
        Convert structured signals into a compact summary dictionary.
        """
        summary: Dict[str, Any] = {}

        for signal in structured_signals:
            summary[signal.signal_name] = signal.signal_value

        return summary

    def _build_rationale_points(
        self,
        plan: PlannerPlan,
        evidence: List[EvidenceItem],
        signal_summary: Dict[str, Any],
    ) -> List[str]:
        """
        Build reasoning rationale points from evidence and signals.
        """
        points: List[str] = []

        if evidence:
            top_docs = [
                item.document_title
                for item in evidence[:3]
                if item.document_title
            ]
            if top_docs:
                points.append(
                    "Grounded reasoning is based on retrieved enterprise documents: "
                    + ", ".join(top_docs)
                    + "."
                )

        if plan.knowledge_domains:
            points.append(
                "The planner identified relevant business domains: "
                + ", ".join(plan.knowledge_domains)
                + "."
            )

        if signal_summary:
            points.append(
                "Structured business signals were provided to strengthen decision reasoning."
            )

        if plan.task_type == TaskType.RAG_QA:
            points.append(
                "This request mainly requires business-policy interpretation over grounded context."
            )

        if plan.task_type == TaskType.ANALYTICS:
            points.append(
                "This request mainly requires analytical interpretation of business signals."
            )

        if plan.task_type == TaskType.HYBRID:
            points.append(
                "This request requires both enterprise document context and analytical signals."
            )

        if plan.task_type == TaskType.EXECUTION:
            points.append(
                "This request may lead to action, so policy and governance consistency matter."
            )

        if not points:
            points.append(
                "Reasoning used default enterprise interpretation because strong evidence patterns were limited."
            )

        return points

    def _detect_risk_flags(
        self,
        plan: PlannerPlan,
        evidence: List[EvidenceItem],
        signal_summary: Dict[str, Any],
    ) -> List[str]:
        """
        Detect simple risk flags from question context, evidence, and signals.
        """
        risks: List[str] = []

        evidence_text = " ".join(
            [
                f"{item.document_title or ''} {item.topic or ''} {item.excerpt}"
                for item in evidence
            ]
        ).lower()

        if "escalation" in evidence_text or "approval" in evidence_text:
            risks.append("governance_review_needed")

        if "supplier" in evidence_text or "lead time" in evidence_text:
            risks.append("supplier_dependency_risk")

        if "stockout" in plan.normalized_question or "low stock" in plan.normalized_question:
            risks.append("service_level_risk")

        risk_like_signal_names = {
            "stockout_risk",
            "expected_stockout_risk",
            "forecast_uncertainty",
            "delay_risk",
            "supplier_risk",
        }

        for key, value in signal_summary.items():
            if key in risk_like_signal_names:
                risks.append(str(key))

        return sorted(set(risks))

    def _build_suggested_next_steps(
        self,
        plan: PlannerPlan,
        evidence: List[EvidenceItem],
        signal_summary: Dict[str, Any],
    ) -> List[AgentStep]:
        """
        Suggest the next workflow steps after reasoning.
        """
        next_steps: List[AgentStep] = []

        if plan.needs_analytics:
            next_steps.append(AgentStep.ANALYTICS)

        if plan.needs_execution:
            next_steps.append(AgentStep.EXECUTION)

        if not next_steps and signal_summary:
            next_steps.append(AgentStep.ANALYTICS)

        if not next_steps and evidence:
            next_steps.append(AgentStep.REASONING)

        return next_steps

    def _build_reasoning_summary(
        self,
        plan: PlannerPlan,
        evidence: List[EvidenceItem],
        signal_summary: Dict[str, Any],
        risk_flags: List[str],
    ) -> str:
        """
        Create one clean reasoning summary sentence block.
        """
        evidence_count = len(evidence)
        signal_count = len(signal_summary)

        if plan.task_type == TaskType.RAG_QA:
            summary = (
                f"Reasoning used {evidence_count} grounded document evidence items "
                f"to interpret the business question."
            )
        elif plan.task_type == TaskType.ANALYTICS:
            summary = (
                f"Reasoning used {signal_count} structured business signals "
                f"to interpret the analytical request."
            )
        elif plan.task_type == TaskType.HYBRID:
            summary = (
                f"Reasoning combined {evidence_count} evidence items and "
                f"{signal_count} structured signals for a hybrid business interpretation."
            )
        elif plan.task_type == TaskType.EXECUTION:
            summary = (
                f"Reasoning evaluated policy context and action implications before execution routing."
            )
        else:
            summary = "Reasoning completed with limited context using default enterprise-safe interpretation."

        if risk_flags:
            summary += " Detected risk areas: " + ", ".join(risk_flags) + "."

        return summary


# =========================================================
# Builder
# =========================================================
def build_reasoning_agent() -> ReasoningAgent:
    """Factory function for consistent agent creation."""
    return ReasoningAgent()