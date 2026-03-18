from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler



# Optional external boosters
try:
    from xgboost import XGBRegressor

    XGBOOST_AVAILABLE = True
except ImportError:
    XGBRegressor = None
    XGBOOST_AVAILABLE = False

try:
    from lightgbm import LGBMRegressor

    LIGHTGBM_AVAILABLE = True
except ImportError:
    LGBMRegressor = None
    LIGHTGBM_AVAILABLE = False


import logging
from app.core.logging import get_logger, setup_logging

# =========================================================
# Logging
# =========================================================

logger = get_logger(__name__)

"""This module implements the training pipeline for the demand forecasting model. 
It includes data loading, validation, feature preparation, model training, evaluation, and artifact saving. 
The pipeline is designed to be modular and extensible for future enhancements.

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
"""

# =========================================================
# Configuration
# =========================================================
@dataclass(frozen=True)
class TrainingConfig:
    feature_input_path: Path = (
        Path("data") / "processed" / "features" / "demand_features.parquet"
    )
    model_output_dir: Path = Path("artifacts") / "models"
    report_output_dir: Path = Path("artifacts") / "reports"

    target_column: str = "target_units_sold_t_plus_1"
    date_column: str = "date"

    drop_columns: Tuple[str, ...] = (
        "date",
        "promotion_id",
        "store_id",
        "warehouse_id",
    )

    validation_days: int = 14
    minimum_train_rows: int = 200
    random_state: int = 42
    clip_negative_predictions_to_zero: bool = True
    model_version: str = "v1.1.0"

    enable_xgboost: bool = True
    enable_lightgbm: bool = True


# =========================================================
# Result model
# =========================================================
@dataclass
class ModelResult:
    model_name: str
    mae: float
    rmse: float
    mape: float
    wape: float
    train_rows: int
    valid_rows: int
    feature_count: int
    selected: bool = False


# =========================================================
# Data loading / validation
# =========================================================
def load_feature_dataset(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"Feature dataset not found: {input_path}")

    logger.info("Loading feature dataset from %s", input_path)
    df = pd.read_parquet(input_path)

    if df.empty:
        raise ValueError("Feature dataset is empty.")

    return df


def validate_training_frame(
    df: pd.DataFrame,
    *,
    target_column: str,
    date_column: str,
) -> pd.DataFrame:
    required_columns = {target_column, date_column}
    missing_columns = sorted(required_columns - set(df.columns))
    if missing_columns:
        raise ValueError(
            f"Training dataset is missing required columns: {missing_columns}"
        )

    output_df = df.copy()
    output_df[date_column] = pd.to_datetime(output_df[date_column], errors="coerce")

    if output_df[date_column].isna().any():
        invalid_count = int(output_df[date_column].isna().sum())
        raise ValueError(
            f"Invalid values found in date column '{date_column}'. "
            f"Invalid row count: {invalid_count}"
        )

    output_df[target_column] = pd.to_numeric(output_df[target_column], errors="coerce")
    output_df = output_df.dropna(subset=[target_column]).copy()

    if output_df.empty:
        raise ValueError("All rows were removed after target validation.")

    return output_df


def split_train_validation_by_date(
    df: pd.DataFrame,
    *,
    date_column: str,
    validation_days: int,
    minimum_train_rows: int,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    output_df = df.sort_values(date_column).reset_index(drop=True)

    max_date = output_df[date_column].max()
    validation_start_date = max_date - pd.Timedelta(days=validation_days - 1)

    train_df = output_df.loc[output_df[date_column] < validation_start_date].copy()
    valid_df = output_df.loc[output_df[date_column] >= validation_start_date].copy()

    if train_df.empty or valid_df.empty:
        raise ValueError(
            "Train/validation split failed. Check date coverage and validation window."
        )

    if len(train_df) < minimum_train_rows:
        raise ValueError(
            f"Training rows are too small: {len(train_df)} < {minimum_train_rows}"
        )

    logger.info(
        "Split complete | train_rows=%s | valid_rows=%s | validation_start=%s",
        len(train_df),
        len(valid_df),
        validation_start_date.date(),
    )

    return train_df, valid_df


# =========================================================
# Feature preparation
# =========================================================
def build_feature_lists(
    df: pd.DataFrame,
    *,
    target_column: str,
    drop_columns: Tuple[str, ...],
) -> Tuple[List[str], List[str], List[str]]:
    excluded_columns = set(drop_columns) | {target_column}

    feature_columns = [
        column
        for column in df.columns
        if column not in excluded_columns
    ]

    if not feature_columns:
        raise ValueError("No feature columns available after exclusions.")

    numeric_columns: List[str] = []
    categorical_columns: List[str] = []

    for column in feature_columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            numeric_columns.append(column)
        else:
            categorical_columns.append(column)

    logger.info(
        "Feature columns prepared | total=%s | numeric=%s | categorical=%s",
        len(feature_columns),
        len(numeric_columns),
        len(categorical_columns),
    )

    return feature_columns, numeric_columns, categorical_columns


def build_preprocessor(
    *,
    numeric_columns: List[str],
    categorical_columns: List[str],
) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_columns),
            ("categorical", categorical_pipeline, categorical_columns),
        ],
        remainder="drop",
    )


