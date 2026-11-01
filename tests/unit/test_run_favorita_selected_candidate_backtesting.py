from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from pipelines.evaluation import run_favorita_selected_candidate_backtesting as runner


def test_runner_passes_only_frozen_configuration_and_retains_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.parquet"
    source.write_bytes(b"immutable source")
    folds = tmp_path / "folds"
    folds.mkdir()
    output = tmp_path / "result"
    checked = Mock()
    monkeypatch.setattr(runner, "validate_evaluation_config", checked)
    calls: list[runner.FavoritaEvaluationRunConfig] = []

    def evaluate(config: runner.FavoritaEvaluationRunConfig) -> SimpleNamespace:
        calls.append(config)
        predictions = output / "predictions.parquet"
        predictions.write_bytes(b"retained selected predictions")
        manifest = output / "run_manifest.json"
        manifest.write_text(
            json.dumps({"configuration": {"hyperparameter_tuning": True}})
        )
        return SimpleNamespace(predictions=predictions, run_manifest=manifest)

    monkeypatch.setattr(runner, "run_evaluation", evaluate)
    path = runner.run_selected_candidate(
        source_path=source, fold_root=folds, output_dir=output
    )
    config = calls[0]
    assert config.model_parameters == {
        "objective": "regression",
        "learning_rate": 0.02757359293934948,
        "num_leaves": 123,
        "min_data_in_leaf": 89,
        "feature_fraction": 0.8394633936788146,
        "seed": 42,
        "num_threads": 4,
        "verbosity": -1,
        "deterministic": True,
        "force_col_wise": True,
        "device_type": "cpu",
    }
    assert config.num_boost_round == 150
    assert config.feature_contract == "time-aware"
    assert config.fold_output_dir == folds
    assert config.overwrite is False
    checked.assert_called_once_with(config)
    manifest = json.loads(path.read_text())
    assert manifest["configuration"]["hyperparameter_tuning"] is False
    assert manifest["selected_candidate"]["predictions_sha256"] == runner.sha256_file(
        output / "predictions.parquet"
    )
    assert manifest["selected_candidate"]["retuned"] is False
    assert manifest["selected_candidate"]["status"] == "completed"
    assert manifest["selected_candidate"]["issue_number"] == 128
    assert manifest["selected_candidate"]["code"]["source_sha256"]
    assert source.read_bytes() == b"immutable source"
    assert list(folds.iterdir()) == []
    with pytest.raises(FileExistsError):
        runner.run_selected_candidate(
            source_path=source, fold_root=folds, output_dir=output
        )
    assert len(calls) == 1


def test_invalid_preflight_never_trains(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    train = Mock()
    monkeypatch.setattr(runner, "run_evaluation", train)
    with pytest.raises(FileNotFoundError):
        runner.run_selected_candidate(
            source_path=tmp_path / "missing",
            fold_root=tmp_path / "folds",
            output_dir=tmp_path / "result",
        )
    train.assert_not_called()
    assert not (tmp_path / "result").exists()


def test_failed_run_cannot_be_accidentally_restarted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "validate_evaluation_config", Mock())
    train = Mock(side_effect=RuntimeError("interrupted fit"))
    monkeypatch.setattr(runner, "run_evaluation", train)
    args = dict(
        source_path=tmp_path / "source",
        fold_root=tmp_path / "folds",
        output_dir=tmp_path / "output",
    )
    with pytest.raises(RuntimeError, match="interrupted"):
        runner.run_selected_candidate(**args)
    with pytest.raises(FileExistsError):
        runner.run_selected_candidate(**args)
    assert train.call_count == 1


def test_output_cannot_overlap_fold_artifacts(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="overlap"):
        runner.run_selected_candidate(
            source_path=tmp_path / "source",
            fold_root=tmp_path / "folds",
            output_dir=tmp_path / "folds/result",
        )


def test_real_validator_and_selected_wrapper_feed_uncertainty_without_training(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from pipelines import runtime_paths
    from pipelines.evaluation import run_favorita_lightgbm_evaluation as evaluator
    from pipelines.evaluation import run_favorita_uncertainty_evaluation as uncertainty
    from tests.unit.test_run_favorita_lightgbm_evaluation import (
        _config,
        _install_serial_fakes,
    )

    config = _config(tmp_path)
    _, models = _install_serial_fakes(monkeypatch, config)
    # Preserve the real validator and evaluator; only model fitting/prediction
    # is fake. Existing manifests use repository-relative roots.
    monkeypatch.setattr(runtime_paths, "REPOSITORY_ROOT", tmp_path)
    before = {}
    for paths in evaluator.approved_fold_artifact_paths(config.fold_output_dir):
        manifest = json.loads(paths.manifest.read_text())
        manifest["artifact_root"] = "folds"
        paths.manifest.write_text(json.dumps(manifest))
        for path in (paths.training, paths.validation, paths.manifest):
            before[path] = (path.read_bytes(), path.stat().st_mtime_ns)
    selected = runner.run_selected_candidate(
        source_path=config.source_path,
        fold_root=Path("folds"),
        output_dir=config.output_dir,
    )
    assert len(models) == 4
    assert all(model.model_parameters == runner.frozen_parameters() for model in models)
    consumer = uncertainty.run_uncertainty(
        input_dir=selected.parent, output_dir=tmp_path / "uncertainty"
    )
    result = json.loads(consumer.read_text())
    assert result["evaluated_folds"] == [2, 3, 4]
    assert result["holdout_touched"] is False
    assert before == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before}


@pytest.mark.parametrize(
    "failure", ["evaluation", "source_change", "enrichment", "publication", "interrupt"]
)
def test_failure_removes_completion_claim_but_preserves_partial_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    output = tmp_path / "output"
    monkeypatch.setattr(runner, "validate_evaluation_config", Mock())
    code = {"git_commit": "a" * 40}
    monkeypatch.setattr(
        runner,
        "code_provenance",
        Mock(side_effect=[code, {}])
        if failure == "source_change"
        else Mock(return_value=code),
    )

    def evaluate(config):
        predictions = output / "predictions.parquet"
        predictions.write_bytes(b"partial evidence")
        manifest = output / "run_manifest.json"
        manifest.write_text(
            json.dumps({"run": {"status": "completed"}, "configuration": {}})
        )
        if failure == "evaluation":
            raise RuntimeError("evaluation failed")
        return SimpleNamespace(predictions=predictions, run_manifest=manifest)

    monkeypatch.setattr(runner, "run_evaluation", evaluate)
    if failure in {"enrichment", "interrupt"}:
        error = (
            KeyboardInterrupt()
            if failure == "interrupt"
            else RuntimeError("enrichment failed")
        )
        monkeypatch.setattr(runner, "write_json", Mock(side_effect=error))
    if failure == "publication":
        monkeypatch.setattr(
            Path, "replace", Mock(side_effect=OSError("publication failed"))
        )
    expected = (
        KeyboardInterrupt
        if failure == "interrupt"
        else (ValueError, RuntimeError, OSError)
    )
    with pytest.raises(expected):
        runner.run_selected_candidate(
            source_path=tmp_path / "source",
            fold_root=tmp_path / "folds",
            output_dir=output,
        )
    assert (output / "predictions.parquet").read_bytes() == b"partial evidence"
    assert not (output / "run_manifest.json").exists()
    assert not (output / ".selected_manifest.tmp").exists()
    with pytest.raises(FileExistsError):
        runner.run_selected_candidate(
            source_path=tmp_path / "source",
            fold_root=tmp_path / "folds",
            output_dir=output,
        )
