from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


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
REPORTS_DIR = ARTIFACTS_DIR / "reports"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_FEATURES_DIR = PROCESSED_DIR / "features"

MANIFEST_PATH = MODELS_DIR / "model_manifest.json"
FEATURE_SCHEMA_PATH = MODELS_DIR / "feature_schema.json"

DEFAULT_MODEL_CANDIDATES = [
    MODELS_DIR / "best_model.joblib",
    MODELS_DIR / "best_model.pkl",
    MODELS_DIR / "demand_forecast_model.joblib",
    MODELS_DIR / "demand_forecast_model.pkl",
]

DEFAULT_VALIDATION_CANDIDATES = [
    PROCESSED_FEATURES_DIR / "valid_features.parquet",
    PROCESSED_FEATURES_DIR / "validation_features.parquet",
    PROCESSED_FEATURES_DIR / "forecast_valid_features.parquet",
    PROCESSED_FEATURES_DIR / "demand_features.parquet",
    PROCESSED_FEATURES_DIR / "valid_features.csv",
    PROCESSED_FEATURES_DIR / "validation_features.csv",
    PROCESSED_FEATURES_DIR / "forecast_valid_features.csv",
    PROCESSED_FEATURES_DIR / "demand_features.csv",
    PROCESSED_DIR / "valid_features.parquet",
    PROCESSED_DIR / "validation_features.parquet",
    PROCESSED_DIR / "forecast_valid_features.parquet",
    PROCESSED_DIR / "training_dataset.parquet",
    PROCESSED_DIR / "train_valid_dataset.parquet",
    PROCESSED_DIR / "valid_features.csv",
    PROCESSED_DIR / "validation_features.csv",
    PROCESSED_DIR / "forecast_valid_features.csv",
    PROCESSED_DIR / "training_dataset.csv",
    PROCESSED_DIR / "train_valid_dataset.csv",
]

TARGET_COLUMN_CANDIDATES = [
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
]

REPORT_JSON_PATH = REPORTS_DIR / "demand_forecast_evaluation_report.json"
PREDICTIONS_CSV_PATH = REPORTS_DIR / "demand_forecast_validation_predictions.csv"
ERROR_SUMMARY_CSV_PATH = REPORTS_DIR / "demand_forecast_error_summary.csv"


# =========================================================
# Dataclasses
# =========================================================
@dataclass
class EvaluationPaths:
    model_path: Path
    validation_path: Path
    report_json_path: Path
    predictions_csv_path: Path
    error_summary_csv_path: Path


@dataclass
class LoadedArtifacts:
    model: Any
    model_path: Path
    manifest: Dict[str, Any]
    feature_schema: Dict[str, Any]


# =========================================================
# Path / file helpers
# =========================================================
def ensure_output_dirs() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
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


def discover_model_path(manifest: Dict[str, Any]) -> Path:
    manifest_candidates: List[str] = []

    if manifest:
        for key in [
            "best_model_path",
            "model_path",
            "artifact_path",
            "selected_model_path",
        ]:
            value = manifest.get(key)
            if isinstance(value, str) and value.strip():
                manifest_candidates.append(value.strip())

        selected_model = manifest.get("selected_model")
        if isinstance(selected_model, dict):
            for key in ["model_path", "artifact_path"]:
                value = selected_model.get(key)
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


def discover_validation_path() -> Path:
    for candidate in DEFAULT_VALIDATION_CANDIDATES:
        if candidate.exists():
            logger.info("Validation dataset found: %s", candidate)
            return candidate

    raise FileNotFoundError(
        "No validation dataset found in data/processed/. "
        "Expected one of: "
        + ", ".join(path.name for path in DEFAULT_VALIDATION_CANDIDATES)
    )


def build_paths(manifest: Dict[str, Any]) -> EvaluationPaths:
    return EvaluationPaths(
        model_path=discover_model_path(manifest),
        validation_path=discover_validation_path(),
        report_json_path=REPORT_JSON_PATH,
        predictions_csv_path=PREDICTIONS_CSV_PATH,
        error_summary_csv_path=ERROR_SUMMARY_CSV_PATH,
    )


