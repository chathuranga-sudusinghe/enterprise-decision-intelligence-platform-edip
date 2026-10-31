from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from pipelines.evaluation import run_favorita_uncertainty_evaluation as runner
from pipelines.evaluation.favorita_temporal_validation import APPROVED_FOLDS
from pipelines.evaluation.favorita_uncertainty import interval_metrics
from tests.unit.test_favorita_uncertainty import prediction_fixture


def selected_evidence(root: Path) -> tuple[Path, dict]:
    root.mkdir()
    frame = prediction_fixture()
    frame.to_parquet(root / "predictions.parquet", index=False)
    manifest = {
        "selected_candidate": {
            "schema_version": 2,
            "status": "completed",
            "candidate_id": runner.CANDIDATE_ID,
            "issue_number": runner.ISSUE_NUMBER,
            "code": {
                "git_commit": "a" * 40,
                "working_tree_dirty": False,
                "source_sha256": {
                    name: "b" * 64 for name in runner.PROVENANCE_SOURCE_PATHS
                },
            },
            "runtime_versions": {
                name: "synthetic-version"
                for name in ("python", *runner.RUNTIME_PACKAGES)
            },
            "prediction_keys": list(runner.PREDICTION_KEYS),
            "retuned": False,
            "model_replaced": False,
            "predictions_sha256": runner.sha256_file(root / "predictions.parquet"),
        },
        "run": {"status": "completed"},
        "configuration": {
            "feature_contract": "time-aware",
            "model_parameters": runner.frozen_parameters(),
            "num_boost_round": 150,
            "hyperparameter_tuning": False,
            "candidate_feature_columns": list(
                runner.resolve_feature_contract("time-aware")
            ),
            "forecast_horizons": list(range(1, 17)),
            "recursive_feedback": False,
            "future_promotion_assumption": False,
            "future_holiday_assumption": False,
        },
        "final_holdout": {
            "scored": False,
            "materialized": False,
            "holdout_start": "2017-07-31",
            "holdout_end": "2017-08-15",
        },
        "fold_artifact_consumption": {
            "mode": "consumption-only",
            "fold_artifacts_mutated": False,
        },
        "evaluation": {"prediction_rows": len(frame)},
        "folds": [
            {
                "fold_id": f.fold_id,
                "forecast_origin": f.forecast_origin.isoformat(),
                "validation_start": f.validation_start.isoformat(),
                "validation_end": f.validation_end.isoformat(),
                "feature_contract": "time-aware",
                "model_parameters": runner.frozen_parameters(),
                "num_boost_round": 150,
                "validation_rows": int(frame.fold_id.eq(f.fold_id).sum()),
            }
            for f in APPROVED_FOLDS
        ],
    }
    runner.write_json(root / "run_manifest.json", manifest)
    return root, manifest


