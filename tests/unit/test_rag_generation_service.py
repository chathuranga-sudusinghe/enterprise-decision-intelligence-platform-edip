from __future__ import annotations

from types import SimpleNamespace
from typing import Any, List

import pytest

from app.services.rag_generation_service import (
    GenerationInput,
    GenerationOutput,
    RagGenerationService,
    build_rag_generation_service,
)


class FakeResponsesAPI:
    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.last_kwargs: dict[str, Any] | None = None

    def create(self, **kwargs: Any) -> Any:
        self.last_kwargs = kwargs
        if self.error is not None:
            raise self.error
        return self.response


class FakeOpenAIClient:
    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.responses = FakeResponsesAPI(response=response, error=error)


def make_response_with_output_text(text: str) -> Any:
    return SimpleNamespace(output_text=text)


def make_response_with_output_parts(parts: List[str]) -> Any:
    content_parts = [SimpleNamespace(text=part) for part in parts]
    output_item = SimpleNamespace(content=content_parts)
    return SimpleNamespace(output=[output_item])


def test_build_context_text_returns_empty_string_for_empty_blocks() -> None:
    result = RagGenerationService._build_context_text(
        context_blocks=["", "   ", None],  # type: ignore[list-item]
        max_context_chars=200,
    )

    assert result == ""


def test_build_context_text_formats_blocks_correctly() -> None:
    result = RagGenerationService._build_context_text(
        context_blocks=["First context", "Second context"],
        max_context_chars=500,
    )

    assert "[Context 1]" in result
    assert "First context" in result
    assert "[Context 2]" in result
    assert "Second context" in result


def test_build_context_text_truncates_when_limit_exceeded() -> None:
    long_block = "A" * 200

    result = RagGenerationService._build_context_text(
        context_blocks=[long_block, "Second block"],
        max_context_chars=80,
    )

    assert "[Context 1]" in result
    assert len(result) <= 80
    assert "Second block" not in result


def test_extract_response_text_prefers_output_text() -> None:
    response = make_response_with_output_text("Grounded answer from model.")

    result = RagGenerationService._extract_response_text(response)

    assert result == "Grounded answer from model."


def test_extract_response_text_falls_back_to_output_parts() -> None:
    response = make_response_with_output_parts(
        ["First answer sentence.", "Second answer sentence."]
    )

    result = RagGenerationService._extract_response_text(response)

    assert "First answer sentence." in result
    assert "Second answer sentence." in result


def test_extract_response_text_returns_empty_string_when_no_text_exists() -> None:
    response = SimpleNamespace(output=None)

    result = RagGenerationService._extract_response_text(response)

    assert result == ""


def test_generate_answer_returns_fallback_when_no_context_is_available() -> None:
    client = FakeOpenAIClient(response=make_response_with_output_text("Should not be used"))
    service = RagGenerationService(
        client=client,
        model_name="gpt-test",
        max_context_chars=12000,
    )

    request = GenerationInput(
        question="Why was urgent replenishment recommended?",
        context_blocks=[],
        temperature=0.1,
        max_context_chars=12000,
    )

    result = service.generate_answer(request)

    assert isinstance(result, GenerationOutput)
    assert result.model_name == "gpt-test"
    assert result.used_context_chars == 0
    assert "No retrieved context was available for grounded generation." in result.warnings
    assert "I could not generate a grounded answer" in result.answer
    assert client.responses.last_kwargs is None


