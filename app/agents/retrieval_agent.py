# app\agents\retrieval_agent.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from app.agents.planner_agent import PlannerPlan
from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# Protocols
# =========================================================
class RetrievalServiceProtocol(Protocol):
    """
    Minimal protocol for the existing RAG retrieval/query service.

    This keeps the agent loosely coupled and easy to test.
    """

    def retrieve_context(
        self,
        question: str,
        *,
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Return retrieval matches only.

        Expected normalized match shape:
        [
            {
                "id": "...",
                "score": 0.91,
                "metadata": {...},
            }
        ]
        """
        ...


# =========================================================
# Data models
# =========================================================
@dataclass(frozen=True)
class RetrievalAgentInput:
    """Input payload for the Retrieval Agent."""

    question: str
    plan: PlannerPlan
    user_role: Optional[str] = None
    region_scope: Optional[str] = None
    top_k: int = 5
    min_score: float = 0.0
    extra_filters: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedChunk:
    """Normalized retrieval result passed to downstream agents."""

    chunk_id: Optional[str]
    score: float
    chunk_text: str
    source_document_id: Optional[str]
    document_title: Optional[str]
    document_type: Optional[str]
    business_domain: Optional[str]
    region_scope: Optional[str]
    owner_role: Optional[str]
    topic: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalAgentResult:
    """Final structured retrieval output."""

    question: str
    metadata_filter: Dict[str, Any]
    retrieval_count: int
    chunks: List[RetrievedChunk]
    warnings: List[str] = field(default_factory=list)


# =========================================================
# Retrieval agent
# =========================================================
class RetrievalAgent:
    """
    EDIP Retrieval Agent.

    Responsibilities:
    - receive planner output
    - build metadata-aware retrieval filters
    - call the RAG retrieval service
    - normalize returned chunks for downstream reasoning
    """

    def __init__(self, retrieval_service: RetrievalServiceProtocol) -> None:
        self.retrieval_service = retrieval_service
        logger.info("RetrievalAgent initialized.")

    def retrieve(self, payload: RetrievalAgentInput) -> RetrievalAgentResult:
        """
            Run metadata-aware retrieval using the current question and planner output.
        """
        normalized_question = self._validate_question(payload.question)
        metadata_filter = self._build_metadata_filter(payload)

        logger.info(
            "RetrievalAgent started | top_k=%s | min_score=%s | filter=%s",
            payload.top_k,
            payload.min_score,
            metadata_filter,
        )

        warnings: List[str] = []

        raw_matches = self.retrieval_service.retrieve_context(
            normalized_question,
            top_k=payload.top_k,
            metadata_filter=metadata_filter,
            min_score=payload.min_score,
        )

        # Fallback retrieval if strict filter returned nothing
        if not raw_matches and metadata_filter:
            warnings.append(
                "Strict metadata filter returned no matches. Retrying with broader retrieval."
            )
            logger.warning(
                "Strict retrieval returned no matches. Retrying with broader filter."
            )

            fallback_filter: Dict[str, Any] = {}

            if payload.plan.knowledge_domains:
                if len(payload.plan.knowledge_domains) == 1:
                    fallback_filter = {
                    "business_domain": {"$eq": payload.plan.knowledge_domains[0]}
                    }
                else:
                    fallback_filter = {
                        "business_domain": {"$in": payload.plan.knowledge_domains}
                    }

            raw_matches = self.retrieval_service.retrieve_context(
                normalized_question,
                top_k=payload.top_k,
                metadata_filter=fallback_filter,
                min_score=payload.min_score,
            )

            metadata_filter = fallback_filter

        if not raw_matches:
            warnings.append("No retrieval matches found for the current request.")
            logger.warning("RetrievalAgent found no matches.")

            return RetrievalAgentResult(
                question=normalized_question,
                metadata_filter=metadata_filter,
                retrieval_count=0,
                chunks=[],
                warnings=warnings,
            )

        chunks = self._normalize_matches(raw_matches)

        if not chunks:
            warnings.append("Matches were returned, but no usable chunk text was found.")
            logger.warning("RetrievalAgent received matches but usable chunks were empty.")

        result = RetrievalAgentResult(
            question=normalized_question,
            metadata_filter=metadata_filter,
            retrieval_count=len(chunks),
            chunks=chunks,
            warnings=warnings,
        )

        logger.info(
            "RetrievalAgent completed | retrieval_count=%s",
            result.retrieval_count,
       )
        return result

    # =========================================================
    # Internal helpers
    # =========================================================
    def _validate_question(self, question: str) -> str:
        """
        Validate and normalize the input question.
        """
        normalized = " ".join(question.strip().split())
        if not normalized:
            raise ValueError("Question cannot be empty for retrieval.")
        return normalized

    def _build_metadata_filter(self, payload: RetrievalAgentInput) -> Dict[str, Any]:
        """
        Build Pinecone-style metadata filters from planner output and user context.

        Strategy:
        - keep business_domain filtering because it is high-value and usually stable
        - do not force user_role as a retrieval filter by default
        - only use region_scope when it is explicitly reliable for document metadata
        - allow extra_filters from caller when truly needed
        """

        filter_parts: List[Dict[str, Any]] = []

        # -------------------------
        # Business domain filter
        # -------------------------
        if payload.plan.knowledge_domains:
            if len(payload.plan.knowledge_domains) == 1:
                filter_parts.append(
                    {"business_domain": {"$eq": payload.plan.knowledge_domains[0]}}
                )
            else:
                filter_parts.append(
                    {"business_domain": {"$in": payload.plan.knowledge_domains}}
                )

        # -------------------------
        # Region filter
        # -------------------------
        safe_region_scope = (payload.region_scope or "").strip().lower()
        if safe_region_scope and safe_region_scope not in {"all", "global", "any"}:
           pass

        # -------------------------
        # Extra caller-provided filters
        # -------------------------
        for key, value in payload.extra_filters.items():
            if value is None:
                continue

            if isinstance(value, list):
                if value:
                    filter_parts.append({key: {"$in": value}})
            else:
                filter_parts.append({key: {"$eq": value}})

        if not filter_parts:
            return {}

        if len(filter_parts) == 1:
            return filter_parts[0]

        return {"$and": filter_parts}


    def _normalize_matches(self, raw_matches: List[Dict[str, Any]]) -> List[RetrievedChunk]:
        """
        Convert raw retrieval matches into a stable downstream structure.
        """
        normalized_chunks: List[RetrievedChunk] = []

        for match in raw_matches:
            metadata = match.get("metadata", {}) or {}
            chunk_text = str(metadata.get("chunk_text", "") or "").strip()

            if not chunk_text:
                continue

            normalized_chunks.append(
                RetrievedChunk(
                    chunk_id=self._to_optional_str(
                        metadata.get("chunk_id") or match.get("id")
                    ),
                    score=float(match.get("score", 0.0) or 0.0),
                    chunk_text=chunk_text,
                    source_document_id=self._to_optional_str(
                        metadata.get("source_document_id")
                    ),
                    document_title=self._to_optional_str(
                        metadata.get("document_title")
                    ),
                    document_type=self._to_optional_str(
                        metadata.get("document_type")
                    ),
                    business_domain=self._to_optional_str(
                        metadata.get("business_domain")
                    ),
                    region_scope=self._to_optional_str(
                        metadata.get("region_scope")
                    ),
                    owner_role=self._to_optional_str(
                        metadata.get("owner_role")
                    ),
                    topic=self._to_optional_str(metadata.get("topic")),
                    metadata=metadata,
                )
            )

        return normalized_chunks

    def _to_optional_str(self, value: Any) -> Optional[str]:
        """
        Safely convert a value to string or None.
        """
        if value is None:
            return None

        text = str(value).strip()
        return text or None


# =========================================================
# Builder
# =========================================================
def build_retrieval_agent(
    retrieval_service: RetrievalServiceProtocol,
) -> RetrievalAgent:
    """Factory for consistent Retrieval Agent creation."""
    return RetrievalAgent(retrieval_service=retrieval_service)