def test_artifacts_metrics_audit_and_reproducibility(tmp_path: Path) -> None:
    source, _ = selected_evidence(tmp_path / "input")
    original_hashes = {p.name: runner.sha256_file(p) for p in source.iterdir()}
    outputs = []
    for name in ("first", "second"):
        destination = tmp_path / name
        runner.run_uncertainty(input_dir=source, output_dir=destination)
        outputs.append(destination)
    first, second = outputs
    expected = {
        "predictions.parquet",
        "calibration.json",
        "overall_metrics.json",
        "fold_metrics.json",
        "horizon_metrics.json",
        "run_manifest.json",
        "evaluation_summary.md",
    }
    assert {p.name for p in first.iterdir()} == expected
    assert {p.name: runner.sha256_file(p) for p in first.iterdir()} == {
        p.name: runner.sha256_file(p) for p in second.iterdir()
    }
    assert original_hashes == {p.name: runner.sha256_file(p) for p in source.iterdir()}
    frame = pd.read_parquet(first / "predictions.parquet")
    assert set(frame.fold_id) == {2, 3, 4}
    assert {
        "actual_unit_sales",
        "prediction",
        "actual_demand",
        "point_forecast",
        "lower_bound",
        "upper_bound",
        "interval_width",
        "uncertainty_level",
    }.issubset(frame.columns)
    overall = json.loads((first / "overall_metrics.json").read_text())
    folds = json.loads((first / "fold_metrics.json").read_text())
    horizons = json.loads((first / "horizon_metrics.json").read_text())
    assert len(horizons) == 16
    assert sum(r["row_count"] for r in folds) == overall["row_count"] == 144
    assert sum(r["row_count"] for r in horizons) == 144
    assert overall == interval_metrics(
        frame.actual_unit_sales, frame.lower_bound, frame.upper_bound
    )
    weighted_width = sum(r["mpiw"] * r["row_count"] for r in folds) / 144
    assert overall["mpiw"] == pytest.approx(weighted_width)
    assert overall["picp"] != pytest.approx(sum(r["picp"] for r in folds) / 3)
    assert overall["mpiw"] != pytest.approx(sum(r["mpiw"] for r in folds) / 3)
    manifest = json.loads((first / "run_manifest.json").read_text())
    assert manifest["holdout_touched"] is False
    assert manifest["issue_number"] == 128
    producer = json.loads((source / "run_manifest.json").read_text())[
        "selected_candidate"
    ]
    assert manifest["input"]["producer_code"] == producer["code"]
    assert (
        manifest["input"]["producer_runtime_versions"] == producer["runtime_versions"]
    )
    assert manifest["code"]["git_commit"] != producer["code"]["git_commit"]
    for name, digest in manifest["artifacts_sha256"].items():
        assert digest == runner.sha256_file(first / name)
    with pytest.raises(FileExistsError):
        runner.run_uncertainty(input_dir=source, output_dir=first)


@pytest.mark.parametrize(
    "mutation",
    [
        "parameters",
        "fold_parameters",
        "holdout",
        "candidate",
        "missing",
        "row_count",
        "fold_count",
        "checksum",
        "features",
    ],
)
def test_rejects_provenance_mismatch_before_publication(
    tmp_path: Path, mutation: str
) -> None:
    source, manifest = selected_evidence(tmp_path / "input")
    if mutation == "parameters":
        manifest["configuration"]["model_parameters"]["num_leaves"] = 31
    elif mutation == "fold_parameters":
        manifest["folds"][1]["model_parameters"]["seed"] = 7
    elif mutation == "holdout":
        manifest["final_holdout"]["scored"] = True
    elif mutation == "candidate":
        manifest["selected_candidate"]["candidate_id"] = "different-model"
    elif mutation == "missing":
        del manifest["selected_candidate"]
    elif mutation == "row_count":
        manifest["evaluation"]["prediction_rows"] += 1
    elif mutation == "fold_count":
        manifest["folds"][0]["validation_rows"] += 1
    elif mutation == "features":
        manifest["configuration"]["candidate_feature_columns"] = ["item_nbr"]
    else:
        manifest["selected_candidate"]["predictions_sha256"] = "0" * 64
    runner.write_json(source / "run_manifest.json", manifest)
    destination = tmp_path / "output"
    with pytest.raises(ValueError, match="provenance"):
        runner.run_uncertainty(input_dir=source, output_dir=destination)
    assert not destination.exists()


