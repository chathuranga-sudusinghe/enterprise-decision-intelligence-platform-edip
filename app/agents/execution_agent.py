from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.agents.analytics_agent import AnalyticsAgentResult
from app.agents.planner_agent import AgentStep, PlannerPlan, TaskType
from app.agents.reasoning_agent import ReasoningAgentResult
from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# Execution enums
# =========================================================
class ExecutionOutputType(str, Enum):
    """High-level execution output categories for EDIP."""

    EXPLANATION = "explanation"
    RECOMMENDATION = "recommendation"
    ALERT = "alert"
    ESCALATION = "escalation"
    REPORT = "report"
    NO_ACTION = "no_action"


class ExecutionStatus(str, Enum):
    """Execution result status."""

    READY = "ready"
    REVIEW_REQUIRED = "review_required"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


# =========================================================
# Data models
# =========================================================
@dataclass(frozen=True)
class ExecutionAction:
    """Normalized business action item produced by the Execution Agent."""

    action_type: str
    title: str
    description: str
    priority: str = "medium"
    owner_role: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuditRecord:
    """Simple audit-friendly execution summary."""

    task_type: str
    output_type: str
    status: str
    risk_flags: List[str]
    action_count: int
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExecutionAgentInput:
    """Input payload for the Execution Agent."""

    question: str
    plan: PlannerPlan
    reasoning_result: Optional[ReasoningAgentResult] = None
    analytics_result: Optional[AnalyticsAgentResult] = None
    user_role: Optional[str] = None
    require_approval: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionAgentResult:
    """Final structured execution output."""

    question: str
    output_type: ExecutionOutputType
    status: ExecutionStatus
    final_message: str
    actions: List[ExecutionAction]
    alerts: List[str]
    escalation_required: bool
    audit_record: AuditRecord
    warnings: List[str] = field(default_factory=list)


