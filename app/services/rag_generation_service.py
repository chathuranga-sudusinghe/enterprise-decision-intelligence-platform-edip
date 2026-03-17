# app/services/rag_generation_service.py

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import OpenAI


# =========================================================
# Logging
# =========================================================
logger = logging.getLogger(__name__)


# =========================================================
# Prompt templates
# =========================================================
SYSTEM_PROMPT = """You are an enterprise decision support assistant for NorthStar Retail & Distribution.

Your job is to answer business questions using only the retrieved EDIP context provided to you.

Rules:
1. Ground the answer only in the supplied context.
2. Do not invent policies, metrics, thresholds, or events not supported by the context.
3. If the context is weak or incomplete, clearly say so.
4. Prefer concise, business-friendly answers.
5. When useful, include practical next actions.
6. If sources conflict, acknowledge uncertainty.
"""

USER_PROMPT_TEMPLATE = """Business question:
{question}

Retrieved context:
{context}

Write a grounded answer for the business user.
"""


# =========================================================
# Models
# =========================================================
@dataclass
class GenerationInput:
    question: str
    context_blocks: List[str]
    temperature: float = 0.1
    max_context_chars: int = 12000


@dataclass
class GenerationOutput:
    answer: str
    model_name: str
    used_context_chars: int
    warnings: List[str] = field(default_factory=list)


# =========================================================
# Service
# =========================================================
class RagGenerationService:
    def __init__(
        self,
        client: OpenAI,
        model_name: str,
        max_context_chars: int = 12000,
    ) -> None:
        self.client = client
        self.model_name = model_name
        self.max_context_chars = max_context_chars

    def generate_answer(self, request: GenerationInput) -> GenerationOutput:
        warnings: List[str] = []

        context_text = self._build_context_text(
            context_blocks=request.context_blocks,
            max_context_chars=request.max_context_chars or self.max_context_chars,
        )

        if not context_text.strip():
            warnings.append("No retrieved context was available for grounded generation.")
            return GenerationOutput(
                answer=(
                    "I could not generate a grounded answer because no relevant EDIP context "
                    "was retrieved for this question."
                ),
                model_name=self.model_name,
                used_context_chars=0,
                warnings=warnings,
            )

        user_prompt = USER_PROMPT_TEMPLATE.format(
            question=request.question.strip(),
            context=context_text,
        )

        try:
            response = self.client.responses.create(
                model=self.model_name,
                temperature=request.temperature,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:
            logger.exception("RAG generation failed.")
            raise RuntimeError("Failed to generate grounded RAG answer.") from exc

        answer_text = self._extract_response_text(response)

        if not answer_text.strip():
            warnings.append("LLM returned an empty answer.")
            answer_text = (
                "The system completed generation, but the answer content was empty."
            )

        return GenerationOutput(
            answer=answer_text.strip(),
            model_name=self.model_name,
            used_context_chars=len(context_text),
            warnings=warnings,
        )

    @staticmethod
    def _build_context_text(
        context_blocks: List[str],
        max_context_chars: int,
    ) -> str:
        cleaned_blocks: List[str] = []
        current_size = 0

        for idx, block in enumerate(context_blocks, start=1):
            if not block or not str(block).strip():
                continue

            normalized = str(block).strip()
            entry = f"[Context {idx}]\n{normalized}\n"

            if current_size + len(entry) > max_context_chars:
                remaining = max_context_chars - current_size
                if remaining > 50:
                    entry = entry[:remaining]
                    cleaned_blocks.append(entry)
                    current_size += len(entry)
                break

            cleaned_blocks.append(entry)
            current_size += len(entry)

        return "\n".join(cleaned_blocks).strip()

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        # Preferred SDK helper if available
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text

        # Fallback for SDK object structures
        output = getattr(response, "output", None)
        if not output:
            return ""

        collected: List[str] = []

        for item in output:
            content = getattr(item, "content", None)
            if not content:
                continue

            for part in content:
                part_text = getattr(part, "text", None)
                if isinstance(part_text, str) and part_text.strip():
                    collected.append(part_text)

        return "\n".join(collected).strip()


# =========================================================
# Factory
# =========================================================
def build_rag_generation_service() -> RagGenerationService:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    model_name = os.getenv("RAG_GENERATION_MODEL", "gpt-4.1-mini")

    try:
        max_context_chars = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "12000"))
    except ValueError:
        logger.warning(
            "Invalid RAG_MAX_CONTEXT_CHARS value. Falling back to 12000."
        )
        max_context_chars = 12000

    client = OpenAI(api_key=api_key)

    return RagGenerationService(
        client=client,
        model_name=model_name,
        max_context_chars=max_context_chars,
    )