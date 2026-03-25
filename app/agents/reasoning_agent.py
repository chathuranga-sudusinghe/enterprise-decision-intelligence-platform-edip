from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.agents.planner_agent import PlannerPlan, TaskType
from app.agents.retrieval_agent import RetrievalAgentResult, RetrievedChunk
from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# Data models
# =========================================================
@dataclass(frozen=True)
class StructuredSignal:
    """
    Normalized structured signal used by the Reasoning Agent.

    This can come from analytics, rules, KPIs, or other structured sources.
    """

    signal_name: str
    signal_value: Any
    signal_type: str = "business_signal"
    source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceItem:
    """
    Compact evidence item derived from retrieval output.
    """

    chunk_id: Optional[str]
    document_title: Optional[str]
    document_type: Optional[str]
    business_domain: Optional[str]
    topic: Optional[str]
    score: float
    excerpt: str


@dataclass(frozen=True)
class ReasoningAgentInput:
    """
    Input payload for the Reasoning Agent.
    """

    question: str
    plan: PlannerPlan
    retrieval_result: Optional[RetrievalAgentResult] = None
    structured_signals: List[StructuredSignal] = field(default_factory=list)


@dataclass(frozen=True)
class ReasoningAgentResult:
    """
    Final structured output from the Reasoning Agent.
    """

    question: str
    task_type: TaskType
    reasoning_summary: str
    rationale_points: List[str]
    risk_flags: List[str]
    suggested_next_steps: List[str]
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
    - interpret planner intent
    - combine retrieval evidence with structured signals
    - produce business-facing reasoning
    - identify risk flags
    - generate context-aware warnings
    """

    def __init__(self) -> None:
        logger.info("ReasoningAgent initialized.")

    def reason(self, payload: ReasoningAgentInput) -> ReasoningAgentResult:
        """
        Build grounded business reasoning from planner output, retrieval evidence,
        and structured business signals.
        """
        normalized_question = self._validate_question(payload.question)

        evidence = self._build_evidence_items(payload.retrieval_result)
        signal_summary = self._summarize_structured_signals(payload.structured_signals)
        rationale_points = self._build_rationale_points(
            plan=payload.plan,
            evidence=evidence,
            signal_summary=signal_summary,
        )
        risk_flags = self._build_risk_flags(
            plan=payload.plan,
            evidence=evidence,
            signal_summary=signal_summary,
        )
        suggested_next_steps = self._build_suggested_next_steps(
            plan=payload.plan,
            evidence=evidence,
            signal_summary=signal_summary,
            risk_flags=risk_flags,
        )

        reasoning_summary = self._build_reasoning_summary(
            plan=payload.plan,
            evidence=evidence,
            signal_summary=signal_summary,
            risk_flags=risk_flags,
        )

        warnings = self._build_warnings(
            plan=payload.plan,
            retrieval_result=payload.retrieval_result,
            evidence=evidence,
            signal_summary=signal_summary,
        )

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
            "ReasoningAgent completed | task_type=%s | evidence_count=%s | signal_count=%s | risks=%s | warnings=%s",
            result.task_type.value,
            len(result.evidence),
            len(result.structured_signal_summary),
            result.risk_flags,
            len(result.warnings),
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
        Convert retrieval chunks into compact evidence items.
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
                    score=float(chunk.score or 0.0),
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
        Build short business rationale points.
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
        elif plan.task_type == TaskType.ANALYTICS:
            points.append(
                "This request mainly requires analytical interpretation of business signals."
            )
        elif plan.task_type == TaskType.HYBRID:
            points.append(
                "This request requires both enterprise document context and analytical support."
            )

        return points

    def _build_risk_flags(
        self,
        plan: PlannerPlan,
        evidence: List[EvidenceItem],
        signal_summary: Dict[str, Any],
    ) -> List[str]:
        """
        Build risk flags from planner context plus structured signals.
        """
        risk_flags: List[str] = []

        # Planner-level approval / governance signal.
        if getattr(plan, "needs_execution", False) and getattr(plan, "needs_reasoning", False):
            risk_flags.append("governance_review")

        # Structured signal heuristics.
        stockout_risk = self._as_float(signal_summary.get("expected_stockout_risk"))
        service_level = self._as_float(signal_summary.get("expected_service_level"))
        confidence_score = self._as_float(signal_summary.get("confidence_score"))
        priority_level = self._normalize_text(signal_summary.get("priority_level"))

        if stockout_risk is not None and stockout_risk >= 0.70:
            risk_flags.append("stockout_risk")

        if service_level is not None and service_level < 0.80:
            risk_flags.append("service_level_risk")

        if confidence_score is not None and confidence_score < 0.20:
            risk_flags.append("low_forecast_confidence")

        if priority_level == "high":
            risk_flags.append("urgent_priority")

        # Retrieval/evidence availability.
        if plan.task_type in {TaskType.RAG_QA, TaskType.HYBRID} and not evidence:
            risk_flags.append("limited_grounding")

        return sorted(set(risk_flags))

    def _build_suggested_next_steps(
        self,
        plan: PlannerPlan,
        evidence: List[EvidenceItem],
        signal_summary: Dict[str, Any],
        risk_flags: List[str],
    ) -> List[str]:
        """
        Suggest short next-step actions.
        """
        steps: List[str] = []

        if "stockout_risk" in risk_flags:
            steps.append("Review replenishment action immediately.")

        if "service_level_risk" in risk_flags:
            steps.append("Investigate service-level exposure before final action.")

        if "limited_grounding" in risk_flags:
            steps.append("Retrieve stronger enterprise evidence before policy-sensitive action.")

        if signal_summary:
            steps.append("Use structured analytics signals in the final execution decision.")

        if plan.task_type == TaskType.HYBRID:
            steps.append("Combine grounded policy context with analytical output before approval.")

        return steps

    def _build_reasoning_summary(
        self,
        plan: PlannerPlan,
        evidence: List[EvidenceItem],
        signal_summary: Dict[str, Any],
        risk_flags: List[str],
    ) -> str:
        """
        Build a cleaner business-facing reasoning summary.
        """
        evidence_count = len(evidence)
        signal_count = len(signal_summary)

        if plan.task_type == TaskType.ANALYTICS:
            base = (
                f"Reasoning used {signal_count} structured business signals "
                f"to interpret the analytical request."
            )
        elif plan.task_type == TaskType.RAG_QA:
            base = (
                f"Reasoning used {evidence_count} retrieved evidence items "
                f"to interpret the grounded business request."
            )
        else:
            base = (
                f"Reasoning combined {evidence_count} evidence items and "
                f"{signal_count} structured signals for a hybrid business interpretation."
            )

        if risk_flags:
            base += " Detected risk areas: " + ", ".join(risk_flags) + "."

        return base

    def _build_warnings(
        self,
        plan: PlannerPlan,
        retrieval_result: Optional[RetrievalAgentResult],
        evidence: List[EvidenceItem],
        signal_summary: Dict[str, Any],
    ) -> List[str]:
        """
        Build context-aware warnings.

        Important rule:
        - only warn about missing evidence when the task actually requires grounding
        - only warn about missing structured signals when the task actually requires analytics
        """
        warnings: List[str] = []

        needs_grounding = plan.task_type in {TaskType.RAG_QA, TaskType.HYBRID}
        needs_signals = plan.task_type in {TaskType.ANALYTICS, TaskType.HYBRID}

        retrieval_count = (
            retrieval_result.retrieval_count if retrieval_result is not None else 0
        )

        if needs_grounding and retrieval_count == 0 and not evidence:
            warnings.append("No retrieval evidence was available for reasoning.")

        if needs_signals and not signal_summary:
            warnings.append("No structured business signals were supplied to reasoning.")

        return warnings

    def _as_float(self, value: Any) -> Optional[float]:
        """
        Safely convert numeric-like values to float.
        """
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _normalize_text(self, value: Any) -> Optional[str]:
        """
        Normalize text-like values to lowercase text.
        """
        if value is None:
            return None

        text = " ".join(str(value).strip().split()).lower()
        return text or None


# =========================================================
# Builder
# =========================================================
def build_reasoning_agent() -> ReasoningAgent:
    """
    Factory function for consistent ReasoningAgent creation.
    """
    return ReasoningAgent()