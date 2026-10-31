"""Retain canonical validation predictions for the frozen selected candidate only."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path
from typing import Any

from pipelines.evaluation.favorita_uncertainty import PREDICTION_KEYS
from pipelines.evaluation.run_favorita_lightgbm_evaluation import (
    FavoritaEvaluationRunConfig,
    run_evaluation,
    validate_evaluation_config,
)
from pipelines.models.favorita_lightgbm import LIGHTGBM_PARAMETERS
from pipelines.models.favorita_model_bundle import (
    FROZEN_MODEL_PARAMETERS,
    FROZEN_NUM_BOOST_ROUND,
)
from pipelines.runtime_paths import (
    REPOSITORY_ROOT,
    artifact_path,
    favorita_source_path,
    resolve_cli_path,
)

CANDIDATE_ID = "favorita_time_aware_frozen_trial_0"
ISSUE_NUMBER = 128
PROVENANCE_SOURCE_PATHS = (
    "pyproject.toml",
    "pipelines/runtime_paths.py",
    "pipelines/evaluation/favorita_uncertainty.py",
    "pipelines/evaluation/favorita_metrics.py",
    "pipelines/evaluation/favorita_temporal_validation.py",
    "pipelines/evaluation/favorita_backtesting.py",
    "pipelines/evaluation/run_favorita_selected_candidate_backtesting.py",
    "pipelines/evaluation/run_favorita_uncertainty_evaluation.py",
    "pipelines/evaluation/run_favorita_lightgbm_evaluation.py",
    "pipelines/features/favorita_model_ready.py",
    "pipelines/features/build_favorita_fold_datasets.py",
    "pipelines/models/favorita_lightgbm.py",
    "pipelines/models/favorita_model_bundle.py",
    "pipelines/models/favorita_bundle_inference.py",
)
RUNTIME_PACKAGES = ("numpy", "pandas", "pyarrow", "lightgbm")


def frozen_parameters() -> dict[str, Any]:
    return {**LIGHTGBM_PARAMETERS, **FROZEN_MODEL_PARAMETERS, "device_type": "cpu"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def code_provenance() -> dict[str, Any]:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    status = subprocess.run(
        [
            "git",
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--",
            *PROVENANCE_SOURCE_PATHS,
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {
        "git_commit": result.stdout.strip(),
        "working_tree_dirty": bool(status.stdout.strip()),
        "source_sha256": {
            name: sha256_file(REPOSITORY_ROOT / name)
            for name in PROVENANCE_SOURCE_PATHS
        },
    }


def runtime_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        **{name: version(name) for name in RUNTIME_PACKAGES},
    }


def run_selected_candidate(
    *, source_path: Path, fold_root: Path, output_dir: Path
) -> Path:
    """Run four serial fits, with no parameter search or model publication."""
    source_path, fold_root, output_dir = map(
        resolve_cli_path, (source_path, fold_root, output_dir)
    )
    if output_dir.exists():
        raise FileExistsError(f"Refusing existing output directory: {output_dir}")
    if (
        output_dir == fold_root
        or fold_root in output_dir.parents
        or output_dir in fold_root.parents
        or output_dir in source_path.parents
    ):
        raise ValueError("Output directory overlaps input artifacts")
    config = FavoritaEvaluationRunConfig(
        source_path=source_path,
        output_dir=output_dir,
        fold_output_dir=fold_root,
        feature_contract="time-aware",
        model_parameters=frozen_parameters(),
        num_boost_round=FROZEN_NUM_BOOST_ROUND,
        overwrite=False,
    )
    validate_evaluation_config(config)
    # Reserve exclusively before training; a failed run remains inspectable and
    # cannot be accidentally retrained/overwritten by invoking this command again.
    code = code_provenance()
    output_dir.mkdir(parents=True, exist_ok=False)
    temporary = output_dir / ".selected_manifest.tmp"
    completed = False
    try:
        paths = run_evaluation(config)
        if code_provenance() != code:
            raise ValueError("Producer source code changed during backtesting")
        manifest = json.loads(paths.run_manifest.read_text(encoding="utf-8"))
        # The generic evaluator calls any custom configuration tuning. Correct
        # only this newly produced manifest for the already frozen candidate.
        manifest["configuration"]["hyperparameter_tuning"] = False
        manifest["selected_candidate"] = {
            "schema_version": 2,
            "status": "completed",
            "issue_number": ISSUE_NUMBER,
            "historical_planning_label": "SCRUM-21",
            "candidate_id": CANDIDATE_ID,
            "selection": "Previously selected SCRUM-59 Trial 0 Time-Aware configuration",
            "retuned": False,
            "model_replaced": False,
            "prediction_keys": list(PREDICTION_KEYS),
            "predictions_sha256": sha256_file(paths.predictions),
            "code": code,
            "runtime_versions": runtime_versions(),
        }
        write_json(temporary, manifest)
        temporary.replace(paths.run_manifest)
        completed = True
        return paths.run_manifest
    finally:
        temporary.unlink(missing_ok=True)
        if not completed:
            # Only our exclusively reserved new output directory is affected.
            # Retain partial predictions for inspection, but no completion claim.
            (output_dir / "run_manifest.json").unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-path", type=resolve_cli_path, default=favorita_source_path()
    )
    parser.add_argument(
        "--fold-root",
        type=resolve_cli_path,
        default=artifact_path("features/favorita_2017_four_fold_time_aware"),
    )
    parser.add_argument(
        "--output-dir",
        type=resolve_cli_path,
        default=artifact_path("evaluation/favorita_selected_candidate"),
    )
    args = parser.parse_args(argv)
    print(
        run_selected_candidate(
            source_path=args.source_path,
            fold_root=args.fold_root,
            output_dir=args.output_dir,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
