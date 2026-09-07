"""Load-only inference for versioned Favorita LightGBM model bundles."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd

from pipelines.runtime_paths import resolve_cli_path

BUNDLE_SCHEMA_VERSION = 1
MODEL_FILENAME = "model.txt"
METADATA_FILENAME = "metadata.json"
TIME_AWARE_FEATURE_CONTRACT = "time-aware"
REQUIRED_FIELDS = frozenset(
    {
        "bundle_schema_version",
        "model_version",
        "model_type",
        "model_family",
        "model_arm",
        "target",
        "feature_contract_name",
        "fitted_feature_columns",
        "categorical_feature_columns",
        "categorical_levels",
        "excluded_all_null_feature_columns",
        "effective_lightgbm_parameters",
        "num_boost_round",
        "provenance",
        "runtime_versions",
        "created_at",
        "files",
    }
)


class FavoritaBundleError(ValueError):
    """Base error for invalid Favorita bundles."""


class UnsupportedBundleSchemaError(FavoritaBundleError):
    """Raised for unsupported bundle schemas."""


class BundleIntegrityError(FavoritaBundleError):
    """Raised when bundle integrity validation fails."""


class FeatureSchemaError(FavoritaBundleError):
    """Raised when inference features are incompatible."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _string_list(metadata: Mapping[str, Any], field: str) -> tuple[str, ...]:
    value = metadata[field]
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise FavoritaBundleError(f"Bundle field {field!r} must be a string list")
    if len(value) != len(set(value)):
        raise FavoritaBundleError(f"Bundle field {field!r} contains duplicates")
    return tuple(value)


class FavoritaBundlePredictor:
    """Synchronous predictor loaded only from native bundle files."""

    def __init__(
        self, bundle_dir: Path, metadata: Mapping[str, Any], booster: lgb.Booster
    ) -> None:
        self.bundle_dir = bundle_dir
        self.metadata = dict(metadata)
        self._booster = booster
        self.fitted_feature_columns = _string_list(metadata, "fitted_feature_columns")
        self.categorical_feature_columns = _string_list(
            metadata, "categorical_feature_columns"
        )
        levels = metadata["categorical_levels"]
        if not isinstance(levels, dict) or set(levels) != set(
            self.categorical_feature_columns
        ):
            raise FavoritaBundleError(
                "categorical_levels must exactly match categorical features"
            )
        if not all(isinstance(v, list) for v in levels.values()):
            raise FavoritaBundleError(
                "Every categorical feature must have a levels list"
            )
        self._levels = {k: tuple(v) for k, v in levels.items()}

    @classmethod
    def load(cls, bundle_dir: str | Path) -> FavoritaBundlePredictor:
        root = resolve_cli_path(bundle_dir)
        metadata_path, model_path = root / METADATA_FILENAME, root / MODEL_FILENAME
        if not metadata_path.is_file():
            raise FileNotFoundError(f"Bundle metadata not found: {metadata_path}")
        if not model_path.is_file():
            raise FileNotFoundError(f"Bundle model not found: {model_path}")
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise FavoritaBundleError(
                "Bundle metadata is not valid readable JSON"
            ) from exc
        if not isinstance(metadata, dict):
            raise FavoritaBundleError("Bundle metadata must be an object")
        missing = REQUIRED_FIELDS - set(metadata)
        if missing:
            raise FavoritaBundleError(
                "Missing bundle fields: " + ", ".join(sorted(missing))
            )
        version = metadata["bundle_schema_version"]
        if version != BUNDLE_SCHEMA_VERSION:
            raise UnsupportedBundleSchemaError(
                f"Unsupported bundle schema version {version!r}; expected {BUNDLE_SCHEMA_VERSION}"
            )
        expected_identity = {
            "model_family": "lightgbm",
            "model_arm": "time_aware",
            "target": "unit_sales",
            "feature_contract_name": TIME_AWARE_FEATURE_CONTRACT,
        }
        for field, expected_value in expected_identity.items():
            if metadata[field] != expected_value:
                raise FavoritaBundleError(
                    f"Bundle field {field!r} must be {expected_value!r}"
                )
        if (
            not isinstance(metadata["model_version"], str)
            or not metadata["model_version"]
        ):
            raise FavoritaBundleError("Bundle model_version must be a non-empty string")
        if not isinstance(metadata["model_type"], str) or not metadata["model_type"]:
            raise FavoritaBundleError("Bundle model_type must be a non-empty string")
        if (
            not isinstance(metadata["num_boost_round"], int)
            or metadata["num_boost_round"] <= 0
        ):
            raise FavoritaBundleError(
                "Bundle num_boost_round must be a positive integer"
            )
        for object_field in (
            "effective_lightgbm_parameters",
            "provenance",
            "runtime_versions",
        ):
            if not isinstance(metadata[object_field], dict):
                raise FavoritaBundleError(
                    f"Bundle field {object_field!r} must be an object"
                )
        _string_list(metadata, "excluded_all_null_feature_columns")
        files = metadata["files"]
        if (
            not isinstance(files, dict)
            or not isinstance(files.get("model"), dict)
            or files["model"].get("filename") != MODEL_FILENAME
        ):
            raise FavoritaBundleError("Bundle model file metadata is invalid")
        expected = files["model"].get("sha256")
        if not isinstance(expected, str) or sha256_file(model_path) != expected:
            raise BundleIntegrityError("Bundle model checksum mismatch")
        fitted = _string_list(metadata, "fitted_feature_columns")
        booster = lgb.Booster(model_file=str(model_path))
        if tuple(booster.feature_name()) != fitted:
            raise FavoritaBundleError("Native model features do not match metadata")
        return cls(root, metadata, booster)

    def _prepare(self, features: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(features, pd.DataFrame):
            raise TypeError("features must be a pandas DataFrame")
        expected, supplied = self.fitted_feature_columns, tuple(features.columns)
        missing = [v for v in expected if v not in supplied]
        unexpected = [v for v in supplied if v not in expected]
        if missing or unexpected:
            parts = (["missing=" + ",".join(missing)] if missing else []) + (
                ["unexpected=" + ",".join(unexpected)] if unexpected else []
            )
            raise FeatureSchemaError("Incompatible feature schema: " + "; ".join(parts))
        frame = features.loc[:, expected].copy()
        categorical = set(self.categorical_feature_columns)
        for column in expected:
            if column in categorical:
                values, levels = frame[column], self._levels[column]
                frame[column] = pd.Categorical(
                    values.where(values.isna() | values.isin(levels)), categories=levels
                ).codes.astype("float64")
            else:
                try:
                    frame[column] = pd.to_numeric(frame[column], errors="raise")
                except (TypeError, ValueError) as exc:
                    raise FeatureSchemaError(
                        f"Feature {column!r} is not numeric"
                    ) from exc
                if pd.api.types.is_bool_dtype(frame[column].dtype):
                    frame[column] = frame[column].astype("float64")
        return frame

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        values = np.asarray(
            self._booster.predict(self._prepare(features)), dtype="float64"
        )
        if len(values) != len(features) or not np.isfinite(values).all():
            raise FavoritaBundleError("LightGBM returned invalid predictions")
        return values
