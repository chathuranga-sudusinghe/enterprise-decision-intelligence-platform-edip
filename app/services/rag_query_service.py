from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

from app.services.rag_generation_service import (
    GenerationInput,
    RagGenerationService,
    build_rag_generation_service,
)

# =========================================================
# Load environment variables
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# =========================================================
# Logging
# =========================================================
logger = logging.getLogger(__name__)

# =========================================================
# Constants
# =========================================================
DEFAULT_QUERY_EMBED_MODEL = "text-embedding-3-small"
DEFAULT_TOP_K = 5
DEFAULT_MAX_CONTEXT_CHARS = 12000
DEFAULT_PREVIEW_CHARS = 220
DEFAULT_HEADING_LEVELS = 2


# =========================================================
# Protocols
# =========================================================
class EmbeddingClient(Protocol):
    def embed_text(self, text: str) -> List[float]:
        ...


class VectorStoreClient(Protocol):
    def query(
        self,
        vector: List[float],
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        ...


# =========================================================
# Data classes
# =========================================================
@dataclass
class RetrievalSource:
    chunk_id: str
    score: float
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    source_path: Optional[str] = None
    document_type: Optional[str] = None
    business_domain: Optional[str] = None
    heading_path: Optional[str] = None
    topic: Optional[str] = None
    text_preview: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RagQueryResult:
    question: str
    answer: str
    sources: List[RetrievalSource]
    retrieval_count: int
    used_context_chars: int
    model_name: str
    latency_ms: int
    warnings: List[str] = field(default_factory=list)


# =========================================================
# OpenAI embedding adapter
# =========================================================
class OpenAIEmbeddingClient:
    def __init__(
        self,
        client: OpenAI,
        model_name: str = DEFAULT_QUERY_EMBED_MODEL,
    ) -> None:
        self.client = client
        self.model_name = model_name

    def embed_text(self, text: str) -> List[float]:
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text,
            )
            return response.data[0].embedding
        except Exception as exc:
            logger.exception("Failed to create query embedding.")
            raise RuntimeError("Embedding generation failed.") from exc


