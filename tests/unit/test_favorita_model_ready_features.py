from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest

from pipelines.features import favorita_model_ready as model_ready
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
    FeatureBuildConfig,
    _fixture_source_frame,
    build_feature_rows_for_origin,
    materialize_feature_dataset,
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


def test_store_major_materialization_matches_origin_major_reference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture, origin = _fixture_source_frame()
    source_path = tmp_path / "source.parquet"
    fixture.to_parquet(source_path, index=False, row_group_size=7)
    origins = (
        (origin - pd.Timedelta(days=1)).date(),
        origin.date(),
    )

    def config_for(filename: str) -> FeatureBuildConfig:
        return FeatureBuildConfig(
            source_path=source_path,
            output_path=tmp_path / filename,
            manifest_path=tmp_path / f"{filename}.json",
            forecast_origins=origins,
            store_batches=((1,),),
            feature_profile="time-aware",
            max_items_per_store=None,
            allow_assumed_future_promotion=True,
            allow_assumed_future_holidays=True,
        )

    read_counts = {"reference": 0, "optimized": 0}
    active_path = "reference"
    original_reader = model_ready._read_filtered_source_slice

    def counting_reader(*args: object, **kwargs: object) -> pd.DataFrame:
        read_counts[active_path] += 1
        return original_reader(*args, **kwargs)

    monkeypatch.setattr(model_ready, "_read_filtered_source_slice", counting_reader)
    reference_path = tmp_path / "reference.parquet"
    materialize_feature_dataset(config_for(reference_path.name))

    active_path = "optimized"
    optimized_path = tmp_path / "optimized.parquet"
    materialize_feature_dataset(
        config_for(optimized_path.name),
        reuse_source_across_origins=True,
    )

    reference_file = pq.ParquetFile(reference_path)
    optimized_file = pq.ParquetFile(optimized_path)
    assert optimized_file.schema_arrow.equals(reference_file.schema_arrow)
    sort_columns = [
        "forecast_origin",
        "forecast_date",
        "store_nbr",
        "item_nbr",
    ]
    reference_rows = (
        reference_file.read()
        .to_pandas()
        .sort_values(sort_columns)
        .reset_index(drop=True)
    )
    optimized_rows = (
        optimized_file.read()
        .to_pandas()
        .sort_values(sort_columns)
        .reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(optimized_rows, reference_rows)
    assert read_counts == {"reference": len(origins), "optimized": 1}


def test_dual_profiles_have_exact_approved_schemas() -> None:
    contextual = model_ready.resolve_feature_profile("contextual")
    time_aware = model_ready.resolve_feature_profile("time-aware")
    assert len(contextual.model_feature_columns) == 22
    assert len(contextual.output_columns) == 25
    assert tuple(contextual.arrow_schema.names) == contextual.output_columns
    assert len(time_aware.model_feature_columns) == 40
    assert len(time_aware.output_columns) == 43
    assert tuple(time_aware.arrow_schema.names) == time_aware.output_columns
    assert time_aware.model_feature_columns[:22] == contextual.model_feature_columns
    assert time_aware.model_feature_columns[22:] == (
        model_ready.HISTORICAL_FEATURE_COLUMNS
    )


def test_invalid_feature_profile_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unsupported feature profile"):
        model_ready.resolve_feature_profile("custom")


def test_contextual_profile_skips_all_historical_builders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, origin = _fixture_source_frame()

    def reject(*args: object, **kwargs: object) -> None:
        raise AssertionError("historical builder must not run")

    monkeypatch.setattr(model_ready, "_series_feature_frame", reject)
    monkeypatch.setattr(model_ready, "_transaction_feature_frame", reject)
    monkeypatch.setattr(model_ready, "_oil_feature_values", reject)
    frame = build_feature_rows_for_origin(
        source,
        forecast_origin=origin,
        feature_profile="contextual",
    )
    assert tuple(frame.columns) == model_ready.CONTEXTUAL_OUTPUT_COLUMNS
    assert not set(model_ready.HISTORICAL_FEATURE_COLUMNS).intersection(frame.columns)


def test_profiles_produce_identical_ordered_keys_and_targets() -> None:
    source, origin = _fixture_source_frame()
    contextual = build_feature_rows_for_origin(
        source,
        forecast_origin=origin,
        feature_profile="contextual",
        drop_targets_without_origin_history=True,
    )
    time_aware = build_feature_rows_for_origin(
        source,
        forecast_origin=origin,
        feature_profile="time-aware",
        drop_targets_without_origin_history=True,
    )
    comparison_columns = [
        "forecast_origin",
        "forecast_date",
        "forecast_horizon",
        "store_nbr",
        "item_nbr",
        "unit_sales",
    ]
    pd.testing.assert_frame_equal(
        contextual.loc[:, comparison_columns],
        time_aware.loc[:, comparison_columns],
    )
    assert len(contextual) == len(time_aware)