@pytest.mark.parametrize(
    "mutation,match", [("duplicate", "Duplicate"), ("holdout", "holdout")]
)
def test_checksummed_but_invalid_rows_are_rejected(
    tmp_path: Path, mutation: str, match: str
) -> None:
    source, manifest = selected_evidence(tmp_path / "input")
    frame = pd.read_parquet(source / "predictions.parquet")
    if mutation == "duplicate":
        frame = pd.concat([frame, frame.iloc[:1]], ignore_index=True)
    else:
        frame.loc[0, "forecast_date"] = pd.Timestamp("2017-07-31")
    frame.to_parquet(source / "predictions.parquet", index=False)
    manifest["selected_candidate"]["predictions_sha256"] = runner.sha256_file(
        source / "predictions.parquet"
    )
    runner.write_json(source / "run_manifest.json", manifest)
    with pytest.raises(ValueError, match=match):
        runner.run_uncertainty(input_dir=source, output_dir=tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_input_changes_during_evaluation_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _ = selected_evidence(tmp_path / "input")
    original = runner.sequential_intervals

    def evaluate(frame: pd.DataFrame) -> tuple:
        result = original(frame)
        with (source / "run_manifest.json").open("a") as stream:
            stream.write("\n")
        return result

    monkeypatch.setattr(runner, "sequential_intervals", evaluate)
    with pytest.raises(ValueError, match="changed"):
        runner.run_uncertainty(input_dir=source, output_dir=tmp_path / "output")
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("code", None),
        ("code.git_commit", "not-a-commit"),
        ("code.working_tree_dirty", "false"),
        ("code.source_sha256", {}),
        ("runtime_versions", None),
        ("runtime_versions.python", ""),
        ("runtime_versions.numpy", 2),
        ("status", "pending"),
        ("schema_version", 1),
        ("issue_number", 999),
        ("prediction_keys", ["item_nbr"]),
    ],
)
def test_malformed_producer_is_rejected_before_reading_predictions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    source, manifest = selected_evidence(tmp_path / "input")
    target = manifest["selected_candidate"]
    keys = field.split(".")
    for key in keys[:-1]:
        target = target[key]
    target[keys[-1]] = value
    runner.write_json(source / "run_manifest.json", manifest)
    monkeypatch.setattr(
        pd, "read_parquet", lambda *a, **kw: pytest.fail("must reject before row reads")
    )
    with pytest.raises(ValueError, match="provenance"):
        runner.run_uncertainty(input_dir=source, output_dir=tmp_path / "output")
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "field", ["code", "runtime_versions", "prediction_keys", "status"]
)
def test_missing_producer_identity_is_rejected(tmp_path: Path, field: str) -> None:
    source, manifest = selected_evidence(tmp_path / "input")
    del manifest["selected_candidate"][field]
    runner.write_json(source / "run_manifest.json", manifest)
    with pytest.raises(ValueError, match="provenance"):
        runner.run_uncertainty(input_dir=source, output_dir=tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_invalid_producer_source_digest_is_rejected(tmp_path: Path) -> None:
    source, manifest = selected_evidence(tmp_path / "input")
    manifest["selected_candidate"]["code"]["source_sha256"]["pyproject.toml"] = (
        "invalid"
    )
    runner.write_json(source / "run_manifest.json", manifest)
    with pytest.raises(ValueError, match="source hash provenance"):
        runner.run_uncertainty(input_dir=source, output_dir=tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_generic_completed_run_is_not_selected_candidate_evidence(
    tmp_path: Path,
) -> None:
    source, manifest = selected_evidence(tmp_path / "input")
    del manifest["selected_candidate"]
    runner.write_json(source / "run_manifest.json", manifest)
    with pytest.raises(ValueError, match="provenance"):
        runner.run_uncertainty(input_dir=source, output_dir=tmp_path / "output")


def test_consumer_code_change_cannot_publish_completed_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from unittest.mock import Mock

    source, _ = selected_evidence(tmp_path / "input")
    monkeypatch.setattr(
        runner, "code_provenance", Mock(side_effect=[{"git_commit": "a" * 40}, {}])
    )
    with pytest.raises(ValueError, match="Consumer source code changed"):
        runner.run_uncertainty(input_dir=source, output_dir=tmp_path / "output")
    assert not (tmp_path / "output").exists()
    assert not list(tmp_path.glob(".favorita-uncertainty-*"))


@pytest.mark.parametrize("filename", ["overall_metrics.json", "run_manifest.json"])
def test_publication_failure_has_no_completion_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, filename: str
) -> None:
    source, _ = selected_evidence(tmp_path / "input")
    original_hashes = {p.name: runner.sha256_file(p) for p in source.iterdir()}
    original_rename = Path.rename

    def rename(path, target):
        if path.name == filename:
            raise OSError("interrupted publication")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", rename)
    output = tmp_path / "output"
    with pytest.raises(OSError, match="interrupted"):
        runner.run_uncertainty(input_dir=source, output_dir=output)
    assert not (output / "run_manifest.json").exists()
    assert original_hashes == {p.name: runner.sha256_file(p) for p in source.iterdir()}
    assert not list(tmp_path.glob(".favorita-uncertainty-*"))
