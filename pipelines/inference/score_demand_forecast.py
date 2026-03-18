from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd


# =========================================================
# Logging
# =========================================================
logger = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


# =========================================================
# Constants
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
MODELS_DIR = ARTIFACTS_DIR / "models"
FORECASTS_DIR = ARTIFACTS_DIR / "forecasts"
REPORTS_DIR = ARTIFACTS_DIR / "reports"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_FEATURES_DIR = PROCESSED_DIR / "features"

MANIFEST_PATH = MODELS_DIR / "model_manifest.json"
FEATURE_SCHEMA_PATH = MODELS_DIR / "feature_schema.json"

DEFAULT_MODEL_CANDIDATES = [
    MODELS_DIR / "best_model.joblib",
    MODELS_DIR / "demand_forecast_model.joblib",
    MODELS_DIR / "best_model.pkl",
    MODELS_DIR / "demand_forecast_model.pkl",
]

DEFAULT_SCORING_CANDIDATES = [
    PROCESSED_FEATURES_DIR / "inference_features.parquet",
    PROCESSED_FEATURES_DIR / "scoring_features.parquet",
    PROCESSED_FEATURES_DIR / "forecast_inference_features.parquet",
    PROCESSED_FEATURES_DIR / "demand_features.parquet",
    PROCESSED_FEATURES_DIR / "inference_features.csv",
    PROCESSED_FEATURES_DIR / "scoring_features.csv",
    PROCESSED_FEATURES_DIR / "forecast_inference_features.csv",
    PROCESSED_FEATURES_DIR / "demand_features.csv",
    PROCESSED_DIR / "inference_features.parquet",
    PROCESSED_DIR / "scoring_features.parquet",
    PROCESSED_DIR / "forecast_inference_features.parquet",
    PROCESSED_DIR / "inference_features.csv",
    PROCESSED_DIR / "scoring_features.csv",
]

TARGET_COLUMN_CANDIDATES = [
    "target_units_sold_t_plus_1",
    "target_demand",
    "target_units",
    "demand_units_target",
    "y",
    "target",
]

DATE_COLUMN_CANDIDATES = [
    "date",
    "target_date",
    "forecast_date",
    "ds",
]

ID_COLUMN_CANDIDATES = [
    "product_id",
    "store_id",
    "warehouse_id",
    "region_id",
    "channel_id",
    "location_id",
]

FORECAST_OUTPUT_PATH = FORECASTS_DIR / "demand_forecast_scored.csv"
FORECAST_SUMMARY_PATH = FORECASTS_DIR / "demand_forecast_scoring_summary.json"


# =========================================================
# Dataclasses
# =========================================================
@dataclass
class ScoringPaths:
    model_path: Path
    scoring_data_path: Path
    forecast_output_path: Path
    forecast_summary_path: Path


@dataclass
class LoadedArtifacts:
    model: Any
    model_path: Path
    manifest: Dict[str, Any]
    feature_schema: Dict[str, Any]


# =========================================================
# Helpers
# =========================================================
def ensure_output_dirs() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    FORECASTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_json_if_exists(path: Path) -> Dict[str, Any]:
    if not path.exists():
        logger.warning("JSON file not found: %s", path)
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
            return payload if isinstance(payload, dict) else {}
    except Exception as exc:
        logger.warning("Failed to read JSON file %s: %s", path, exc)
        return {}


