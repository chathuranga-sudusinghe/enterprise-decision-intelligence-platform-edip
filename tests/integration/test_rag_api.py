# tests/integration/test_rag_api.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.rag import get_rag_query_service


# =========================================================
# Fake service result models
# =========================================================
@dataclass
class FakeRetrievalSource:
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
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FakeRagQueryResult:
    question: str
    answer: str
    sources: List[FakeRetrievalSource]
    retrieval_count: int
    used_context_chars: int
    model_name: str
    latency_ms: int
    warnings: List[str] = field(default_factory=list)


# =========================================================
# Fake service
# =========================================================
class FakeRagQueryService:
    def answer_question(
        self,
        question: str,
        *,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
        temperature: float = 0.1,
    ) -> FakeRagQueryResult:
        return FakeRagQueryResult(
            question=question,
            answer="Urgent replenishment was recommended because demand exceeded current available stock coverage.",
            sources=[
                FakeRetrievalSource(
                    chunk_id="chunk-001",
                    score=0.92,
                    document_id="doc-001",
                    document_title="Replenishment Decision Playbook",
                    source_path="docs/rag_source/replenishment_decision_playbook.md",
                    document_type="playbook",
                    business_domain="replenishment",
                    heading_path="root > urgent replenishment",
                    topic="stockout_risk",
                    text_preview="Urgent replenishment should be triggered when projected demand exceeds available cover.",
                    metadata={
                        "document_title": "Replenishment Decision Playbook",
                        "source_path": "docs/rag_source/replenishment_decision_playbook.md",
                        "topic": "stockout_risk",
                    },
                )
            ],
            retrieval_count=1,
            used_context_chars=312,
            model_name="gpt-4.1-mini",
            latency_ms=25,
            warnings=[],
        )


# =========================================================
# Test client fixture
# =========================================================
@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_rag_query_service] = lambda: FakeRagQueryService()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# =========================================================
# Tests
# =========================================================
def test_rag_health_returns_200(client: TestClient) -> None:
    response = client.get("/rag/health")

    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert "service" in payload


def test_rag_query_returns_200_for_valid_request(client: TestClient) -> None:
    request_payload = {
        "question": "Why was urgent replenishment recommended for SKU-100245?",
        "top_k": 5,
        "min_score": 0.0,
        "temperature": 0.1,
        "document_type": "playbook",
        "business_domain": "replenishment",
        "topic": "stockout_risk",
    }

    response = client.post("/rag/query", json=request_payload)

    assert response.status_code == 200

    payload = response.json()
    assert payload["question"] == request_payload["question"]
    assert "urgent replenishment" in payload["answer"].lower()
    assert payload["retrieval_count"] == 1
    assert payload["used_context_chars"] == 312
    assert payload["model_name"] == "gpt-4.1-mini"
    assert isinstance(payload["sources"], list)
    assert len(payload["sources"]) == 1
    assert payload["sources"][0]["document_title"] == "Replenishment Decision Playbook"


def test_rag_query_returns_422_for_invalid_payload(client: TestClient) -> None:
    request_payload = {
        "question": "ok",   # too short for min_length=3
        "top_k": 0,         # invalid because ge=1
    }

    response = client.post("/rag/query", json=request_payload)

    assert response.status_code == 422


def test_rag_query_returns_422_when_question_missing(client: TestClient) -> None:
    request_payload = {
        "top_k": 5,
        "temperature": 0.1,
    }

    response = client.post("/rag/query", json=request_payload)

    assert response.status_code == 422