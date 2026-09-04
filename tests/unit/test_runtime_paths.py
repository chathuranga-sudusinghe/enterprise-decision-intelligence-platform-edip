from __future__ import annotations

from pathlib import Path

import pytest

from pipelines import runtime_paths


def test_default_paths_do_not_depend_on_current_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("EDIP_FAVORITA_SOURCE_PATH", raising=False)
    monkeypatch.delenv("EDIP_ARTIFACT_ROOT", raising=False)

    assert runtime_paths.favorita_source_path() == (
        runtime_paths.REPOSITORY_ROOT
        / "data/processed/favorita_cleaned/favorita_cleaned.parquet"
    )
    assert runtime_paths.artifact_path("evaluation/result") == (
        runtime_paths.REPOSITORY_ROOT / "artifacts/evaluation/result"
    )


def test_configured_relative_paths_are_anchored_to_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDIP_FAVORITA_SOURCE_PATH", "inputs/source.parquet")
    monkeypatch.setenv("EDIP_ARTIFACT_ROOT", "outputs")

    assert runtime_paths.favorita_source_path() == (
        runtime_paths.REPOSITORY_ROOT / "inputs/source.parquet"
    )
    assert runtime_paths.artifact_path("evaluation/result") == (
        runtime_paths.REPOSITORY_ROOT / "outputs/evaluation/result"
    )


def test_configured_absolute_paths_are_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.parquet"
    artifacts = tmp_path / "artifacts"
    monkeypatch.setenv("EDIP_FAVORITA_SOURCE_PATH", str(source))
    monkeypatch.setenv("EDIP_ARTIFACT_ROOT", str(artifacts))

    assert runtime_paths.favorita_source_path() == source
    assert runtime_paths.artifact_path("evaluation/result") == (
        artifacts / "evaluation/result"
    )


def test_artifact_path_rejects_escape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EDIP_ARTIFACT_ROOT", raising=False)

    with pytest.raises(ValueError, match="below the artifact root"):
        runtime_paths.artifact_path("../outside")