# =========================================================
# Pinecone adapter
# =========================================================
class PineconeVectorStoreClient:
    def __init__(
        self,
        index: Any,
        namespace: Optional[str] = None,
    ) -> None:
        self.index = index
        self.namespace = namespace

    def query(
        self,
        vector: List[float],
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        try:
            response = self.index.query(
                vector=vector,
                top_k=top_k,
                include_metadata=True,
                namespace=self.namespace,
                filter=metadata_filter or None,
            )

            matches = getattr(response, "matches", None)
            if matches is None and isinstance(response, dict):
                matches = response.get("matches", [])

            normalized: List[Dict[str, Any]] = []
            for match in matches or []:
                if isinstance(match, dict):
                    normalized.append(match)
                else:
                    normalized.append(
                        {
                            "id": getattr(match, "id", None),
                            "score": getattr(match, "score", None),
                            "metadata": getattr(match, "metadata", {}) or {},
                        }
                    )

            return normalized

        except Exception as exc:
            logger.exception("Pinecone query failed.")
            raise RuntimeError("Vector retrieval failed.") from exc


# =========================================================
# Main service
# =========================================================
class RagQueryService:
    def __init__(
        self,
        embedding_client: EmbeddingClient,
        vector_store_client: VectorStoreClient,
        generation_service: RagGenerationService,
        *,
        default_top_k: int = DEFAULT_TOP_K,
        max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
        preview_chars: int = DEFAULT_PREVIEW_CHARS,
        heading_levels: int = DEFAULT_HEADING_LEVELS,
    ) -> None:
        self.embedding_client = embedding_client
        self.vector_store_client = vector_store_client
        self.generation_service = generation_service
        self.default_top_k = default_top_k
        self.max_context_chars = max_context_chars
        self.preview_chars = preview_chars
        self.heading_levels = heading_levels

    def answer_question(
        self,
        question: str,
        *,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
        temperature: float = 0.1,
        debug: bool = False,
    ) -> RagQueryResult:
        started_at = time.perf_counter()
        warnings: List[str] = []

        normalized_question = self._validate_question(question)
        effective_top_k = top_k or self.default_top_k

        logger.info(
            "Starting RAG query | question=%s | top_k=%s | filter=%s | debug=%s",
            normalized_question,
            effective_top_k,
            json.dumps(metadata_filter or {}, ensure_ascii=False),
            debug,
        )

        query_vector = self.embedding_client.embed_text(normalized_question)

        raw_matches = self.vector_store_client.query(
            vector=query_vector,
            top_k=effective_top_k,
            metadata_filter=metadata_filter,
        )

        filtered_matches = [
            match
            for match in raw_matches
            if float(match.get("score", 0.0) or 0.0) >= min_score
        ]

        if not filtered_matches:
            warnings.append("No retrieval matches satisfied the filter and score threshold.")
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)

            return RagQueryResult(
                question=normalized_question,
                answer="I could not find enough relevant business context to answer this confidently.",
                sources=[],
                retrieval_count=0,
                used_context_chars=0,
                model_name=self.generation_service.model_name,
                latency_ms=elapsed_ms,
                warnings=warnings,
            )

        context_blocks = self._build_generation_context_blocks(filtered_matches)

        if not context_blocks:
            warnings.append("Retrieved matches were present, but usable chunk text was empty.")
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)

            return RagQueryResult(
                question=normalized_question,
                answer="Relevant records were found, but usable document text was missing.",
                sources=self._build_sources(filtered_matches, debug=debug),
                retrieval_count=len(filtered_matches),
                used_context_chars=0,
                model_name=self.generation_service.model_name,
                latency_ms=elapsed_ms,
                warnings=warnings,
            )

        generation_output = self.generation_service.generate_answer(
            GenerationInput(
                question=normalized_question,
                context_blocks=context_blocks,
                temperature=temperature,
                max_context_chars=self.max_context_chars,
            )
        )

        warnings.extend(generation_output.warnings)
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)

        result = RagQueryResult(
            question=normalized_question,
            answer=generation_output.answer,
            sources=self._build_sources(filtered_matches, debug=debug),
            retrieval_count=len(filtered_matches),
            used_context_chars=generation_output.used_context_chars,
            model_name=generation_output.model_name,
            latency_ms=elapsed_ms,
            warnings=warnings,
        )

        logger.info(
            "RAG query completed | retrieval_count=%s | used_context_chars=%s | latency_ms=%s",
            result.retrieval_count,
            result.used_context_chars,
            result.latency_ms,
        )

        return result

    @staticmethod
    def _validate_question(question: str) -> str:
        normalized = (question or "").strip()
        if not normalized:
            raise ValueError("Question cannot be empty.")
        if len(normalized) < 3:
            raise ValueError("Question is too short.")
        return normalized

    @staticmethod
    def _normalize_text(value: Optional[str]) -> str:
        if not isinstance(value, str):
            return ""
        return " ".join(value.split()).strip()

    def _short_preview(self, text: Optional[str]) -> Optional[str]:
        cleaned = self._normalize_text(text)
        if not cleaned:
            return None
        if len(cleaned) <= self.preview_chars:
            return cleaned
        return cleaned[: self.preview_chars - 3].rstrip() + "..."

    def _short_heading_path(self, heading_path: Optional[str]) -> Optional[str]:
        cleaned = self._normalize_text(heading_path)
        if not cleaned:
            return None

        # Supports common heading path separators safely.
        separators = [" > ", ">>", ">", "/", " | "]
        parts: List[str] = [cleaned]

        for separator in separators:
            if separator in cleaned:
                split_parts = [part.strip() for part in cleaned.split(separator) if part.strip()]
                if split_parts:
                    parts = split_parts
                    break

        shortened = " > ".join(parts[-self.heading_levels :]).strip()
        return shortened or cleaned

    @staticmethod
    def _extract_chunk_text(match: Dict[str, Any]) -> str:
        metadata = match.get("metadata", {}) or {}

        logger.info("Retrieved metadata keys: %s", list(metadata.keys()))

        candidate_fields = [
            "chunk_text",
            "text",
            "content",
            "body",
            "chunk",
            "page_content",
            "content_text",
            "markdown_text",
            "raw_text",
            "document_text",
        ]

        for field_name in candidate_fields:
            value = metadata.get(field_name)
            if isinstance(value, str) and value.strip():
                logger.info("Chunk text found in metadata field: %s", field_name)
                return value.strip()

        logger.warning("No usable chunk text field found in metadata.")
        return ""

    def _build_generation_context_blocks(
        self,
        matches: List[Dict[str, Any]],
    ) -> List[str]:
        context_blocks: List[str] = []

        for idx, match in enumerate(matches, start=1):
            metadata = dict(match.get("metadata", {}) or {})
            text = self._extract_chunk_text(match)

            if not text:
                continue

            if "chunk_id" not in metadata:
                metadata["chunk_id"] = match.get("id")

            block = "\n".join(
                [
                    f"[Context Block {idx}]",
                    f"Document Title: {metadata.get('document_title', 'Unknown Document')}",
                    f"Heading Path: {metadata.get('heading_path', 'root')}",
                    f"Source Path: {metadata.get('source_path', '')}",
                    f"Chunk ID: {metadata.get('chunk_id', '')}",
                    "Text:",
                    text,
                ]
            ).strip()

            if block:
                context_blocks.append(block)

        return context_blocks

    def _build_sources(
        self,
        matches: List[Dict[str, Any]],
        *,
        debug: bool = False,
    ) -> List[RetrievalSource]:
        sources: List[RetrievalSource] = []

        for match in matches:
            metadata = dict(match.get("metadata", {}) or {})
            chunk_text = self._extract_chunk_text(match)

            source = RetrievalSource(
                chunk_id=str(metadata.get("chunk_id") or match.get("id") or ""),
                score=float(match.get("score", 0.0) or 0.0),
                document_id=metadata.get("document_id"),
                document_title=metadata.get("document_title"),
                source_path=metadata.get("source_path"),
                document_type=metadata.get("document_type"),
                business_domain=metadata.get("business_domain"),
                heading_path=self._short_heading_path(metadata.get("heading_path")),
                topic=metadata.get("topic"),
                text_preview=self._short_preview(chunk_text),
                metadata=metadata if debug else None,
            )
            sources.append(source)

        return sources