# =========================================================
# Candidate models
# =========================================================
def build_candidate_models(
    preprocessor: ColumnTransformer,
    *,
    config: TrainingConfig,
) -> Dict[str, Pipeline]:
    models: Dict[str, Pipeline] = {
        "ridge_regression": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    TransformedTargetRegressor(
                        regressor=Ridge(alpha=1.0),
                        func=np.log1p,
                        inverse_func=np.expm1,
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    TransformedTargetRegressor(
                        regressor=RandomForestRegressor(
                            n_estimators=250,
                            max_depth=16,
                            min_samples_leaf=3,
                            random_state=config.random_state,
                            n_jobs=-1,
                        ),
                        func=np.log1p,
                        inverse_func=np.expm1,
                    ),
                ),
            ]
        ),
        "hist_gradient_boosting": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    TransformedTargetRegressor(
                        regressor=HistGradientBoostingRegressor(
                            learning_rate=0.05,
                            max_depth=10,
                            max_iter=250,
                            min_samples_leaf=20,
                            random_state=config.random_state,
                        ),
                        func=np.log1p,
                        inverse_func=np.expm1,
                    ),
                ),
            ]
        ),
    }

    if config.enable_xgboost and XGBOOST_AVAILABLE:
        models["xgboost"] = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    TransformedTargetRegressor(
                        regressor=XGBRegressor(
                            n_estimators=400,
                            learning_rate=0.05,
                            max_depth=8,
                            min_child_weight=3,
                            subsample=0.8,
                            colsample_bytree=0.8,
                            objective="reg:squarederror",
                            random_state=config.random_state,
                            n_jobs=-1,
                        ),
                        func=np.log1p,
                        inverse_func=np.expm1,
                    ),
                ),
            ]
        )
    elif config.enable_xgboost:
        logger.warning("XGBoost is enabled in config, but package is not installed.")

    if config.enable_lightgbm and LIGHTGBM_AVAILABLE:
        models["lightgbm"] = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    TransformedTargetRegressor(
                        regressor=LGBMRegressor(
                            n_estimators=400,
                            learning_rate=0.05,
                            num_leaves=64,
                            max_depth=-1,
                            min_child_samples=20,
                            subsample=0.8,
                            colsample_bytree=0.8,
                            random_state=config.random_state,
                            n_jobs=-1,
                            verbose=-1,
                        ),
                        func=np.log1p,
                        inverse_func=np.expm1,
                    ),
                ),
            ]
        )
    elif config.enable_lightgbm:
        logger.warning("LightGBM is enabled in config, but package is not installed.")

    logger.info("Candidate models: %s", list(models.keys()))
    return models


# =========================================================
# Metrics
# =========================================================
def calculate_forecast_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict[str, float]:
    epsilon = 1e-9

    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))

    non_zero_mask = np.abs(y_true) > epsilon
    if non_zero_mask.any():
        mape = float(
            np.mean(
                np.abs(
                    (y_true[non_zero_mask] - y_pred[non_zero_mask])
                    / y_true[non_zero_mask]
                )
            )
            * 100.0
        )
    else:
        mape = 0.0

    denominator = float(np.sum(np.abs(y_true)))
    if denominator > epsilon:
        wape = float(np.sum(np.abs(y_true - y_pred)) / denominator * 100.0)
    else:
        wape = 0.0

    return {
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "wape": wape,
    }


# =========================================================
# Training / selection
# =========================================================
def fit_and_evaluate_models(
    *,
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    target_column: str,
    feature_columns: List[str],
    models: Dict[str, Pipeline],
    clip_negative_predictions_to_zero: bool,
) -> Tuple[Pipeline, List[ModelResult], str]:
    x_train = train_df[feature_columns]
    y_train = train_df[target_column].to_numpy(dtype=float)

    x_valid = valid_df[feature_columns]
    y_valid = valid_df[target_column].to_numpy(dtype=float)

    results: List[ModelResult] = []
    fitted_models: Dict[str, Pipeline] = {}

    for model_name, model_pipeline in models.items():
        logger.info("Training model: %s", model_name)

        model_pipeline.fit(x_train, y_train)
        predictions = model_pipeline.predict(x_valid)

        if clip_negative_predictions_to_zero:
            predictions = np.clip(predictions, a_min=0.0, a_max=None)

        metrics = calculate_forecast_metrics(y_valid, predictions)

        result = ModelResult(
            model_name=model_name,
            mae=metrics["mae"],
            rmse=metrics["rmse"],
            mape=metrics["mape"],
            wape=metrics["wape"],
            train_rows=len(train_df),
            valid_rows=len(valid_df),
            feature_count=len(feature_columns),
        )
        results.append(result)
        fitted_models[model_name] = model_pipeline

        logger.info(
            "Model complete | %s | MAE=%.4f | RMSE=%.4f | MAPE=%.4f | WAPE=%.4f",
            model_name,
            result.mae,
            result.rmse,
            result.mape,
            result.wape,
        )

    sorted_results = sorted(
        results,
        key=lambda item: (item.mae, item.rmse, item.wape),
    )

    best_result = sorted_results[0]
    best_result.selected = True
    best_model_name = best_result.model_name
    best_model = fitted_models[best_model_name]

    logger.info("Selected best model: %s", best_model_name)

    return best_model, results, best_model_name


