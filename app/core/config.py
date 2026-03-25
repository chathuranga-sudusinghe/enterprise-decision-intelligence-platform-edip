# app\core\config.py

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# =========================================================
# Helpers
# =========================================================
def _get_env_str(name: str, default: str = "") -> str:
    """Read a string environment variable with a safe default."""
    return os.getenv(name, default).strip()


def _get_env_int(name: str, default: int) -> int:
    """Read an integer environment variable with fallback."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default

    try:
        return int(value)
    except ValueError:
        return default


def _get_env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable with common true/false handling."""
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y", "on"}:
        return True
    if normalized in {"false", "0", "no", "n", "off"}:
        return False
    return default


def _get_env_list(name: str, default: List[str] | None = None) -> List[str]:
    """Read a comma-separated environment variable as a list."""
    raw_value = os.getenv(name, "")
    if not raw_value.strip():
        return default or []

    return [item.strip() for item in raw_value.split(",") if item.strip()]


# =========================================================
# App Settings
# =========================================================
@dataclass(frozen=True)
class Settings:
    """Central application settings loaded from environment variables."""

    # Core app metadata
    app_name: str = field(default_factory=lambda: _get_env_str("APP_NAME", "EDIP API"))
    app_version: str = field(default_factory=lambda: _get_env_str("APP_VERSION", "1.0.0"))
    app_env: str = field(default_factory=lambda: _get_env_str("APP_ENV", "development"))

    # API runtime
    api_host: str = field(default_factory=lambda: _get_env_str("API_HOST", "127.0.0.1"))
    api_port: int = field(default_factory=lambda: _get_env_int("API_PORT", 8000))

    # CORS
    allow_credentials: bool = field(default_factory=lambda: _get_env_bool("ALLOW_CREDENTIALS", True))
    allowed_origins: List[str] = field(
        default_factory=lambda: _get_env_list(
            "ALLOWED_ORIGINS",
            default=[
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://192.168.8.161:3000",
            ],
        )
    )

    # OpenAI / Pinecone / RAG
    openai_api_key: str = field(default_factory=lambda: _get_env_str("OPENAI_API_KEY"))
    pinecone_api_key: str = field(default_factory=lambda: _get_env_str("PINECONE_API_KEY"))
    pinecone_index_name: str = field(default_factory=lambda: _get_env_str("PINECONE_INDEX_NAME", "edip-rag-index"))
    pinecone_namespace: str = field(default_factory=lambda: _get_env_str("PINECONE_NAMESPACE", "edip-phase-6"))

    openai_embed_model: str = field(
        default_factory=lambda: _get_env_str("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    )
    openai_chat_model: str = field(
        default_factory=lambda: _get_env_str("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
    )

    rag_top_k: int = field(default_factory=lambda: _get_env_int("RAG_TOP_K", 5))
    rag_max_context_chars: int = field(default_factory=lambda: _get_env_int("RAG_MAX_CONTEXT_CHARS", 12000))


# Shared settings instance
settings = Settings()