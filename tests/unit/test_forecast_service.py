# tests/unit/test_forecast_service.py

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from app.services.forecast_service import (
    ForecastOverview,
    ForecastRecommendationRecord,
    ForecastService,
    ForecastServiceResponse,
    build_overview,
    build_recommendation_records,
    load_csv_if_exists,
    load_json_if_exists,
    normalize_recommendation_df,
    safe_float,
    safe_int,
    safe_str,
)


def test_safe_int_returns_integer_for_valid_value() -> None:
    assert safe_int(10) == 10
    assert safe_int(10.0) == 10


def test_safe_int_returns_none_for_invalid_value() -> None:
    assert safe_int(None) is None
    assert safe_int("abc") is None


def test_safe_float_returns_float_for_valid_value() -> None:
    assert safe_float(10) == 10.0
    assert safe_float("10.5") == 10.5


def test_safe_float_returns_none_for_invalid_value() -> None:
    assert safe_float(None) is None
    assert safe_float("abc") is None


def test_safe_str_returns_trimmed_string() -> None:
    assert safe_str("  hello  ") == "hello"


def test_safe_str_returns_none_for_empty_or_null() -> None:
    assert safe_str(None) is None
    assert safe_str("   ") is None


def test_load_json_if_exists_returns_empty_dict_when_file_missing(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.json"
    result = load_json_if_exists(missing_path)
    assert result == {}


def test_load_json_if_exists_returns_dict_when_file_exists(tmp_path: Path) -> None:
    path = tmp_path / "sample.json"
    payload = {"model_name": "xgboost", "row_count_scored": 100}
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = load_json_if_exists(path)

    assert result == payload


def test_load_json_if_exists_raises_runtime_error_for_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{bad json}", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Failed to read JSON file"):
        load_json_if_exists(path)