# =========================================================
# Loading
# =========================================================
def load_dataframe(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()

    if suffix == ".parquet":
        return pd.read_parquet(path)

    if suffix == ".csv":
        return pd.read_csv(path)

    raise ValueError(f"Unsupported validation dataset format: {path}")


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
# Schema / feature helpers
# =========================================================
def detect_target_column(
    df: pd.DataFrame,
    manifest: Dict[str, Any],
    feature_schema: Dict[str, Any],
) -> str:
    for source in [feature_schema, manifest]:
        for key in ["target_column", "label_column", "target"]:
            value = source.get(key)
            if isinstance(value, str) and value in df.columns:
                return value

    for candidate in TARGET_COLUMN_CANDIDATES:
        if candidate in df.columns:
            return candidate

    raise ValueError(
        "Could not determine target column. "
        f"Tried manifest/schema and defaults: {TARGET_COLUMN_CANDIDATES}"
    )

def detect_feature_columns(
    df: pd.DataFrame,
    target_column: str,
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
            columns = [str(col) for col in value]
            return columns

    numeric_cols = feature_schema.get("numeric_feature_columns")
    categorical_cols = feature_schema.get("categorical_feature_columns")
    if isinstance(numeric_cols, list) and isinstance(categorical_cols, list):
        return [str(col) for col in numeric_cols + categorical_cols]

    excluded = {
        target_column,
        "split",
        "dataset_split",
        "row_type",
    }

    candidate_columns = [col for col in df.columns if col not in excluded]

    if not candidate_columns:
        raise ValueError("No usable feature columns found in validation dataset.")

    return candidate_columns

def apply_validation_split_filter(df: pd.DataFrame) -> pd.DataFrame:
    working_df = df.copy()

    for split_col in ["split", "dataset_split", "row_type"]:
        if split_col in working_df.columns:
            normalized = (
                working_df[split_col]
                .astype(str)
                .str.strip()
                .str.lower()
            )
            valid_mask = normalized.isin(["valid", "validation", "val"])

            if valid_mask.any():
                logger.info(
                    "Filtered validation dataset using column '%s': %s rows retained.",
                    split_col,
                    int(valid_mask.sum()),
                )
                return working_df.loc[valid_mask].reset_index(drop=True)

    return working_df.reset_index(drop=True)


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
# Evaluation metrics
# =========================================================
def safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> Optional[float]:
    denominator = np.where(np.abs(y_true) < 1e-9, np.nan, np.abs(y_true))
    ratio = np.abs((y_true - y_pred) / denominator)
    value = np.nanmean(ratio) * 100
    return None if np.isnan(value) else float(value)


def safe_smape(y_true: np.ndarray, y_pred: np.ndarray) -> Optional[float]:
    denominator = np.abs(y_true) + np.abs(y_pred)
    denominator = np.where(denominator < 1e-9, np.nan, denominator)
    ratio = (2.0 * np.abs(y_pred - y_true)) / denominator
    value = np.nanmean(ratio) * 100
    return None if np.isnan(value) else float(value)


def build_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Optional[float]]:
    metrics: Dict[str, Optional[float]] = {
        "row_count": int(len(y_true)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mape_pct": safe_mape(y_true, y_pred),
        "smape_pct": safe_smape(y_true, y_pred),
        "mean_actual": float(np.mean(y_true)),
        "mean_predicted": float(np.mean(y_pred)),
        "total_actual": float(np.sum(y_true)),
        "total_predicted": float(np.sum(y_pred)),
        "bias_mean_error": float(np.mean(y_pred - y_true)),
    }

    if len(y_true) >= 2:
        metrics["r2"] = float(r2_score(y_true, y_pred))
    else:
        metrics["r2"] = None

    return metrics


def build_prediction_frame(
    source_df: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    target_column: str,
) -> pd.DataFrame:
    prediction_df = pd.DataFrame({
        "actual": y_true,
        "predicted": y_pred,
    })
    prediction_df["error"] = prediction_df["predicted"] - prediction_df["actual"]
    prediction_df["absolute_error"] = np.abs(prediction_df["error"])
    prediction_df["squared_error"] = np.square(prediction_df["error"])

    for col in DATE_COLUMN_CANDIDATES + ID_COLUMN_CANDIDATES:
        if col in source_df.columns:
            prediction_df[col] = source_df[col].values

    prediction_df["target_column"] = target_column
    return prediction_df


def build_error_summary(
    prediction_df: pd.DataFrame,
) -> pd.DataFrame:
    summary_rows: List[Dict[str, Any]] = []

    for grouping_col in ["region_id", "store_id", "warehouse_id", "product_id"]:
        if grouping_col not in prediction_df.columns:
            continue

        grouped = (
            prediction_df.groupby(grouping_col, dropna=False)
            .agg(
                row_count=("actual", "size"),
                actual_mean=("actual", "mean"),
                predicted_mean=("predicted", "mean"),
                mae=("absolute_error", "mean"),
                rmse=("squared_error", lambda s: float(np.sqrt(np.mean(s)))),
                total_actual=("actual", "sum"),
                total_predicted=("predicted", "sum"),
            )
            .reset_index()
        )
        grouped.insert(0, "summary_level", grouping_col)
        summary_rows.append(grouped)

    if not summary_rows:
        return pd.DataFrame(
            columns=[
                "summary_level",
                "group_value",
                "row_count",
                "actual_mean",
                "predicted_mean",
                "mae",
                "rmse",
                "total_actual",
                "total_predicted",
            ]
        )

    final_df = pd.concat(summary_rows, ignore_index=True)

    value_col = final_df.columns[1]
    if value_col != "group_value":
        final_df = final_df.rename(columns={value_col: "group_value"})

    return final_df


# =========================================================
# Save outputs
# =========================================================
def sanitize_for_json(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def save_json_report(payload: Dict[str, Any], path: Path) -> None:
    serializable = {
        key: sanitize_for_json(value)
        for key, value in payload.items()
    }
    with path.open("w", encoding="utf-8") as file:
        json.dump(serializable, file, indent=2, ensure_ascii=False)


# =========================================================
# Main evaluation flow
# =========================================================
def evaluate_model() -> Dict[str, Any]:
    ensure_output_dirs()

    loaded = load_model_artifacts()
    paths = build_paths(loaded.manifest)

    df = load_dataframe(paths.validation_path)
    df = apply_validation_split_filter(df)

    if df.empty:
        raise ValueError("Validation dataset is empty after filtering.")

    target_column = detect_target_column(df, loaded.manifest, loaded.feature_schema)
    feature_columns = detect_feature_columns(
        df=df,
        target_column=target_column,
        manifest=loaded.manifest,
        feature_schema=loaded.feature_schema,
    )

    missing_features = [col for col in feature_columns if col not in df.columns]
    if missing_features:
        raise ValueError(f"Validation dataset is missing feature columns: {missing_features}")

    df = df.copy()

    df[target_column] = pd.to_numeric(df[target_column], errors="coerce")
    df = df.loc[df[target_column].notna()].reset_index(drop=True)

    if df.empty:
        raise ValueError("Validation dataset became empty after dropping NaN target rows.")

    x_valid = coerce_features_for_model(df[feature_columns])
    y_valid = df[target_column].astype(float).to_numpy()

    logger.info("Validation rows: %s", len(df))
    logger.info("Feature count used for evaluation: %s", len(feature_columns))
    logger.info("Model artifact: %s", loaded.model_path.name)

    expected_columns = list(x_valid.columns)
    logger.info("Evaluation feature columns: %s", expected_columns)

    missing_in_df = [col for col in feature_columns if col not in df.columns]
    if missing_in_df:
        raise ValueError(
        f"Validation dataset is missing required feature columns: {missing_in_df}"
    )

    try:
        y_pred = loaded.model.predict(x_valid)
    except Exception as exc:
        logger.exception("Model prediction failed during evaluation.")
        raise RuntimeError("Model prediction failed during evaluation.") from exc

    y_pred = np.asarray(y_pred, dtype=float)
    valid_mask = np.isfinite(y_valid) & np.isfinite(y_pred)

    if not valid_mask.all():
        logger.warning(
            "Dropping %s rows due to non-finite values in y_true or y_pred.",
            int((~valid_mask).sum()),
        )

    y_valid = y_valid[valid_mask]
    y_pred = y_pred[valid_mask]
    df = df.loc[valid_mask].reset_index(drop=True)

    if len(y_valid) == 0:
        raise ValueError("No valid rows remain after removing NaN/inf values from evaluation.")

    metrics = build_metrics(y_valid, y_pred)

    prediction_df = build_prediction_frame(
        source_df=df,
        y_true=y_valid,
        y_pred=y_pred,
        target_column=target_column,
    )
    error_summary_df = build_error_summary(prediction_df)

    prediction_df.to_csv(paths.predictions_csv_path, index=False)
    error_summary_df.to_csv(paths.error_summary_csv_path, index=False)

    best_model_name = (
        loaded.manifest.get("best_model_name")
        or loaded.manifest.get("selected_model_name")
        or loaded.model.__class__.__name__
    )

    report_payload: Dict[str, Any] = {
        "project": "EDIP",
        "company_name": "NorthStar Retail & Distribution",
        "use_case": "SKU-location demand forecasting",
        "evaluation_dataset_path": str(paths.validation_path.relative_to(PROJECT_ROOT)),
        "model_artifact_path": str(paths.model_path.relative_to(PROJECT_ROOT)),
        "best_model_name": str(best_model_name),
        "model_class": loaded.model.__class__.__name__,
        "target_column": target_column,
        "feature_count": len(feature_columns),
        "feature_columns": feature_columns,
        "metrics": metrics,
        "artifacts": {
            "predictions_csv": str(paths.predictions_csv_path.relative_to(PROJECT_ROOT)),
            "error_summary_csv": str(paths.error_summary_csv_path.relative_to(PROJECT_ROOT)),
        },
        "warnings": [],
    }

    if metrics["row_count"] < 10:
        report_payload["warnings"].append(
            "Validation row count is very small. Treat metrics as unstable."
        )

    if metrics["row_count"] < 2:
        report_payload["warnings"].append(
            "R2 is not meaningful because validation row count is below 2."
        )

    save_json_report(report_payload, paths.report_json_path)

    logger.info("Evaluation report saved: %s", paths.report_json_path)
    logger.info("Validation predictions saved: %s", paths.predictions_csv_path)
    logger.info("Error summary saved: %s", paths.error_summary_csv_path)
    logger.info("MAE: %.4f | RMSE: %.4f | R2: %s",
        metrics["mae"],
        metrics["rmse"],
        "n/a" if metrics["r2"] is None else f"{metrics['r2']:.4f}",
    )

    return report_payload


def main() -> None:
    setup_logging()

    try:
        report = evaluate_model()
        logger.info(
            "Demand forecast evaluation completed successfully. Best model: %s",
            report["best_model_name"],
        )
    except Exception as exc:
        logger.exception("Demand forecast evaluation failed.")
        raise
    finally:
        logger.info("evaluate_demand_forecast.py finished.")


if __name__ == "__main__":
    main()