# =========================================================
# Factory
# =========================================================
def build_rag_query_service() -> RagQueryService:
    """
    Default factory for the EDIP app layer.

    Required environment variables:
    - OPENAI_API_KEY
    - PINECONE_API_KEY
    - PINECONE_INDEX_NAME

    Optional:
    - OPENAI_EMBED_MODEL
    - PINECONE_NAMESPACE
    - RAG_TOP_K
    - RAG_MAX_CONTEXT_CHARS
    - RAG_GENERATION_MODEL
    - RAG_PREVIEW_CHARS
    - RAG_HEADING_LEVELS
    """
    try:
        logger.info("OPENAI_API_KEY loaded: %s", bool(os.getenv("OPENAI_API_KEY")))
        logger.info("PINECONE_API_KEY loaded: %s", bool(os.getenv("PINECONE_API_KEY")))
        logger.info("PINECONE_INDEX_NAME loaded: %s", os.getenv("PINECONE_INDEX_NAME"))

        openai_api_key = os.getenv("OPENAI_API_KEY")
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

        if not openai_api_key:
            raise ValueError("Missing OPENAI_API_KEY.")
        if not pinecone_api_key:
            raise ValueError("Missing PINECONE_API_KEY.")
        if not pinecone_index_name:
            raise ValueError("Missing PINECONE_INDEX_NAME.")

        embed_model = os.getenv("OPENAI_EMBED_MODEL", DEFAULT_QUERY_EMBED_MODEL)
        pinecone_namespace = os.getenv("PINECONE_NAMESPACE")

        try:
            rag_top_k = int(os.getenv("RAG_TOP_K", str(DEFAULT_TOP_K)))
        except ValueError:
            logger.warning("Invalid RAG_TOP_K. Falling back to default.")
            rag_top_k = DEFAULT_TOP_K

        try:
            rag_max_context_chars = int(
                os.getenv("RAG_MAX_CONTEXT_CHARS", str(DEFAULT_MAX_CONTEXT_CHARS))
            )
        except ValueError:
            logger.warning("Invalid RAG_MAX_CONTEXT_CHARS. Falling back to default.")
            rag_max_context_chars = DEFAULT_MAX_CONTEXT_CHARS

        try:
            rag_preview_chars = int(os.getenv("RAG_PREVIEW_CHARS", str(DEFAULT_PREVIEW_CHARS)))
        except ValueError:
            logger.warning("Invalid RAG_PREVIEW_CHARS. Falling back to default.")
            rag_preview_chars = DEFAULT_PREVIEW_CHARS

        try:
            rag_heading_levels = int(
                os.getenv("RAG_HEADING_LEVELS", str(DEFAULT_HEADING_LEVELS))
            )
        except ValueError:
            logger.warning("Invalid RAG_HEADING_LEVELS. Falling back to default.")
            rag_heading_levels = DEFAULT_HEADING_LEVELS

        # Safety guard
        if rag_preview_chars < 50:
            logger.warning("RAG_PREVIEW_CHARS too small. Resetting to default.")
            rag_preview_chars = DEFAULT_PREVIEW_CHARS

        if rag_heading_levels < 1:
            logger.warning("RAG_HEADING_LEVELS too small. Resetting to default.")
            rag_heading_levels = DEFAULT_HEADING_LEVELS

        openai_client = OpenAI(api_key=openai_api_key)
        pinecone_client = Pinecone(api_key=pinecone_api_key)
        pinecone_index = pinecone_client.Index(pinecone_index_name)

        embedding_client = OpenAIEmbeddingClient(
            client=openai_client,
            model_name=embed_model,
        )

        vector_store_client = PineconeVectorStoreClient(
            index=pinecone_index,
            namespace=pinecone_namespace,
        )

        generation_service = build_rag_generation_service()

        return RagQueryService(
            embedding_client=embedding_client,
            vector_store_client=vector_store_client,
            generation_service=generation_service,
            default_top_k=rag_top_k,
            max_context_chars=rag_max_context_chars,
            preview_chars=rag_preview_chars,
            heading_levels=rag_heading_levels,
        )

    except Exception as exc:
        logger.exception("Failed to build RagQueryService.")
        raise RuntimeError("RAG query service initialization failed.") from exc