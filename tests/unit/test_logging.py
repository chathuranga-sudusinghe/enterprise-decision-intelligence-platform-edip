from __future__ import annotations

from pathlib import Path

import pytest

from app.core.logging import configure_logging


def test_console_logging_does_not_create_repository_log_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    configure_logging()

    assert not (tmp_path / "monitoring/logs").exists()


def test_file_logging_requires_explicit_directory() -> None:
    with pytest.raises(ValueError, match="log_dir is required"):
        configure_logging(log_to_file=True)


def test_explicit_local_file_logging_creates_requested_file(tmp_path: Path) -> None:
    configure_logging(log_to_file=True, log_dir=tmp_path, log_filename="local.log")

    assert (tmp_path / "local.log").is_file()