def load_dataframe(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()

    if suffix == ".parquet":
        return pd.read_parquet(path)

    if suffix == ".csv":
        return pd.read_csv(path)

    raise ValueError(f"Unsupported data format: {path}")


def discover_model_path(manifest: Dict[str, Any]) -> Path:
    manifest_candidates: List[str] = []

    if manifest:
        for key in [
            "best_model_path",
            "model_path",
            "artifact_path",
            "selected_model_path",
            "model_artifact_path",
        ]:
            value = manifest.get(key)
            if isinstance(value, str) and value.strip():
                manifest_candidates.append(value.strip())

    for candidate in manifest_candidates:
        candidate_path = Path(candidate)
        if not candidate_path.is_absolute():
            candidate_path = PROJECT_ROOT / candidate_path

        if candidate_path.exists():
            logger.info("Model path discovered from manifest: %s", candidate_path)
            return candidate_path

    for candidate in DEFAULT_MODEL_CANDIDATES:
        if candidate.exists():
            logger.info("Model path discovered from default candidates: %s", candidate)
            return candidate

    dynamic_candidates = sorted(
        list(MODELS_DIR.glob("*.joblib")) + list(MODELS_DIR.glob("*.pkl")),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if dynamic_candidates:
        logger.info("Model path discovered from latest artifact: %s", dynamic_candidates[0])
        return dynamic_candidates[0]

    raise FileNotFoundError(
        "No trained model artifact was found in artifacts/models/. "
        "Run train_demand_forecast.py first."
    )


def discover_scoring_data_path() -> Path:
    for candidate in DEFAULT_SCORING_CANDIDATES:
        if candidate.exists():
            logger.info("Scoring dataset found: %s", candidate)
            return candidate

    raise FileNotFoundError(
        "No scoring dataset found. Expected one of: "
        + ", ".join(path.name for path in DEFAULT_SCORING_CANDIDATES)
    )


def build_paths(manifest: Dict[str, Any]) -> ScoringPaths:
    return ScoringPaths(
        model_path=discover_model_path(manifest),
        scoring_data_path=discover_scoring_data_path(),
        forecast_output_path=FORECAST_OUTPUT_PATH,
        forecast_summary_path=FORECAST_SUMMARY_PATH,
    )


def load_model_artifacts() -> LoadedArtifacts:
    manifest = load_json_if_exists(MANIFEST_PATH)
    feature_schema = load_json_if_exists(FEATURE_SCHEMA_PATH)
    paths = build_paths(manifest)

    try:
        model = joblib.load(paths.model_path)
    except Exception as exc:
        logger.exception("Failed to load model artifact from %s", paths.model_path)
        raise RuntimeError("Failed to load trained model artifact.") from exc

    return LoadedArtifacts(
        model=model,
        model_path=paths.model_path,
        manifest=manifest,
        feature_schema=feature_schema,
    )


# =========================================================
# Feature schema helpers
# =========================================================
def detect_target_column(
    df: pd.DataFrame,
    manifest: Dict[str, Any],
    feature_schema: Dict[str, Any],
) -> Optional[str]:
    for source in [feature_schema, manifest]:
        for key in ["target_column", "label_column", "target"]:
            value = source.get(key)
            if isinstance(value, str) and value in df.columns:
                return value

    for candidate in TARGET_COLUMN_CANDIDATES:
        if candidate in df.columns:
            return candidate

    return None


def detect_feature_columns(
    df: pd.DataFrame,
    target_column: Optional[str],
    manifest: Dict[str, Any],
    feature_schema: Dict[str, Any],
) -> List[str]:
    schema_candidates = [
        feature_schema.get("all_feature_columns"),
        feature_schema.get("feature_columns"),
        feature_schema.get("features"),
        feature_schema.get("training_features"),
    ]

    for value in schema_candidates:
        if isinstance(value, list) and value:
            return [str(col) for col in value]

    numeric_cols = feature_schema.get("numeric_feature_columns")
    categorical_cols = feature_schema.get("categorical_feature_columns")
    if isinstance(numeric_cols, list) and isinstance(categorical_cols, list):
        return [str(col) for col in numeric_cols + categorical_cols]

    excluded = {"split", "dataset_split", "row_type"}
    if target_column:
        excluded.add(target_column)

    candidate_columns = [col for col in df.columns if col not in excluded]

    if not candidate_columns:
        raise ValueError("No usable feature columns found in scoring dataset.")

    return candidate_columns


def coerce_features_for_model(x_df: pd.DataFrame) -> pd.DataFrame:
    transformed = x_df.copy()

    for col in transformed.columns:
        if pd.api.types.is_bool_dtype(transformed[col]):
            transformed[col] = transformed[col].astype(int)
        elif pd.api.types.is_object_dtype(transformed[col]):
            transformed[col] = transformed[col].fillna("missing")
        elif isinstance(transformed[col].dtype, pd.CategoricalDtype):
            transformed[col] = transformed[col].astype(str).fillna("missing")

    return transformed


# =========================================================
# Scoring dataset selection
# =========================================================
def select_inference_rows(df: pd.DataFrame, target_column: Optional[str]) -> pd.DataFrame:
    working_df = df.copy()

    for split_col in ["split", "dataset_split", "row_type"]:
        if split_col in working_df.columns:
            normalized = working_df[split_col].astype(str).str.strip().str.lower()
            inference_mask = normalized.isin(["score", "scoring", "inference", "predict"])
            if inference_mask.any():
                logger.info(
                    "Selected inference rows using '%s': %s rows retained.",
                    split_col,
                    int(inference_mask.sum()),
                )
                return working_df.loc[inference_mask].reset_index(drop=True)

    if target_column and target_column in working_df.columns:
        target_numeric = pd.to_numeric(working_df[target_column], errors="coerce")
        missing_target_mask = target_numeric.isna()

        if missing_target_mask.any():
            logger.info(
                "Selected inference rows using NaN target column '%s': %s rows retained.",
                target_column,
                int(missing_target_mask.sum()),
            )
            return working_df.loc[missing_target_mask].reset_index(drop=True)

    if "date" in working_df.columns:
        working_df["date"] = pd.to_datetime(working_df["date"], errors="coerce")
        latest_date = working_df["date"].max()
        if pd.notna(latest_date):
            latest_mask = working_df["date"] == latest_date
            logger.info(
                "No explicit inference split found. Using latest date rows: %s rows retained.",
                int(latest_mask.sum()),
            )
            return working_df.loc[latest_mask].reset_index(drop=True)

    logger.warning("No explicit inference rows found. Scoring all available rows.")
    return working_df.reset_index(drop=True)


# =========================================================
# Output builders
# =========================================================
def build_forecast_output(
    source_df: pd.DataFrame,
    predictions: np.ndarray,
    model_name: str,
    model_version: str,
    target_column: Optional[str],
) -> pd.DataFrame:
    output_df = pd.DataFrame(index=source_df.index)

    for col in DATE_COLUMN_CANDIDATES + ID_COLUMN_CANDIDATES:
        if col in source_df.columns:
            output_df[col] = source_df[col].values

    if "date" in source_df.columns:
        parsed_dates = pd.to_datetime(source_df["date"], errors="coerce")
        output_df["forecast_date"] = parsed_dates.dt.strftime("%Y-%m-%d")
        output_df["target_date"] = (parsed_dates + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")

    output_df["predicted_units"] = np.round(predictions.astype(float), 4)
    output_df["model_name"] = model_name
    output_df["model_version"] = model_version
    output_df["scored_at"] = pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if target_column and target_column in source_df.columns:
        actual_values = pd.to_numeric(source_df[target_column], errors="coerce")
        output_df["actual_target_if_available"] = actual_values.values

    return output_df.reset_index(drop=True)


def sanitize_for_json(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def save_json_report(payload: Dict[str, Any], path: Path) -> None:
    serializable = {key: sanitize_for_json(value) for key, value in payload.items()}
    with path.open("w", encoding="utf-8") as file:
        json.dump(serializable, file, indent=2, ensure_ascii=False)


# =========================================================
# Main scoring flow
# =========================================================
def score_model() -> Dict[str, Any]:
    ensure_output_dirs()

    loaded = load_model_artifacts()
    paths = build_paths(loaded.manifest)

    df = load_dataframe(paths.scoring_data_path)

    target_column = detect_target_column(df, loaded.manifest, loaded.feature_schema)
    df = select_inference_rows(df, target_column)

    if df.empty:
        raise ValueError("Scoring dataset is empty after inference-row selection.")

    feature_columns = detect_feature_columns(
        df=df,
        target_column=target_column,
        manifest=loaded.manifest,
        feature_schema=loaded.feature_schema,
    )

    missing_features = [col for col in feature_columns if col not in df.columns]
    if missing_features:
        raise ValueError(f"Scoring dataset is missing required feature columns: {missing_features}")

    x_score = coerce_features_for_model(df[feature_columns])

    logger.info("Scoring rows: %s", len(df))
    logger.info("Feature count used for scoring: %s", len(feature_columns))
    logger.info("Model artifact: %s", loaded.model_path.name)

    try:
        predictions = loaded.model.predict(x_score)
    except Exception as exc:
        logger.exception("Model prediction failed during scoring.")
        raise RuntimeError("Model prediction failed during scoring.") from exc

    predictions = np.asarray(predictions, dtype=float)
    finite_mask = np.isfinite(predictions)

    if not finite_mask.all():
        logger.warning(
            "Dropping %s rows due to non-finite predictions.",
            int((~finite_mask).sum()),
        )
        df = df.loc[finite_mask].reset_index(drop=True)
        predictions = predictions[finite_mask]

    if len(predictions) == 0:
        raise ValueError("No valid prediction rows remain after filtering non-finite values.")

    model_name = str(
        loaded.manifest.get("model_name")
        or loaded.manifest.get("best_model_name")
        or loaded.manifest.get("selected_model_name")
        or loaded.model.__class__.__name__
    )
    model_version = str(loaded.manifest.get("model_version", "unknown"))

    forecast_output_df = build_forecast_output(
        source_df=df,
        predictions=predictions,
        model_name=model_name,
        model_version=model_version,
        target_column=target_column,
    )
    forecast_output_df.to_csv(paths.forecast_output_path, index=False)

    summary_payload: Dict[str, Any] = {
        "project": "EDIP",
        "company_name": "NorthStar Retail & Distribution",
        "use_case": "SKU-location demand forecasting inference",
        "input_dataset_path": str(paths.scoring_data_path.relative_to(PROJECT_ROOT)),
        "model_artifact_path": str(paths.model_path.relative_to(PROJECT_ROOT)),
        "forecast_output_path": str(paths.forecast_output_path.relative_to(PROJECT_ROOT)),
        "model_name": model_name,
        "model_version": model_version,
        "target_column_if_present": target_column,
        "feature_count": len(feature_columns),
        "row_count_scored": int(len(forecast_output_df)),
        "prediction_summary": {
            "min_predicted_units": float(np.min(predictions)),
            "max_predicted_units": float(np.max(predictions)),
            "mean_predicted_units": float(np.mean(predictions)),
            "total_predicted_units": float(np.sum(predictions)),
        },
        "warnings": [],
    }

    if target_column and target_column in df.columns:
        actual_values = pd.to_numeric(df[target_column], errors="coerce")
        if actual_values.notna().any():
            summary_payload["warnings"].append(
                "Scoring dataset still contains some actual target values."
            )

    save_json_report(summary_payload, paths.forecast_summary_path)

    logger.info("Forecast output saved: %s", paths.forecast_output_path)
    logger.info("Scoring summary saved: %s", paths.forecast_summary_path)
    logger.info(
        "Prediction summary | rows=%s | mean=%.4f | total=%.4f",
        len(forecast_output_df),
        float(np.mean(predictions)),
        float(np.sum(predictions)),
    )

    return summary_payload


def main() -> None:
    setup_logging()

    try:
        summary = score_model()
        logger.info(
            "Demand forecast scoring completed successfully. Model: %s",
            summary["model_name"],
        )
    except Exception:
        logger.exception("Demand forecast scoring failed.")
        raise
    finally:
        logger.info("score_demand_forecast.py finished.")


if __name__ == "__main__":
    main()