# =========================================================
# Execution agent
# =========================================================
class ExecutionAgent:
    """
    EDIP Execution Agent.

    Responsibilities:
    - convert reasoning and analytics results into business-friendly outputs
    - package recommendations, alerts, escalations, or no-action responses
    - produce audit-friendly final output for APIs and downstream systems
    """

    def __init__(self) -> None:
        logger.info("ExecutionAgent initialized.")

    def execute(self, payload: ExecutionAgentInput) -> ExecutionAgentResult:
        """
        Build the final decision/action package for the current workflow.
        """
        normalized_question = self._validate_question(payload.question)
        warnings: List[str] = []

        reasoning_result = payload.reasoning_result
        analytics_result = payload.analytics_result

        risk_flags = reasoning_result.risk_flags if reasoning_result else []
        escalation_required = self._is_escalation_required(
            risk_flags=risk_flags,
            require_approval=payload.require_approval,
            plan=payload.plan,
            analytics_result=analytics_result,
        )

        output_type = self._resolve_output_type(
            plan=payload.plan,
            reasoning_result=reasoning_result,
            analytics_result=analytics_result,
            escalation_required=escalation_required,
        )

        actions = self._build_actions(
            payload=payload,
            output_type=output_type,
            escalation_required=escalation_required,
        )

        alerts = self._build_alerts(
            reasoning_result=reasoning_result,
            analytics_result=analytics_result,
            escalation_required=escalation_required,
        )

        if reasoning_result is None:
            warnings.append("Reasoning result was not supplied to execution.")

        if payload.plan.needs_analytics and analytics_result is None:
            warnings.append("Planner expected analytics, but analytics result was not supplied.")

        if analytics_result and analytics_result.analytics_used is False:
            warnings.append("Analytics stage completed without usable analytical output.")

        if self._has_high_operational_risk(analytics_result):
            warnings.append(
                "High operational risk was detected, but the recommendation remains actionable."
            )

        status = self._resolve_status(
            output_type=output_type,
            escalation_required=escalation_required,
            require_approval=payload.require_approval,
            actions=actions,
            warnings=warnings,
        )

        final_message = self._build_final_message(
            output_type=output_type,
            status=status,
            reasoning_result=reasoning_result,
            analytics_result=analytics_result,
            escalation_required=escalation_required,
        )

        audit_record = AuditRecord(
            task_type=payload.plan.task_type.value,
            output_type=output_type.value,
            status=status.value,
            risk_flags=risk_flags,
            action_count=len(actions),
            notes=self._build_audit_notes(
                payload=payload,
                escalation_required=escalation_required,
                warnings=warnings,
            ),
        )

        result = ExecutionAgentResult(
            question=normalized_question,
            output_type=output_type,
            status=status,
            final_message=final_message,
            actions=actions,
            alerts=alerts,
            escalation_required=escalation_required,
            audit_record=audit_record,
            warnings=warnings,
        )

        logger.info(
            "ExecutionAgent completed | output_type=%s | status=%s | action_count=%s | escalation_required=%s",
            result.output_type.value,
            result.status.value,
            len(result.actions),
            result.escalation_required,
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
            raise ValueError("Question cannot be empty for execution.")
        return normalized

    def _is_escalation_required(
        self,
        *,
        risk_flags: List[str],
        require_approval: bool,
        plan: PlannerPlan,
        analytics_result: Optional[AnalyticsAgentResult],
    ) -> bool:
        """
        Decide whether this workflow should escalate.

        Important policy:
        - governance / approval / hard control issues => escalate
        - high operational risk alone => warn, but do not automatically escalate
        """
        governance_risks = {
            "governance_review",
            "governance_review_needed",
            "supplier_dependency_risk",
            "supplier_risk",
            "policy_exception",
            "approval_required",
            "compliance_risk",
        }

        if require_approval:
            return True

        if any(flag in governance_risks for flag in risk_flags):
            return True

        if plan.task_type == TaskType.EXECUTION:
            return True

        # Do not escalate only because stockout risk or service level risk is high.
        # Those should usually remain actionable recommendation cases.
        return False

    def _resolve_output_type(
        self,
        *,
        plan: PlannerPlan,
        reasoning_result: Optional[ReasoningAgentResult],
        analytics_result: Optional[AnalyticsAgentResult],
        escalation_required: bool,
    ) -> ExecutionOutputType:
        """
        Resolve the final output type.
        """
        if escalation_required:
            return ExecutionOutputType.ESCALATION

        if analytics_result and analytics_result.analytics_used:
            if analytics_result.recommendation_payload:
                return ExecutionOutputType.RECOMMENDATION
            return ExecutionOutputType.REPORT

        if reasoning_result and reasoning_result.evidence:
            if plan.task_type == TaskType.RAG_QA:
                return ExecutionOutputType.EXPLANATION
            return ExecutionOutputType.REPORT

        if reasoning_result and reasoning_result.reasoning_summary:
            return ExecutionOutputType.EXPLANATION

        return ExecutionOutputType.NO_ACTION

    def _build_actions(
        self,
        *,
        payload: ExecutionAgentInput,
        output_type: ExecutionOutputType,
        escalation_required: bool,
    ) -> List[ExecutionAction]:
        """
        Build normalized execution actions.
        """
        actions: List[ExecutionAction] = []

        reasoning_result = payload.reasoning_result
        analytics_result = payload.analytics_result

        if escalation_required:
            actions.append(
                ExecutionAction(
                    action_type="escalate_case",
                    title="Escalate decision workflow",
                    description=(
                        "Escalate this case for governance, planner, or manager review "
                        "before final operational action."
                    ),
                    priority="high",
                    owner_role="manager",
                    metadata={
                        "risk_flags": reasoning_result.risk_flags if reasoning_result else [],
                    },
                )
            )

        if analytics_result and analytics_result.recommendation_payload:
            recommendation_payload = analytics_result.recommendation_payload
            priority = self._resolve_priority(recommendation_payload)

            recommended_order_qty = recommendation_payload.get("recommended_order_qty")
            if recommended_order_qty is not None:
                actions.append(
                    ExecutionAction(
                        action_type="create_replenishment_recommendation",
                        title="Create replenishment recommendation",
                        description=f"Recommend order quantity of {recommended_order_qty}.",
                        priority=priority,
                        owner_role="planner",
                        metadata=recommendation_payload,
                    )
                )

            recommended_transfer_qty = recommendation_payload.get("recommended_transfer_qty")
            if recommended_transfer_qty is not None:
                try:
                    transfer_qty_value = float(recommended_transfer_qty)
                except (TypeError, ValueError):
                    transfer_qty_value = 0.0

                if transfer_qty_value > 0:
                    actions.append(
                        ExecutionAction(
                            action_type="create_transfer_recommendation",
                            title="Create stock transfer recommendation",
                            description=f"Recommend transfer quantity of {recommended_transfer_qty}.",
                            priority=priority,
                            owner_role="inventory_controller",
                            metadata=recommendation_payload,
                        )
                    )

        if output_type == ExecutionOutputType.EXPLANATION and reasoning_result:
            actions.append(
                ExecutionAction(
                    action_type="return_explanation",
                    title="Return grounded explanation",
                    description="Return a business-friendly grounded explanation to the user.",
                    priority="low",
                    owner_role=payload.user_role,
                    metadata={
                        "rationale_points": reasoning_result.rationale_points,
                    },
                )
            )

        return actions

    def _build_alerts(
        self,
        *,
        reasoning_result: Optional[ReasoningAgentResult],
        analytics_result: Optional[AnalyticsAgentResult],
        escalation_required: bool,
    ) -> List[str]:
        """
        Build alert messages from reasoning and analytics results.
        """
        alerts: List[str] = []

        if reasoning_result:
            for risk_flag in reasoning_result.risk_flags:
                alerts.append(f"Risk detected: {risk_flag}")

        if analytics_result and analytics_result.recommendation_payload:
            recommendation_payload = analytics_result.recommendation_payload

            for key in [
                "priority_level",
                "reason_code",
                "expected_stockout_risk",
                "expected_service_level",
            ]:
                if recommendation_payload.get(key) is not None:
                    alerts.append(f"{key}: {recommendation_payload.get(key)}")

        if escalation_required:
            alerts.append("Escalation is required before final action.")

        return alerts

    def _resolve_status(
        self,
        *,
        output_type: ExecutionOutputType,
        escalation_required: bool,
        require_approval: bool,
        actions: List[ExecutionAction],
        warnings: List[str],
    ) -> ExecutionStatus:
        """
        Resolve execution status.
        """
        if escalation_required or require_approval:
            return ExecutionStatus.REVIEW_REQUIRED

        if output_type == ExecutionOutputType.NO_ACTION:
            return ExecutionStatus.SKIPPED

        if not actions and warnings:
            return ExecutionStatus.BLOCKED

        if output_type == ExecutionOutputType.RECOMMENDATION and actions:
            return ExecutionStatus.READY

        if output_type == ExecutionOutputType.EXPLANATION and actions:
            return ExecutionStatus.READY

        if output_type == ExecutionOutputType.REPORT:
            return ExecutionStatus.READY

        if not actions:
            return ExecutionStatus.BLOCKED

        return ExecutionStatus.READY

    def _build_final_message(
        self,
        *,
        output_type: ExecutionOutputType,
        status: ExecutionStatus,
        reasoning_result: Optional[ReasoningAgentResult],
        analytics_result: Optional[AnalyticsAgentResult],
        escalation_required: bool,
    ) -> str:
        """
        Build the final user/business-facing message.
        """
        if output_type == ExecutionOutputType.ESCALATION:
            return (
                "The workflow identified governance or approval-sensitive risk, "
                "so the case should be reviewed before final action."
            )

        if output_type == ExecutionOutputType.RECOMMENDATION and analytics_result:
            recommendation_payload = analytics_result.recommendation_payload or {}
            priority_level = recommendation_payload.get("priority_level")
            reason_code = recommendation_payload.get("reason_code")

            if priority_level or reason_code:
                return (
                    "The system produced a prescriptive recommendation package "
                    f"with priority '{priority_level}' and reason code '{reason_code}'."
                )

            return (
                "The system produced a prescriptive recommendation package based on "
                "analytics and reasoning outputs."
            )

        if output_type == ExecutionOutputType.EXPLANATION and reasoning_result:
            return reasoning_result.reasoning_summary

        if output_type == ExecutionOutputType.REPORT:
            return "The workflow completed and returned an audit-friendly decision summary."

        if status == ExecutionStatus.SKIPPED:
            return "No final business action was required for the current request."

        return "Execution completed with limited actionable output."

    def _build_audit_notes(
        self,
        *,
        payload: ExecutionAgentInput,
        escalation_required: bool,
        warnings: List[str],
    ) -> List[str]:
        """
        Build small audit notes.
        """
        notes: List[str] = []

        if payload.plan.notes:
            notes.extend(payload.plan.notes)

        if escalation_required:
            notes.append("Escalation path activated by governance/approval conditions.")

        if payload.require_approval:
            notes.append("Manual approval is required before downstream action.")

        notes.extend(warnings)
        return notes

    def _resolve_priority(self, recommendation_payload: Dict[str, Any]) -> str:
        """
        Resolve action priority from recommendation payload.
        """
        priority = recommendation_payload.get("priority_level")
        if priority is None:
            return "medium"

        priority_text = str(priority).strip().lower()
        if priority_text in {"low", "medium", "high", "critical"}:
            return priority_text

        return "medium"

    def _has_high_operational_risk(
        self,
        analytics_result: Optional[AnalyticsAgentResult],
    ) -> bool:
        """
        Detect high operational risk from recommendation payload.

        This should warn, but not automatically escalate.
        """
        if analytics_result is None or not analytics_result.recommendation_payload:
            return False

        recommendation_payload = analytics_result.recommendation_payload

        stockout_risk = self._as_float(recommendation_payload.get("expected_stockout_risk"))
        service_level = self._as_float(recommendation_payload.get("expected_service_level"))
        priority_level = self._normalize_text(recommendation_payload.get("priority_level"))

        if stockout_risk is not None and stockout_risk >= 0.90:
            return True

        if service_level is not None and service_level < 0.20:
            return True

        if priority_level in {"high", "critical"}:
            return True

        return False

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
        Normalize text-like values.
        """
        if value is None:
            return None

        text = " ".join(str(value).strip().split()).lower()
        return text or None


# =========================================================
# Builder
# =========================================================
def build_execution_agent() -> ExecutionAgent:
    """Factory function for consistent Execution Agent creation."""
    return ExecutionAgent()