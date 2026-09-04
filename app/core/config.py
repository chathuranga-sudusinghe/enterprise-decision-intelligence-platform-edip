from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LOCAL_ENVIRONMENTS = frozenset({"development", "dev", "local"})
_EXTERNAL_APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
if _EXTERNAL_APP_ENV in _LOCAL_ENVIRONMENTS:
    # Environment variables retain precedence over local developer conveniences.
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def _get_env_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _get_env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y", "on"}:
        return True
    if normalized in {"false", "0", "no", "n", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


def _get_env_list(name: str, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    raw_value = os.getenv(name, "")
    if not raw_value.strip():
        return default
    return tuple(item.strip() for item in raw_value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from authoritative environment variables."""

    app_name: str = field(default_factory=lambda: _get_env_str("APP_NAME", "EDIP API"))
    app_version: str = field(default_factory=lambda: _get_env_str("APP_VERSION", "1.0.0"))
    app_env: str = field(default_factory=lambda: _get_env_str("APP_ENV", "development").lower())
    api_host: str = field(default_factory=lambda: _get_env_str("API_HOST", "127.0.0.1"))
    api_port: int = field(default_factory=lambda: _get_env_int("API_PORT", 8000))
    allow_credentials: bool = field(
        default_factory=lambda: _get_env_bool("ALLOW_CREDENTIALS", True)
    )
    allowed_origins: tuple[str, ...] = field(
        default_factory=lambda: _get_env_list(
            "ALLOWED_ORIGINS",
            default=("http://localhost:3000", "http://127.0.0.1:3000"),
        )
    )

    def __post_init__(self) -> None:
        if self.app_env not in {*_LOCAL_ENVIRONMENTS, "test", "staging", "production"}:
            raise ValueError("APP_ENV must be development, dev, local, test, staging, or production")
        if not 1 <= self.api_port <= 65535:
            raise ValueError("API_PORT must be between 1 and 65535")
        if not self.api_host:
            raise ValueError("API_HOST must not be empty")
        if self.app_env != "production":
            return
        if os.getenv("ALLOWED_ORIGINS", "").strip() == "":
            raise ValueError("ALLOWED_ORIGINS is required in production")
        if "*" in self.allowed_origins and self.allow_credentials:
            raise ValueError(
                "ALLOWED_ORIGINS cannot contain '*' when credentials are enabled"
            )
        if any(
            origin.startswith(("http://localhost", "http://127.0.0.1"))
            for origin in self.allowed_origins
        ):
            raise ValueError("loopback ALLOWED_ORIGINS are not valid in production")


settings = Settings()
