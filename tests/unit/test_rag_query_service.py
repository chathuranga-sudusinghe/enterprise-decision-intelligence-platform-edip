from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import pytest

from app.services.rag_query_service import (
    RagQueryService,
    RagQueryResult,
    RetrievalSource,
)


@dataclass
class FakeGenerationInput:
    question: str
    context_blocks: List[str]
    temperature: float = 0.1
    max_context_chars: int = 12000


@dataclass
class FakeGenerationOutput:
    answer: str
    model_name: str
    used_context_chars: int
    warnings: List[str] = field(default_factory=list)


class FakeEmbeddingClient:
    def __init__(self, vector: List[float] | None = None) -> None:
        self.vector = vector or [0.1, 0.2, 0.3]
        self.last_text: str | None = None

    def embed_text(self, text: str) -> List[float]:
        self.last_text = text
        return self.vector


class FailingEmbeddingClient:
    def embed_text(self, text: str) -> List[float]:
        raise RuntimeError("Embedding generation failed.")


class FakeVectorStoreClient:
    def __init__(self, matches: List[Dict[str, Any]] | None = None) -> None:
        self.matches = matches or []
        self.last_vector: List[float] | None = None
        self.last_top_k: int | None = None
        self.last_metadata_filter: Dict[str, Any] | None = None

    def query(
        self,
        vector: List[float],
        top_k: int,
        metadata_filter: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        self.last_vector = vector
        self.last_top_k = top_k
        self.last_metadata_filter = metadata_filter
        return self.matches


class FailingVectorStoreClient:
    def query(
        self,
        vector: List[float],
        top_k: int,
        metadata_filter: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        raise RuntimeError("Vector retrieval failed.")


class FakeGenerationService:
    def __init__(
        self,
        answer: str = "Grounded answer from retrieved context.",
        model_name: str = "gpt-test",
        used_context_chars: int = 250,
        warnings: List[str] | None = None,
    ) -> None:
        self.answer = answer
        self.model_name = model_name
        self.used_context_chars = used_context_chars
        self.warnings = warnings or []
        self.last_request: Any = None

    def generate_answer(self, request: Any) -> FakeGenerationOutput:
        self.last_request = request
        return FakeGenerationOutput(
            answer=self.answer,
            model_name=self.model_name,
            used_context_chars=self.used_context_chars,
            warnings=self.warnings,
        )


class FailingGenerationService:
    model_name = "gpt-test"

    def generate_answer(self, request: Any) -> FakeGenerationOutput:
        raise RuntimeError("Generation failed.")


def build_service(
    *,
    embedding_client: Any | None = None,
    vector_store_client: Any | None = None,
    generation_service: Any | None = None,
    default_top_k: int = 5,
    max_context_chars: int = 12000,
) -> RagQueryService:
    return RagQueryService(
        embedding_client=embedding_client or FakeEmbeddingClient(),
        vector_store_client=vector_store_client or FakeVectorStoreClient(),
        generation_service=generation_service or FakeGenerationService(),
        default_top_k=default_top_k,
        max_context_chars=max_context_chars,
    )


def sample_match(
    *,
    chunk_id: str = "chunk-001",
    score: float = 0.92,
    chunk_text: str = "This is a business context chunk for replenishment decisions.",
    document_title: str = "Inventory Policy Manual",
    heading_path: str = "Policy > Replenishment",
    source_path: str = "docs/policies/inventory_policy.md",
) -> Dict[str, Any]:
    return {
        "id": chunk_id,
        "score": score,
        "metadata": {
            "chunk_id": chunk_id,
            "document_id": "DOC-001",
            "document_title": document_title,
            "source_path": source_path,
            "document_type": "policy",
            "business_domain": "inventory",
            "heading_path": heading_path,
            "topic": "replenishment",
            "chunk_text": chunk_text,
        },
    }


def test_validate_question_returns_trimmed_text() -> None:
    assert RagQueryService._validate_question("  Why is stockout risk high?  ") == "Why is stockout risk high?"


def test_validate_question_raises_for_empty_question() -> None:
    with pytest.raises(ValueError, match="Question cannot be empty."):
        RagQueryService._validate_question("   ")


def test_validate_question_raises_for_too_short_question() -> None:
    with pytest.raises(ValueError, match="Question is too short."):
        RagQueryService._validate_question("hi")


def test_extract_chunk_text_prefers_chunk_text() -> None:
    match = {
        "metadata": {
            "chunk_text": "Primary chunk text",
            "text": "Fallback text",
        }
    }
    assert RagQueryService._extract_chunk_text(match) == "Primary chunk text"


def test_extract_chunk_text_falls_back_to_other_fields() -> None:
    match = {"metadata": {"content": "Content fallback text"}}
    assert RagQueryService._extract_chunk_text(match) == "Content fallback text"


def test_extract_chunk_text_returns_empty_string_when_missing() -> None:
    match = {"metadata": {"document_title": "No Text Here"}}
    assert RagQueryService._extract_chunk_text(match) == ""


def test_build_generation_context_blocks_returns_blocks_for_valid_matches() -> None:
    service = build_service()
    matches = [
        sample_match(chunk_id="chunk-001"),
        sample_match(chunk_id="chunk-002", chunk_text="Second block text."),
    ]

    blocks = service._build_generation_context_blocks(matches)

    assert len(blocks) == 2
    assert "[Context Block 1]" in blocks[0]
    assert "Inventory Policy Manual" in blocks[0]
    assert "Chunk ID: chunk-001" in blocks[0]
    assert "This is a business context chunk" in blocks[0]


def test_build_generation_context_blocks_skips_empty_text_matches() -> None:
    service = build_service()
    matches = [
        sample_match(chunk_id="chunk-001", chunk_text=""),
        sample_match(chunk_id="chunk-002", chunk_text="Useful text."),
    ]

    blocks = service._build_generation_context_blocks(matches)

    assert len(blocks) == 1
    assert "chunk-002" in blocks[0]


def test_build_sources_returns_retrieval_source_objects() -> None:
    service = build_service()
    matches = [sample_match()]

    sources = service._build_sources(matches)

    assert len(sources) == 1
    assert isinstance(sources[0], RetrievalSource)
    assert sources[0].chunk_id == "chunk-001"
    assert sources[0].score == 0.92
    assert sources[0].document_title == "Inventory Policy Manual"
    assert sources[0].text_preview is not None


def test_answer_question_returns_result_for_valid_matches() -> None:
    matches = [
        sample_match(chunk_id="chunk-001", score=0.95),
        sample_match(chunk_id="chunk-002", score=0.85, chunk_text="Second supporting context."),
    ]
    embedding_client = FakeEmbeddingClient()
    vector_store_client = FakeVectorStoreClient(matches=matches)
    generation_service = FakeGenerationService(
        answer="Urgent replenishment is recommended because stockout risk is elevated.",
        model_name="gpt-test",
        used_context_chars=480,
        warnings=["Minor context truncation applied."],
    )
    service = build_service(
        embedding_client=embedding_client,
        vector_store_client=vector_store_client,
        generation_service=generation_service,
        default_top_k=5,
        max_context_chars=12000,
    )

    result = service.answer_question(
        "Why is urgent replenishment recommended?",
        top_k=2,
        metadata_filter={"document_type": "policy"},
        min_score=0.80,
        temperature=0.2,
    )

    assert isinstance(result, RagQueryResult)
    assert result.question == "Why is urgent replenishment recommended?"
    assert result.answer.startswith("Urgent replenishment")
    assert result.retrieval_count == 2
    assert result.used_context_chars == 480
    assert result.model_name == "gpt-test"
    assert "Minor context truncation applied." in result.warnings

    assert embedding_client.last_text == "Why is urgent replenishment recommended?"
    assert vector_store_client.last_top_k == 2
    assert vector_store_client.last_metadata_filter == {"document_type": "policy"}

    assert generation_service.last_request.question == "Why is urgent replenishment recommended?"
    assert len(generation_service.last_request.context_blocks) == 2
    assert generation_service.last_request.temperature == 0.2
    assert generation_service.last_request.max_context_chars == 12000


def test_answer_question_uses_default_top_k_when_not_provided() -> None:
    vector_store_client = FakeVectorStoreClient(matches=[sample_match()])
    service = build_service(
        vector_store_client=vector_store_client,
        default_top_k=7,
    )

    result = service.answer_question("What caused the recommendation?")

    assert result.retrieval_count == 1
    assert vector_store_client.last_top_k == 7


def test_answer_question_filters_out_low_score_matches() -> None:
    matches = [
        sample_match(chunk_id="chunk-001", score=0.92),
        sample_match(chunk_id="chunk-002", score=0.30, chunk_text="Low score text."),
    ]
    service = build_service(
        vector_store_client=FakeVectorStoreClient(matches=matches),
    )

    result = service.answer_question(
        "Why was this recommended?",
        min_score=0.50,
    )

    assert result.retrieval_count == 1
    assert len(result.sources) == 1
    assert result.sources[0].chunk_id == "chunk-001"


def test_answer_question_returns_fallback_when_no_matches_pass_threshold() -> None:
    matches = [
        sample_match(chunk_id="chunk-001", score=0.20),
        sample_match(chunk_id="chunk-002", score=0.10),
    ]
    service = build_service(
        vector_store_client=FakeVectorStoreClient(matches=matches),
        generation_service=FakeGenerationService(model_name="gpt-test"),
    )

    result = service.answer_question(
        "Why was the item flagged?",
        min_score=0.50,
    )

    assert result.retrieval_count == 0
    assert result.sources == []
    assert result.used_context_chars == 0
    assert result.model_name == "gpt-test"
    assert "No retrieval matches satisfied the filter and score threshold." in result.warnings
    assert "I could not find enough relevant business context" in result.answer


def test_answer_question_returns_fallback_when_context_blocks_are_empty() -> None:
    matches = [
        sample_match(chunk_id="chunk-001", chunk_text=""),
        {
            "id": "chunk-002",
            "score": 0.88,
            "metadata": {
                "chunk_id": "chunk-002",
                "document_title": "Doc Without Text",
            },
        },
    ]
    service = build_service(
        vector_store_client=FakeVectorStoreClient(matches=matches),
        generation_service=FakeGenerationService(model_name="gpt-test"),
    )

    result = service.answer_question("What happened here?")

    assert result.retrieval_count == 2
    assert len(result.sources) == 2
    assert result.used_context_chars == 0
    assert result.model_name == "gpt-test"
    assert "Retrieved matches were present, but usable chunk text was empty." in result.warnings
    assert "usable document text was missing" in result.answer


def test_answer_question_propagates_embedding_error() -> None:
    service = build_service(
        embedding_client=FailingEmbeddingClient(),
        vector_store_client=FakeVectorStoreClient(matches=[sample_match()]),
    )

    with pytest.raises(RuntimeError, match="Embedding generation failed."):
        service.answer_question("Why is this item urgent?")


def test_answer_question_propagates_vector_store_error() -> None:
    service = build_service(
        vector_store_client=FailingVectorStoreClient(),
    )

    with pytest.raises(RuntimeError, match="Vector retrieval failed."):
        service.answer_question("Why is this item urgent?")


def test_answer_question_propagates_generation_error() -> None:
    service = build_service(
        vector_store_client=FakeVectorStoreClient(matches=[sample_match()]),
        generation_service=FailingGenerationService(),
    )

    with pytest.raises(RuntimeError, match="Generation failed."):
        service.answer_question("Why is this item urgent?")