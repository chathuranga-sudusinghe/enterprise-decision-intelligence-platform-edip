from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from pipelines.evaluation import (
    run_favorita_lightgbm_bounded_integration as integration,
)
from pipelines.evaluation.favorita_temporal_validation import FINAL_HOLDOUT


def _config(tmp_path: Path) -> integration.BoundedIntegrationConfig:
    source_path = tmp_path / "source.parquet"
    source_path.write_bytes(b"fixture-source")
    return integration.BoundedIntegrationConfig(
        source_path=source_path,
        output_dir=tmp_path / "artifacts" / "integration" / "bounded",
    )


def test_bounded_configuration_is_explicit_and_separate() -> None:
    config = integration.BoundedIntegrationConfig()

    assert config.stores == (1, 2)
    assert config.item_cap == 50
    assert config.validation_batch_size == 128
    assert config.training_origins == integration.BOUNDED_TRAINING_ORIGINS
    assert config.output_dir == integration.DEFAULT_OUTPUT_DIR
    assert not integration._is_within(
        config.output_dir,
        integration.OFFICIAL_EVALUATION_OUTPUT_DIR,
    )
    assert not integration._is_within(
        config.output_dir,
        integration.DEFAULT_FOLD_OUTPUT_DIR,
    )


def test_integration_config_rejects_final_holdout_scoring(
    tmp_path: Path,
) -> None:
    config = replace(
        _config(tmp_path),
        validation_origin=FINAL_HOLDOUT.forecast_origin,
    )

    with pytest.raises(ValueError, match="must not score the final holdout"):
        integration.validate_integration_config(config)


@pytest.mark.parametrize(
    "official_output",
    [
        integration.OFFICIAL_EVALUATION_OUTPUT_DIR,
        integration.DEFAULT_FOLD_OUTPUT_DIR / "bounded",
    ],
)
def test_integration_config_rejects_official_output_paths(
    tmp_path: Path,
    official_output: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    config = replace(_config(tmp_path), output_dir=official_output)

    with pytest.raises(ValueError, match="separate from official artifacts"):
        integration.validate_integration_config(config)


def test_source_immutability_check_detects_change(tmp_path: Path) -> None:
    config = _config(tmp_path)
    before = integration._source_state(config.source_path)
    config.source_path.write_bytes(b"definitely-changed-source")

    with pytest.raises(AssertionError, match="Cleaned source changed"):
        integration._require_source_unchanged(config.source_path, before)


def test_failure_does_not_publish_completed_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config(tmp_path)

    def fail_materialization(*args: object, **kwargs: object) -> dict[str, object]:
        raise RuntimeError("bounded materialization failed")

    monkeypatch.setattr(
        integration,
        "materialize_feature_dataset",
        fail_materialization,
    )

    with pytest.raises(RuntimeError, match="bounded materialization failed"):
        integration.run_bounded_integration(config)

    assert not config.output_dir.exists()
    assert not integration._artifact_paths(config.output_dir).manifest.exists()
