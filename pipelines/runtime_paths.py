"""Portable filesystem paths for offline EDIP pipeline commands."""

from __future__ import annotations

import os
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _configured_path(environment_variable: str, default: Path) -> Path:
    """Resolve an environment override without depending on the process CWD."""

    raw_value = os.getenv(environment_variable)
    candidate = Path(raw_value).expanduser() if raw_value else default
    if not candidate.is_absolute():
        candidate = REPOSITORY_ROOT / candidate
    return candidate.resolve()


def resolve_cli_path(value: str | Path) -> Path:
    """Resolve an explicit CLI path relative to the repository, not the caller CWD."""

    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = REPOSITORY_ROOT / candidate
    return candidate.resolve()


def favorita_source_path() -> Path:
    """Return the configured cleaned Favorita source path."""

    return _configured_path(
        "EDIP_FAVORITA_SOURCE_PATH",
        REPOSITORY_ROOT
        / "data"
        / "processed"
        / "favorita_cleaned"
        / "favorita_cleaned.parquet",
    )


def artifact_path(relative_path: str | Path) -> Path:
    """Return a path below the configured EDIP artifact root."""

    artifact_root = _configured_path(
        "EDIP_ARTIFACT_ROOT",
        REPOSITORY_ROOT / "artifacts",
    )
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("artifact relative_path must remain below the artifact root")
    return (artifact_root / relative).resolve()
