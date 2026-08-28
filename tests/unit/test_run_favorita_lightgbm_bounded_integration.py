from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from pipelines.evaluation import (
    run_favorita_lightgbm_bounded_integration as integration,
)
from pipelines.evaluation.favorita_temporal_validation import FINAL_HOLDOUT


def _config(
    tmp_path: Path,
    profile: str = "small",
) -> integration.BoundedIntegrationConfig:
    source_path = tmp_path / "source.parquet"
    source_path.write_bytes(b"fixture-source")
    return integration.integration_config_for_profile(
        profile,
        source_path=source_path,
        output_dir=(
            tmp_path / "artifacts" / "integration" / f"{profile}_bounded"
        ),
    )


def test_small_profile_values_remain_unchanged() -> None:
    config = integration.integration_config_for_profile("small")

    assert config.profile == "small"
    assert config.stores == (1, 2)
    assert config.item_cap == 50
    assert config.validation_batch_size == 128
    assert config.training_origins == integration.SMALL_TRAINING_ORIGINS
    assert config.validation_origin == integration.BOUNDED_VALIDATION_ORIGIN
    assert config.output_dir == integration.SMALL_OUTPUT_DIR


def test_medium_profile_values_are_explicit() -> None:
    config = integration.integration_config_for_profile("medium")

    assert config.profile == "medium"
    assert config.stores == (1, 2, 3, 4, 5)
    assert config.item_cap == 200
    assert len(config.training_origins) == 12
    assert config.training_origins == integration.MEDIUM_TRAINING_ORIGINS
    assert config.validation_origin == integration.BOUNDED_VALIDATION_ORIGIN
    assert config.validation_batch_size == 128
    assert config.output_dir == integration.MEDIUM_OUTPUT_DIR


def test_large_profile_values_are_explicit_and_ordered() -> None:
    config = integration.integration_config_for_profile("large")

    assert config.profile == "large"
    assert config.stores == tuple(range(1, 11))
    assert len(config.stores) == 10
    assert config.item_cap == 500
    assert len(config.training_origins) == 24
    assert config.training_origins == integration.LARGE_TRAINING_ORIGINS
    assert tuple(sorted(set(config.training_origins))) == config.training_origins
    assert config.training_origins[-1] + timedelta(days=16) <= (
        config.validation_origin
    )
    assert config.validation_origin == integration.BOUNDED_VALIDATION_ORIGIN
    assert config.validation_batch_size == 128
    assert config.output_dir == integration.LARGE_OUTPUT_DIR


def test_profile_output_paths_are_separate_from_each_other_and_official() -> None:
    configs = tuple(
        integration.integration_config_for_profile(profile)
        for profile in integration.PROFILE_NAMES
    )

    assert len({config.output_dir for config in configs}) == 3
    for config in configs:
        for other in configs:
            if config.profile != other.profile:
                assert not integration._is_within(
                    config.output_dir,
                    other.output_dir,
                )
        assert not integration._is_within(
            config.output_dir,
            integration.OFFICIAL_EVALUATION_OUTPUT_DIR,
        )
        assert not integration._is_within(
            config.output_dir,
            integration.DEFAULT_FOLD_OUTPUT_DIR,
        )


@pytest.mark.parametrize("profile", integration.PROFILE_NAMES)
def test_integration_config_rejects_final_holdout_scoring(
    tmp_path: Path,
    profile: str,
) -> None:
    config = replace(
        _config(tmp_path, profile),
        validation_origin=FINAL_HOLDOUT.forecast_origin,
    )

    with pytest.raises(ValueError, match="must not score the final holdout"):
        integration.validate_integration_config(config)


@pytest.mark.parametrize(
    ("profile", "other_profile"),
    [
        (profile, other_profile)
        for profile in integration.PROFILE_NAMES
        for other_profile in integration.PROFILE_NAMES
        if profile != other_profile
    ],
)
def test_profile_cannot_use_other_profile_default_output(
    tmp_path: Path,
    profile: str,
    other_profile: str,
) -> None:
    config = _config(tmp_path, profile)
    config = replace(
        config,
        output_dir=integration.INTEGRATION_PROFILES[other_profile].output_dir,
    )

    with pytest.raises(ValueError, match="separate from other profiles"):
        integration.validate_integration_config(config)


def test_default_small_output_is_explicit_and_separate() -> None:
    config = integration.BoundedIntegrationConfig()

    assert config.output_dir == integration.SMALL_OUTPUT_DIR
    assert not integration._is_within(
        config.output_dir,
        integration.OFFICIAL_EVALUATION_OUTPUT_DIR,
    )
    assert not integration._is_within(
        config.output_dir,
        integration.DEFAULT_FOLD_OUTPUT_DIR,
    )


@pytest.mark.parametrize(
    ("profile", "official_output"),
    [
        (profile, official_output)
        for profile in integration.PROFILE_NAMES
        for official_output in (
            integration.OFFICIAL_EVALUATION_OUTPUT_DIR,
            integration.DEFAULT_FOLD_OUTPUT_DIR / "bounded",
        )
    ],
)
def test_integration_config_rejects_official_output_paths(
    tmp_path: Path,
    profile: str,
    official_output: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    config = replace(
        _config(tmp_path, profile),
        output_dir=official_output,
    )

    with pytest.raises(ValueError, match="separate from official artifacts"):
        integration.validate_integration_config(config)


@pytest.mark.parametrize("profile", integration.PROFILE_NAMES)
def test_source_immutability_check_detects_change(
    tmp_path: Path,
    profile: str,
) -> None:
    config = _config(tmp_path, profile)
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


@pytest.mark.parametrize("profile", integration.PROFILE_NAMES)
def test_cli_accepts_bounded_profiles(profile: str) -> None:
    args = integration._argument_parser().parse_args(["--profile", profile])

    assert args.profile == profile
    assert args.output_dir is None
