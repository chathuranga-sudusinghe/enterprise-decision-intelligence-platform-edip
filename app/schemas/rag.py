# app\schemas\rag.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# =========================================================
# Shared base
# =========================================================
class RagBaseSchema(BaseModel):
    """
    Shared safe config for EDIP RAG schemas.

    Why:
    - extra="ignore" helps avoid response/model crashes during
      ongoing refactors if an extra field appears temporarily.
    - populate_by_name=True helps future alias support safely.
    """
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )


# =========================================================
# Request schema
# =========================================================
class RagQueryRequest(RagBaseSchema):
    question: str = Field(
        ...,
        min_length=3,
        description="Business question to answer using EDIP RAG retrieval and grounded generation.",
        examples=["Why was urgent replenishment recommended for SKU-100245?"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of retrieved chunks to consider.",
    )
    min_score: float = Field(
        default=0.0,
        ge=0.0,
        description="Minimum retrieval score threshold.",
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="LLM generation temperature for grounded answering.",
    )

    # Optional EDIP metadata filters
    document_type: Optional[str] = Field(
        default=None,
        description="Document category filter, for example: policy, sop, review.",
    )
    business_domain: Optional[str] = Field(
        default=None,
        description="Business domain filter, for example: replenishment, pricing.",
    )
    region_scope: Optional[str] = Field(
        default=None,
        description="Region scope filter, for example: west, east, enterprise.",
    )
    topic: Optional[str] = Field(
        default=None,
        description="Topic filter, for example: stockout_risk, supplier_delay.",
    )
    owner_role: Optional[str] = Field(
        default=None,
        description="Owner role filter.",
    )
    document_status: Optional[str] = Field(
        default=None,
        description="Document status filter, for example: active.",
    )
    approval_level: Optional[str] = Field(
        default=None,
        description="Approval level filter, for example: manager, executive.",
    )

    # Safe future payload-control flag
    # Current pipeline can ignore this until API/service cleanup is added.
    debug: bool = Field(
        default=False,
        description="If true, allows future debug-oriented responses such as full metadata exposure.",
    )


# =========================================================
# Source schema
# =========================================================
class RagSourceResponse(RagBaseSchema):
    chunk_id: str = Field(
        ...,
        description="Unique retrieved chunk identifier.",
    )
    score: float = Field(
        ...,
        description="Vector similarity / retrieval score for the chunk.",
    )

    document_id: Optional[str] = Field(
        default=None,
        description="Source document identifier.",
    )
    document_title: Optional[str] = Field(
        default=None,
        description="Source document title.",
    )
    source_path: Optional[str] = Field(
        default=None,
        description="Original source file path.",
    )
    document_type: Optional[str] = Field(
        default=None,
        description="Document type such as policy, sop, review, playbook, guide.",
    )
    business_domain: Optional[str] = Field(
        default=None,
        description="Business domain such as replenishment, pricing, inventory.",
    )
    heading_path: Optional[str] = Field(
        default=None,
        description="Heading path for the retrieved section.",
    )
    topic: Optional[str] = Field(
        default=None,
        description="Topic label for the retrieved section.",
    )
    text_preview: Optional[str] = Field(
        default=None,
        description="Short preview of retrieved chunk text for API responses.",
    )

    # Keep metadata supported so current pipeline does not break.
    # Later normal responses can set this to None for payload cleanup.
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional full metadata payload. Can be omitted in normal responses for smaller payload size.",
    )


# =========================================================
# Main query response schema
# =========================================================
class RagQueryResponse(RagBaseSchema):
    question: str = Field(
        ...,
        description="Original user question after validation/normalization.",
    )
    answer: str = Field(
        ...,
        description="Grounded answer generated from retrieved EDIP context.",
    )
    retrieval_count: int = Field(
        ...,
        ge=0,
        description="Number of retrieval matches used after filtering.",
    )
    used_context_chars: int = Field(
        ...,
        ge=0,
        description="Total number of context characters passed to generation.",
    )
    model_name: str = Field(
        ...,
        description="Generation model used for the final answer.",
    )
    latency_ms: int = Field(
        ...,
        ge=0,
        description="Total end-to-end request latency in milliseconds.",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings produced during retrieval or generation.",
    )
    filters_applied: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata filters actually applied to the retrieval query.",
    )
    sources: List[RagSourceResponse] = Field(
        default_factory=list,
        description="Retrieved source chunks used to ground the answer.",
    )


# =========================================================
# Health schema
# =========================================================
class RagHealthResponse(RagBaseSchema):
    status: str = Field(
        ...,
        description="Overall health status of the RAG API.",
    )
    service: str = Field(
        ...,
        description="Service name.",
    )
    retrieval_ready: bool = Field(
        ...,
        description="Whether retrieval dependencies are ready.",
    )
    generation_ready: bool = Field(
        ...,
        description="Whether generation dependencies are ready.",
    )
    timestamp_utc: str = Field(
        ...,
        description="UTC timestamp of the health response.",
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional detailed health information.",
    )