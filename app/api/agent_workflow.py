from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.monitoring import record_workflow_error, record_workflow_run
from app.services.agent_workflow_service import (
    AgentWorkflowRequest,
    AgentWorkflowService,
    build_agent_workflow_service,
)
from app.services.forecast_service import build_forecast_service
from app.services.rag_query_service import build_rag_query_service


# =========================================================
# Router
# =========================================================
router = APIRouter(
    prefix="/agents/workflow",
    tags=["Agent Workflow"],
)


# =========================================================
# Request / Response Schemas
# =========================================================
class AgentWorkflowRunRequest(BaseModel):
    """
    API request schema for one EDIP multi-agent workflow run.
    """

    question: str = Field(
        ...,
        min_length=3,
        description="Business question for the EDIP multi-agent workflow.",
        examples=["Why was urgent replenishment recommended for SKU-100245?"],
    )
    user_role: Optional[str] = Field(
        default=None,
        description="Optional business role of the requester, for example planner.",
    )
    region_scope: Optional[str] = Field(
        default=None,
        description="Optional region scope such as west, east, or enterprise.",
    )

    product_id: Optional[int] = Field(
        default=None,
        description="Optional product identifier for scoped analytics and recommendations.",
    )
    store_id: Optional[int] = Field(
        default=None,
        description="Optional store identifier for scoped analytics and recommendations.",
    )
    warehouse_id: Optional[int] = Field(
        default=None,
        description="Optional warehouse identifier for scoped analytics and recommendations.",
    )
    region_id: Optional[int] = Field(
        default=None,
        description="Optional region identifier for scoped analytics and recommendations.",
    )

    horizon_days: int = Field(
        default=7,
        gt=0,
        description="Forecast horizon in days.",
    )
    include_recommendations: bool = Field(
        default=True,
        description="Whether the analytics step should include recommendation logic.",
    )
    require_approval: bool = Field(
        default=False,
        description="Whether the final workflow output should require approval handling.",
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional additional metadata for tracing, routing, or debugging.",
    )


class AgentWorkflowHealthResponse(BaseModel):
    """
    Health response for the EDIP multi-agent workflow API.
    """

    status: str = Field(..., description="Overall health status.")
    service: str = Field(..., description="Service name.")
    retrieval_ready: bool = Field(..., description="Whether retrieval service can be built.")
    forecast_ready: bool = Field(..., description="Whether forecast service can be built.")
    workflow_ready: bool = Field(..., description="Whether workflow service can be built.")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional diagnostic details.",
    )


class RagRetrievalAdapter:
    """
    Temporary adapter to make RagQueryService compatible with
    RetrievalServiceProtocol expected by RetrievalAgent.
    """

    def __init__(self, rag_query_service: Any) -> None:
        self.rag_query_service = rag_query_service

    def retrieve_context(
        self,
        question: str,
        *,
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
    ) -> list[dict]:
        if hasattr(self.rag_query_service, "retrieve_context"):
            return self.rag_query_service.retrieve_context(
                question,
                top_k=top_k,
                metadata_filter=metadata_filter,
                min_score=min_score,
            )

        if hasattr(self.rag_query_service, "answer_question"):
            rag_result = self.rag_query_service.answer_question(
                question,
                top_k=top_k,
                metadata_filter=metadata_filter,
                min_score=min_score,
            )

            normalized_matches: list[dict] = []
            sources = getattr(rag_result, "sources", []) or []

            for source in sources:
                metadata = {
                    "chunk_id": getattr(source, "chunk_id", None),
                    "document_id": getattr(source, "document_id", None),
                    "document_title": getattr(source, "document_title", None),
                    "source_path": getattr(source, "source_path", None),
                    "document_type": getattr(source, "document_type", None),
                    "business_domain": getattr(source, "business_domain", None),
                    "heading_path": getattr(source, "heading_path", None),
                    "topic": getattr(source, "topic", None),
                    "chunk_text": getattr(source, "text_preview", None),
                }

                normalized_matches.append(
                    {
                        "id": getattr(source, "chunk_id", None),
                        "score": float(getattr(source, "score", 0.0) or 0.0),
                        "metadata": metadata,
                    }
                )

            return normalized_matches

        raise RuntimeError(
            "RAG service does not expose retrieve_context(...) or answer_question(...)."
        )


