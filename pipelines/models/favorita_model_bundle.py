"""Export fitted Time-Aware Favorita adapters as native model bundles."""

from __future__ import annotations

import json
import os
import platform
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd

from pipelines.models.favorita_bundle_inference import (
    BUNDLE_SCHEMA_VERSION,
    METADATA_FILENAME,
    MODEL_FILENAME,
    TIME_AWARE_FEATURE_CONTRACT,
    sha256_file,
)
from pipelines.models.favorita_lightgbm import FavoritaLightGBMAdapter
from pipelines.runtime_paths import resolve_cli_path

SCRUM_19_EVIDENCE_PATH = (
    "artifacts/evaluation/favorita_scrum_19_final_holdout/scrum_19_final_holdout.json"
)
FROZEN_MODEL_PARAMETERS: Mapping[str, object] = {
    "learning_rate": 0.02757359293934948,
    "num_leaves": 123,
    "min_data_in_leaf": 89,
    "feature_fraction": 0.8394633936788146,
}
FROZEN_NUM_BOOST_ROUND = 150


def _json_value(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Mapping):
        return {str(k): _json_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Non-JSON bundle metadata value: {type(value).__name__}")


def export_favorita_model_bundle(
    adapter: FavoritaLightGBMAdapter,
    target_dir: str | Path,
    *,
    model_version: str,
    source_dataset_identity: str | None = None,
    source_dataset_digest: str | None = None,
    code_commit: str | None = None,
) -> Path:
    """Write one immutable Time-Aware native LightGBM bundle."""
    if not isinstance(adapter, FavoritaLightGBMAdapter):
        raise TypeError("adapter must be a FavoritaLightGBMAdapter")
    if not adapter.is_fitted:
        raise RuntimeError("Cannot export an unfitted FavoritaLightGBMAdapter")
    if adapter.feature_contract_name != TIME_AWARE_FEATURE_CONTRACT:
        raise ValueError("Only the selected Time-Aware model arm can be exported")
    if not isinstance(model_version, str) or not model_version.strip():
        raise ValueError("model_version must be non-empty")
    if not adapter.fitted_feature_columns:
        raise RuntimeError("Fitted feature metadata is missing")
    if set(adapter.categorical_feature_columns) != set(adapter.categorical_levels):
        raise RuntimeError("Categorical preprocessing metadata is incomplete")
    mismatched = {
        name: adapter.model_parameters.get(name)
        for name, expected in FROZEN_MODEL_PARAMETERS.items()
        if adapter.model_parameters.get(name) != expected
    }
    if mismatched or adapter.num_boost_round != FROZEN_NUM_BOOST_ROUND:
        raise ValueError(
            "Adapter does not use the frozen selected Time-Aware LightGBM configuration"
        )
    root = resolve_cli_path(target_dir)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty bundle: {root}")
    root.mkdir(parents=True, exist_ok=True)
    model_tmp, metadata_tmp = root / ".model.txt.tmp", root / ".metadata.json.tmp"
    try:
        adapter.fitted_booster.save_model(str(model_tmp))
        metadata = {
            "bundle_schema_version": BUNDLE_SCHEMA_VERSION,
            "model_version": model_version.strip(),
            "model_type": "global_direct_horizon_regressor",
            "model_family": "lightgbm",
            "model_arm": "time_aware",
            "target": "unit_sales",
            "feature_contract_name": adapter.feature_contract_name,
            "fitted_feature_columns": list(adapter.fitted_feature_columns),
            "categorical_feature_columns": list(adapter.categorical_feature_columns),
            "categorical_levels": _json_value(adapter.categorical_levels),
            "excluded_all_null_feature_columns": list(
                adapter.excluded_all_null_features
            ),
            "effective_lightgbm_parameters": _json_value(adapter.model_parameters),
            "num_boost_round": adapter.num_boost_round,
            "provenance": {
                "research_evidence": "SCRUM-19",
                "research_evidence_path": SCRUM_19_EVIDENCE_PATH,
                "source_dataset_identity": source_dataset_identity,
                "source_dataset_digest": source_dataset_digest,
                "code_git_commit": code_commit,
            },
            "runtime_versions": {
                "python": platform.python_version(),
                "lightgbm": lgb.__version__,
                "numpy": np.__version__,
                "pandas": pd.__version__,
            },
            "created_at": datetime.now(UTC).isoformat(),
            "files": {
                "model": {"filename": MODEL_FILENAME, "sha256": sha256_file(model_tmp)},
                "metadata": {"filename": METADATA_FILENAME},
            },
        }
        metadata_tmp.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(model_tmp, root / MODEL_FILENAME)
        os.replace(metadata_tmp, root / METADATA_FILENAME)
    except Exception:
        model_tmp.unlink(missing_ok=True)
        metadata_tmp.unlink(missing_ok=True)
        raise
    return root
