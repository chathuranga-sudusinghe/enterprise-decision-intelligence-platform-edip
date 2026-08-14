from __future__ import annotations

import pandas as pd

from pipelines.features.favorita_model_ready import (
    FEATURE_DEFINITIONS,
    FORBIDDEN_MODEL_COLUMNS,
    FORECAST_HORIZONS,
    INFERENCE_OUTPUT_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    OUTPUT_ARROW_SCHEMA,
    SALES_LAG_OFFSETS,
    TARGET_COLUMN,
    TRAINING_OUTPUT_COLUMNS,
    _fixture_source_frame,
    build_feature_rows_for_origin,
    run_deterministic_fixture_validation,
)


def test_deterministic_feature_contract_across_row_groups() -> None:
    results = run_deterministic_fixture_validation()

    expected_checks = {
        "sales_lag_1_is_t_minus_1",
        "sales_lag_7_is_t_minus_7",
        "sales_lag_14_is_t_minus_14",
        "sales_lag_28_is_t_minus_28",
        "sales_windows_exclude_origin",
        "complete_calendar_windows",
        "missing_exact_date_remains_null",
        "missing_date_invalidates_sales_windows",
        "transactions_at_origin_is_t",
        "transactions_lag_7_is_t_minus_7",
        "transactions_lag_14_is_t_minus_14",
        "transaction_windows_include_origin",
        "future_actuals_do_not_affect_historical_features",
        "cross_row_group_equivalence",
    }
    assert expected_checks.issubset(results)
    assert all(results.values())


def test_exact_forecast_origin_relative_lag_definitions() -> None:
    assert SALES_LAG_OFFSETS == {
        "sales_lag_1": 1,
        "sales_lag_7": 7,
        "sales_lag_14": 14,
        "sales_lag_28": 28,
    }
    assert FEATURE_DEFINITIONS["sales_lag_1"].endswith("t-1")
    assert FEATURE_DEFINITIONS["sales_lag_7"].endswith("t-7")
    assert FEATURE_DEFINITIONS["sales_lag_14"].endswith("t-14")
    assert FEATURE_DEFINITIONS["sales_lag_28"].endswith("t-28")
    assert "[t-7,t-1]" in FEATURE_DEFINITIONS["sales_rolling_mean_7"]
    assert "[t-14,t-1]" in FEATURE_DEFINITIONS["sales_rolling_mean_14"]
    assert "[t-28,t-1]" in FEATURE_DEFINITIONS["sales_rolling_mean_28"]
    assert FEATURE_DEFINITIONS["transactions_lag_7"].endswith("t-7")
    assert FEATURE_DEFINITIONS["transactions_lag_14"].endswith("t-14")
    assert "[t-6,t]" in FEATURE_DEFINITIONS["transactions_mean_7d"]
    assert "[t-13,t]" in FEATURE_DEFINITIONS["transactions_mean_14d"]


def test_ordered_training_and_inference_schema_parity() -> None:
    assert tuple(
        column for column in TRAINING_OUTPUT_COLUMNS if column != TARGET_COLUMN
    ) == (INFERENCE_OUTPUT_COLUMNS)
    assert TARGET_COLUMN not in INFERENCE_OUTPUT_COLUMNS
    assert tuple(OUTPUT_ARROW_SCHEMA.names) == TRAINING_OUTPUT_COLUMNS


def test_forbidden_columns_and_horizon_contract() -> None:
    assert not FORBIDDEN_MODEL_COLUMNS.intersection(MODEL_FEATURE_COLUMNS)
    assert FORECAST_HORIZONS == tuple(range(1, 17))
    assert min(FORECAST_HORIZONS) == 1
    assert max(FORECAST_HORIZONS) == 16


def test_sixteen_day_row_generation_is_deterministic() -> None:
    fixture, origin = _fixture_source_frame()

    first = build_feature_rows_for_origin(
        fixture,
        forecast_origin=origin,
        allow_assumed_future_promotion=True,
        allow_assumed_future_holidays=True,
    )
    second = build_feature_rows_for_origin(
        fixture,
        forecast_origin=origin,
        allow_assumed_future_promotion=True,
        allow_assumed_future_holidays=True,
    )

    pd.testing.assert_frame_equal(first, second)
    assert len(first) == 2 * len(FORECAST_HORIZONS) == 32
    assert set(first["forecast_horizon"]) == set(FORECAST_HORIZONS)
    group_horizons = first.groupby(
        ["forecast_origin", "store_nbr", "item_nbr"], observed=True
    )["forecast_horizon"].agg(lambda values: tuple(sorted(values)))
    assert (group_horizons == tuple(FORECAST_HORIZONS)).all()
    assert not first.duplicated(
        ["forecast_origin", "forecast_date", "store_nbr", "item_nbr"]
    ).any()
    assert first["forecast_date"].min() == origin + pd.Timedelta(days=1)
    assert first["forecast_date"].max() == origin + pd.Timedelta(days=16)
    assert (
        first["forecast_date"]
        == first["forecast_origin"]
        + pd.to_timedelta(first["forecast_horizon"], unit="D")
    ).all()