def test_load_csv_if_exists_returns_empty_dataframe_when_file_missing(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.csv"
    result = load_csv_if_exists(missing_path)

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_load_csv_if_exists_returns_dataframe_when_file_exists(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    df.to_csv(path, index=False)

    result = load_csv_if_exists(path)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert list(result.columns) == ["a", "b"]


def test_load_csv_if_exists_raises_runtime_error_for_invalid_csv(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text('"unclosed,quote\n1,2', encoding="utf-8")

    with pytest.raises(RuntimeError, match="Failed to read CSV file"):
        load_csv_if_exists(path)


def test_normalize_recommendation_df_converts_numeric_and_dates() -> None:
    df = pd.DataFrame(
        {
            "forecast_date": ["2026-03-18"],
            "target_date": ["2026-03-25"],
            "product_id": ["101"],
            "recommended_order_qty": ["25"],
            "stockout_risk_score": ["0.82"],
        }
    )

    result = normalize_recommendation_df(df)

    assert pd.api.types.is_datetime64_any_dtype(result["forecast_date"])
    assert pd.api.types.is_datetime64_any_dtype(result["target_date"])
    assert pd.api.types.is_numeric_dtype(result["product_id"])
    assert pd.api.types.is_numeric_dtype(result["recommended_order_qty"])
    assert pd.api.types.is_numeric_dtype(result["stockout_risk_score"])


def test_build_overview_returns_expected_dataclass() -> None:
    scoring_summary = {
        "model_name": "random_forest",
        "model_version": "1.0",
        "input_dataset_path": "data/processed/train.parquet",
        "forecast_output_path": "artifacts/forecasts/demand_forecast_scored.csv",
        "row_count_scored": 1000,
        "prediction_summary": {
            "mean_predicted_units": 12.5,
            "total_predicted_units": 12500.0,
        },
        "warnings": ["scoring warning"],
    }

    recommendation_summary = {
        "recommendation_output_path": "artifacts/forecasts/replenishment_recommendations.csv",
        "row_count_total": 250,
        "row_count_actionable": 120,
        "total_recommended_order_qty": 5000,
        "avg_stockout_risk_score": 0.44,
        "warnings": ["recommendation warning"],
    }

    overview = build_overview(scoring_summary, recommendation_summary)

    assert isinstance(overview, ForecastOverview)
    assert overview.model_name == "random_forest"
    assert overview.model_version == "1.0"
    assert overview.row_count_scored == 1000
    assert overview.row_count_recommendations == 250
    assert overview.row_count_actionable == 120
    assert overview.mean_predicted_units == 12.5
    assert overview.total_predicted_units == 12500.0
    assert overview.total_recommended_order_qty == 5000
    assert overview.avg_stockout_risk_score == 0.44
    assert "scoring warning" in overview.warnings
    assert "recommendation warning" in overview.warnings


def test_build_recommendation_records_returns_empty_list_for_empty_dataframe() -> None:
    df = pd.DataFrame()
    result = build_recommendation_records(df, top_n=5)

    assert result == []


def test_build_recommendation_records_filters_actionable_and_priority_and_sorts() -> None:
    df = pd.DataFrame(
        {
            "forecast_date": pd.to_datetime(["2026-03-18", "2026-03-18", "2026-03-18"]),
            "target_date": pd.to_datetime(["2026-03-25", "2026-03-25", "2026-03-25"]),
            "product_id": [101, 102, 103],
            "location_id": [1, 1, 1],
            "recommended_order_qty": [50, 0, 30],
            "priority": ["high", "high", "medium"],
            "stockout_risk_score": [0.90, 0.95, 0.70],
            "reason_code": ["stockout_risk", "stockout_risk", "coverage_gap"],
            "reason_text": ["high risk", "high risk", "medium risk"],
            "model_name": ["rf", "rf", "rf"],
            "model_version": ["1.0", "1.0", "1.0"],
        }
    )

    result = build_recommendation_records(
        recommendation_df=df,
        top_n=5,
        priority_filter=["high"],
        action_only=True,
    )

    assert len(result) == 1
    assert isinstance(result[0], ForecastRecommendationRecord)
    assert result[0].product_id == 101
    assert result[0].recommended_order_qty == 50
    assert result[0].priority == "high"


def test_build_recommendation_records_respects_top_n() -> None:
    df = pd.DataFrame(
        {
            "forecast_date": pd.to_datetime(["2026-03-18", "2026-03-18", "2026-03-18"]),
            "target_date": pd.to_datetime(["2026-03-25", "2026-03-25", "2026-03-25"]),
            "product_id": [201, 202, 203],
            "recommended_order_qty": [100, 80, 60],
            "priority": ["high", "medium", "low"],
            "stockout_risk_score": [0.90, 0.70, 0.50],
        }
    )

    result = build_recommendation_records(
        recommendation_df=df,
        top_n=2,
        action_only=True,
    )

    assert len(result) == 2


def test_forecast_service_get_forecast_overview_returns_dataclass(tmp_path: Path) -> None:
    scoring_summary_path = tmp_path / "scoring_summary.json"
    recommendation_summary_path = tmp_path / "recommendation_summary.json"

    scoring_summary_path.write_text(
        json.dumps(
            {
                "model_name": "xgboost",
                "model_version": "2.0",
                "row_count_scored": 500,
                "prediction_summary": {
                    "mean_predicted_units": 8.5,
                    "total_predicted_units": 4250.0,
                },
            }
        ),
        encoding="utf-8",
    )

    recommendation_summary_path.write_text(
        json.dumps(
            {
                "row_count_total": 100,
                "row_count_actionable": 40,
                "total_recommended_order_qty": 2000,
                "avg_stockout_risk_score": 0.37,
            }
        ),
        encoding="utf-8",
    )

    service = ForecastService(
        scoring_summary_path=scoring_summary_path,
        scoring_output_path=tmp_path / "scored.csv",
        recommendation_summary_path=recommendation_summary_path,
        recommendation_output_path=tmp_path / "recommendations.csv",
        evaluation_report_path=tmp_path / "evaluation.json",
    )

    overview = service.get_forecast_overview()

    assert isinstance(overview, ForecastOverview)
    assert overview.model_name == "xgboost"
    assert overview.model_version == "2.0"
    assert overview.row_count_scored == 500
    assert overview.row_count_recommendations == 100
    assert overview.row_count_actionable == 40


def test_forecast_service_get_recommendations_returns_records(tmp_path: Path) -> None:
    recommendation_output_path = tmp_path / "recommendations.csv"

    pd.DataFrame(
        {
            "forecast_date": ["2026-03-18", "2026-03-18"],
            "target_date": ["2026-03-25", "2026-03-25"],
            "product_id": [101, 102],
            "location_id": [1, 2],
            "recommended_order_qty": [25, 0],
            "priority": ["high", "medium"],
            "stockout_risk_score": [0.88, 0.30],
            "reason_code": ["stockout_risk", "low_priority"],
            "reason_text": ["high risk", "not urgent"],
            "model_name": ["rf", "rf"],
            "model_version": ["1.0", "1.0"],
        }
    ).to_csv(recommendation_output_path, index=False)

    service = ForecastService(
        scoring_summary_path=tmp_path / "scoring_summary.json",
        scoring_output_path=tmp_path / "scored.csv",
        recommendation_summary_path=tmp_path / "recommendation_summary.json",
        recommendation_output_path=recommendation_output_path,
        evaluation_report_path=tmp_path / "evaluation.json",
    )

    results = service.get_recommendations(
        top_n=5,
        priority_filter=["high"],
        action_only=True,
    )

    assert len(results) == 1
    assert isinstance(results[0], ForecastRecommendationRecord)
    assert results[0].product_id == 101
    assert results[0].priority == "high"


def test_forecast_service_get_forecast_response_returns_combined_dataclass(tmp_path: Path) -> None:
    scoring_summary_path = tmp_path / "scoring_summary.json"
    recommendation_summary_path = tmp_path / "recommendation_summary.json"
    recommendation_output_path = tmp_path / "recommendations.csv"

    scoring_summary_path.write_text(
        json.dumps(
            {
                "model_name": "xgboost",
                "model_version": "2.1",
                "row_count_scored": 200,
                "prediction_summary": {
                    "mean_predicted_units": 6.0,
                    "total_predicted_units": 1200.0,
                },
            }
        ),
        encoding="utf-8",
    )

    recommendation_summary_path.write_text(
        json.dumps(
            {
                "row_count_total": 50,
                "row_count_actionable": 20,
                "total_recommended_order_qty": 500,
                "avg_stockout_risk_score": 0.29,
            }
        ),
        encoding="utf-8",
    )

    pd.DataFrame(
        {
            "forecast_date": ["2026-03-18"],
            "target_date": ["2026-03-25"],
            "product_id": [501],
            "recommended_order_qty": [40],
            "priority": ["high"],
            "stockout_risk_score": [0.77],
        }
    ).to_csv(recommendation_output_path, index=False)

    service = ForecastService(
        scoring_summary_path=scoring_summary_path,
        scoring_output_path=tmp_path / "scored.csv",
        recommendation_summary_path=recommendation_summary_path,
        recommendation_output_path=recommendation_output_path,
        evaluation_report_path=tmp_path / "evaluation.json",
    )

    response = service.get_forecast_response(
        top_n=5,
        priority_filter=["high"],
        action_only=True,
    )

    assert isinstance(response, ForecastServiceResponse)
    assert isinstance(response.overview, ForecastOverview)
    assert isinstance(response.recommendations, list)
    assert len(response.recommendations) == 1
    assert response.recommendations[0].product_id == 501


def test_forecast_service_healthcheck_returns_artifact_flags(tmp_path: Path) -> None:
    scoring_summary_path = tmp_path / "scoring_summary.json"
    scoring_output_path = tmp_path / "scored.csv"
    recommendation_summary_path = tmp_path / "recommendation_summary.json"
    recommendation_output_path = tmp_path / "recommendations.csv"
    evaluation_report_path = tmp_path / "evaluation.json"

    scoring_summary_path.write_text("{}", encoding="utf-8")
    scoring_output_path.write_text("a,b\n1,2\n", encoding="utf-8")
    recommendation_summary_path.write_text("{}", encoding="utf-8")
    recommendation_output_path.write_text("a,b\n1,2\n", encoding="utf-8")
    evaluation_report_path.write_text("{}", encoding="utf-8")

    service = ForecastService(
        scoring_summary_path=scoring_summary_path,
        scoring_output_path=scoring_output_path,
        recommendation_summary_path=recommendation_summary_path,
        recommendation_output_path=recommendation_output_path,
        evaluation_report_path=evaluation_report_path,
    )

    result = service.healthcheck()

    assert result["service"] == "forecast_service"
    assert result["status"] == "ok"
    assert result["artifacts_ready"]["evaluation_report"] is True
    assert result["artifacts_ready"]["scoring_summary"] is True
    assert result["artifacts_ready"]["scoring_output"] is True
    assert result["artifacts_ready"]["recommendation_summary"] is True
    assert result["artifacts_ready"]["recommendation_output"] is True