# =========================================================
# Artifact saving
# =========================================================
def save_model_artifacts(
    *,
    best_model: Pipeline,
    model_name: str,
    config: TrainingConfig,
    feature_columns: List[str],
    numeric_columns: List[str],
    categorical_columns: List[str],
    results: List[ModelResult],
) -> None:
    config.model_output_dir.mkdir(parents=True, exist_ok=True)
    config.report_output_dir.mkdir(parents=True, exist_ok=True)

    model_path = config.model_output_dir / "demand_forecast_model.joblib"
    manifest_path = config.model_output_dir / "model_manifest.json"
    feature_schema_path = config.model_output_dir / "feature_schema.json"
    evaluation_report_path = config.report_output_dir / "model_evaluation_report.json"
    comparison_csv_path = config.report_output_dir / "model_comparison.csv"

    joblib.dump(best_model, model_path)

    manifest = {
        "model_name": model_name,
        "model_version": config.model_version,
        "artifact_type": "demand_forecast_regressor",
        "target_column": config.target_column,
        "feature_count": len(feature_columns),
        "feature_artifact_path": str(feature_schema_path),
        "model_artifact_path": str(model_path),
        "xgboost_available": XGBOOST_AVAILABLE,
        "lightgbm_available": LIGHTGBM_AVAILABLE,
    }

    feature_schema = {
        "all_feature_columns": feature_columns,
        "numeric_feature_columns": numeric_columns,
        "categorical_feature_columns": categorical_columns,
        "target_column": config.target_column,
    }

    report_payload = {
        "selected_model_name": model_name,
        "model_version": config.model_version,
        "selection_rule": [
            "lowest MAE",
            "then lowest RMSE",
            "then lowest WAPE",
        ],
        "results": [asdict(item) for item in results],
    }

    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)

    with feature_schema_path.open("w", encoding="utf-8") as file:
        json.dump(feature_schema, file, indent=2)

    with evaluation_report_path.open("w", encoding="utf-8") as file:
        json.dump(report_payload, file, indent=2)

    comparison_df = pd.DataFrame([asdict(item) for item in results]).sort_values(
        by=["selected", "mae", "rmse", "wape"],
        ascending=[False, True, True, True],
    )
    comparison_df.to_csv(comparison_csv_path, index=False)

    logger.info("Saved model artifact to %s", model_path)
    logger.info("Saved manifest to %s", manifest_path)
    logger.info("Saved feature schema to %s", feature_schema_path)
    logger.info("Saved evaluation report to %s", evaluation_report_path)
    logger.info("Saved comparison CSV to %s", comparison_csv_path)


# =========================================================
# Main flow
# =========================================================
def run_training(config: TrainingConfig | None = None) -> str:
    cfg = config or TrainingConfig()

    df = load_feature_dataset(cfg.feature_input_path)
    df = validate_training_frame(
        df,
        target_column=cfg.target_column,
        date_column=cfg.date_column,
    )

    logger.info("Feature dataset total rows before split: %s", len(df))
    logger.info("Feature dataset min date: %s", df[cfg.date_column].min())
    logger.info("Feature dataset max date: %s", df[cfg.date_column].max())
 
    train_df, valid_df = split_train_validation_by_date(
        df,
        date_column=cfg.date_column,
        validation_days=cfg.validation_days,
        minimum_train_rows=cfg.minimum_train_rows,
    )

    feature_columns, numeric_columns, categorical_columns = build_feature_lists(
        df=train_df,
        target_column=cfg.target_column,
        drop_columns=cfg.drop_columns,
    )

    preprocessor = build_preprocessor(
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
    )

    models = build_candidate_models(
        preprocessor=preprocessor,
        config=cfg,
    )

    best_model, results, best_model_name = fit_and_evaluate_models(
        train_df=train_df,
        valid_df=valid_df,
        target_column=cfg.target_column,
        feature_columns=feature_columns,
        models=models,
        clip_negative_predictions_to_zero=cfg.clip_negative_predictions_to_zero,
    )

    save_model_artifacts(
        best_model=best_model,
        model_name=best_model_name,
        config=cfg,
        feature_columns=feature_columns,
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        results=results,
    )

    return best_model_name # Return the name of the selected model


if __name__ == "__main__":
    setup_logging(level="INFO")
    selected_model = run_training() 
    logger.info(
        "Training pipeline completed successfully. Selected model: %s",
        selected_model,                                               
    )
        
         #  logger.info("Training pipeline completed successfully. Selected model: %s", selected_model,) 
                    #  = logger.info(f"Training pipeline completed successfully. Selected model: {selected_model}") 