def test_generate_answer_calls_openai_and_returns_output_text() -> None:
    response = make_response_with_output_text(
        "Urgent replenishment is recommended because stockout risk is elevated."
    )
    client = FakeOpenAIClient(response=response)
    service = RagGenerationService(
        client=client,
        model_name="gpt-4.1-mini-test",
        max_context_chars=12000,
    )

    request = GenerationInput(
        question="Why was urgent replenishment recommended?",
        context_blocks=["Policy says urgent action is required for elevated stockout risk."],
        temperature=0.2,
        max_context_chars=500,
    )

    result = service.generate_answer(request)

    assert isinstance(result, GenerationOutput)
    assert result.answer.startswith("Urgent replenishment")
    assert result.model_name == "gpt-4.1-mini-test"
    assert result.used_context_chars > 0
    assert result.warnings == []

    assert client.responses.last_kwargs is not None
    assert client.responses.last_kwargs["model"] == "gpt-4.1-mini-test"
    assert client.responses.last_kwargs["temperature"] == 0.2
    assert isinstance(client.responses.last_kwargs["input"], list)
    assert client.responses.last_kwargs["input"][0]["role"] == "system"
    assert client.responses.last_kwargs["input"][1]["role"] == "user"
    assert "Why was urgent replenishment recommended?" in client.responses.last_kwargs["input"][1]["content"]


def test_generate_answer_uses_output_parts_when_output_text_missing() -> None:
    response = make_response_with_output_parts(
        ["Grounded business answer.", "Next practical action."]
    )
    client = FakeOpenAIClient(response=response)
    service = RagGenerationService(
        client=client,
        model_name="gpt-test",
        max_context_chars=12000,
    )

    request = GenerationInput(
        question="What should the planner do next?",
        context_blocks=["Planner should review inbound supply and reorder levels."],
    )

    result = service.generate_answer(request)

    assert "Grounded business answer." in result.answer
    assert "Next practical action." in result.answer
    assert result.warnings == []


def test_generate_answer_returns_empty_answer_fallback_when_llm_response_is_empty() -> None:
    response = make_response_with_output_text("")
    client = FakeOpenAIClient(response=response)
    service = RagGenerationService(
        client=client,
        model_name="gpt-test",
        max_context_chars=12000,
    )

    request = GenerationInput(
        question="What is the issue?",
        context_blocks=["Some valid context block."],
    )

    result = service.generate_answer(request)

    assert result.answer == "The system completed generation, but the answer content was empty."
    assert "LLM returned an empty answer." in result.warnings
    assert result.used_context_chars > 0


def test_generate_answer_raises_runtime_error_when_openai_call_fails() -> None:
    client = FakeOpenAIClient(error=RuntimeError("API down"))
    service = RagGenerationService(
        client=client,
        model_name="gpt-test",
        max_context_chars=12000,
    )

    request = GenerationInput(
        question="Why is the forecast risky?",
        context_blocks=["Useful context."],
    )

    with pytest.raises(RuntimeError, match="Failed to generate grounded RAG answer."):
        service.generate_answer(request)


def test_build_rag_generation_service_raises_when_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("RAG_GENERATION_MODEL", raising=False)
    monkeypatch.delenv("RAG_MAX_CONTEXT_CHARS", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY is not set."):
        build_rag_generation_service()


def test_build_rag_generation_service_uses_env_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeOpenAI:
        def __init__(self, api_key: str) -> None:
            captured["api_key"] = api_key

    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("RAG_GENERATION_MODEL", "gpt-custom-mini")
    monkeypatch.setenv("RAG_MAX_CONTEXT_CHARS", "9000")
    monkeypatch.setattr("app.services.rag_generation_service.OpenAI", FakeOpenAI)

    service = build_rag_generation_service()

    assert captured["api_key"] == "test-key-123"
    assert service.model_name == "gpt-custom-mini"
    assert service.max_context_chars == 9000


def test_build_rag_generation_service_falls_back_to_default_context_chars_on_invalid_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeOpenAI:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.delenv("RAG_GENERATION_MODEL", raising=False)
    monkeypatch.setenv("RAG_MAX_CONTEXT_CHARS", "invalid-number")
    monkeypatch.setattr("app.services.rag_generation_service.OpenAI", FakeOpenAI)

    service = build_rag_generation_service()

    assert service.model_name == "gpt-4.1-mini"
    assert service.max_context_chars == 12000