# =========================================================
# Dependency builders
# =========================================================
def get_agent_workflow_service() -> AgentWorkflowService:
    """
    Build the EDIP agent workflow service using the project's real services.
    """
    rag_query_service = build_rag_query_service()
    forecast_service = build_forecast_service()

    retrieval_service = RagRetrievalAdapter(rag_query_service=rag_query_service)

    return build_agent_workflow_service(
        retrieval_service=retrieval_service,
        forecast_service=forecast_service,
    )


# =========================================================
# Monitoring helpers
# =========================================================
def _extract_scenario(metadata: Dict[str, Any]) -> str:
    """
    Extract workflow scenario safely from request metadata.
    """
    scenario = metadata.get("scenario")
    if isinstance(scenario, str) and scenario.strip():
        return scenario.strip()
    return "unknown"


def _extract_workflow_status(result: Dict[str, Any]) -> str:
    """
    Extract final workflow status safely from the workflow result.
    """
    decision_summary = result.get("decision_summary", {}) or {}
    status_value = decision_summary.get("status")

    if isinstance(status_value, str) and status_value.strip():
        return status_value.strip()

    execution_result = result.get("execution_result", {}) or {}
    execution_status = execution_result.get("status")

    if isinstance(execution_status, str) and execution_status.strip():
        return execution_status.strip()

    return "unknown"


# =========================================================
# Routes
# =========================================================
@router.get(
    "/health",
    response_model=AgentWorkflowHealthResponse,
    status_code=status.HTTP_200_OK,
)
def agent_workflow_health() -> AgentWorkflowHealthResponse:
    """
    Health check for the EDIP multi-agent workflow API.
    """
    details: Dict[str, Any] = {}

    retrieval_ready = False
    forecast_ready = False
    workflow_ready = False

    try:
        rag_query_service = build_rag_query_service()
        retrieval_ready = True
        details["retrieval_service"] = "ok"
    except Exception as exc:
        details["retrieval_service"] = f"failed: {exc}"

    try:
        forecast_service = build_forecast_service()
        forecast_ready = True
        details["forecast_service"] = "ok"
    except Exception as exc:
        details["forecast_service"] = f"failed: {exc}"

    if retrieval_ready and forecast_ready:
        try:
            retrieval_service = RagRetrievalAdapter(rag_query_service=rag_query_service)

            _ = build_agent_workflow_service(
                retrieval_service=retrieval_service,
                forecast_service=forecast_service,
            )
            workflow_ready = True
            details["workflow_service"] = "ok"
        except Exception as exc:
            details["workflow_service"] = f"failed: {exc}"
    else:
        details["workflow_service"] = "skipped"

    overall_ok = retrieval_ready and forecast_ready and workflow_ready

    return AgentWorkflowHealthResponse(
        status="ok" if overall_ok else "degraded",
        service="edip_agent_workflow_api",
        retrieval_ready=retrieval_ready,
        forecast_ready=forecast_ready,
        workflow_ready=workflow_ready,
        details=details,
    )


@router.post(
    "/run",
    status_code=status.HTTP_200_OK,
)
def run_agent_workflow(request: AgentWorkflowRunRequest) -> Dict[str, Any]:
    """
    Run one full EDIP agent workflow and return the serialized summary.
    """
    scenario = _extract_scenario(request.metadata)

    try:
        service = get_agent_workflow_service()

        workflow_request = AgentWorkflowRequest(
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

        result = service.run_workflow(workflow_request)

        reasoning_result = result.get("reasoning_result", {}) or {}
        execution_result = result.get("execution_result", {}) or {}

        result["business_answer"] = {
            "why": reasoning_result.get("reasoning_summary"),
            "decision": execution_result.get("final_message"),
            "recommendations": execution_result.get("recommendations"),
        }

        workflow_status = _extract_workflow_status(result)
        record_workflow_run(
            scenario=scenario,
            status=workflow_status,
        )

        return result

    except ValueError as exc:
        record_workflow_run(
            scenario=scenario,
            status="client_error",
        )
        record_workflow_error(scenario=scenario)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        record_workflow_run(
            scenario=scenario,
            status="server_error",
        )
        record_workflow_error(scenario=scenario)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow execution failed: {exc}",
        ) from exc