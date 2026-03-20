from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.rag import (
    RagHealthResponse,
    RagQueryRequest,
    RagQueryResponse,
    RagSourceResponse,
)
from app.services.rag_query_service import RagQueryService, build_rag_query_service


# =========================================================
# Logging
# =========================================================
logger = logging.getLogger(__name__)


# =========================================================
# Router
# =========================================================
router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)


# =========================================================
# Helper functions
# =========================================================
def _build_metadata_filter(request: RagQueryRequest) -> Dict[str, Any]:
    metadata_filter: Dict[str, Any] = {}

    filter_fields = {
        "document_type": request.document_type,
        "business_domain": request.business_domain,
        "region_scope": request.region_scope,
        "topic": request.topic,
        "owner_role": request.owner_role,
        "document_status": request.document_status,
        "approval_level": request.approval_level,
    }

    for key, value in filter_fields.items():
        if value is not None and str(value).strip():
            metadata_filter[key] = str(value).strip()

    return metadata_filter


def get_rag_query_service() -> RagQueryService:
    try:
        return build_rag_query_service()
    except Exception as exc:
        logger.exception("Failed to initialize RAG query service.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RAG service initialization failed.",
        ) from exc


# =========================================================
# Routes
# =========================================================
@router.get(
    "/health",
    response_model=RagHealthResponse,
    status_code=status.HTTP_200_OK,
)
def rag_health() -> RagHealthResponse:
    return RagHealthResponse(
        status="ok",
        service="edip_rag_api",
        retrieval_ready=True,
        generation_ready=True,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        details={},
    )


@router.post(
    "/query",
    response_model=RagQueryResponse,
    status_code=status.HTTP_200_OK,
)
def query_rag(
    request: RagQueryRequest,
    rag_service: RagQueryService = Depends(get_rag_query_service),
) -> RagQueryResponse:
    metadata_filter = _build_metadata_filter(request)

    try:
        result = rag_service.answer_question(
            question=request.question,
            top_k=request.top_k,
            metadata_filter=metadata_filter or None,
            min_score=request.min_score,
            temperature=request.temperature,
        )

        return RagQueryResponse(
            question=result.question,
            answer=result.answer,
            retrieval_count=result.retrieval_count,
            used_context_chars=result.used_context_chars,
            model_name=result.model_name,
            latency_ms=result.latency_ms,
            warnings=result.warnings,
            filters_applied=metadata_filter,
            sources=[
                RagSourceResponse(
                    chunk_id=source.chunk_id,
                    score=source.score,
                    document_id=source.document_id,
                    document_title=source.document_title,
                    source_path=source.source_path,
                    document_type=source.document_type,
                    business_domain=source.business_domain,
                    heading_path=source.heading_path,
                    topic=source.topic,
                    text_preview=source.text_preview,
                    metadata=source.metadata,
                )
                for source in result.sources
            ],
        )

    except ValueError as exc:
        logger.warning("Invalid RAG query request: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Unexpected error while processing RAG query.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while processing RAG query.",
        ) from exc