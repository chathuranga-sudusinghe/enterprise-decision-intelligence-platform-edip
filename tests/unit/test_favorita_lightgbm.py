from __future__ import annotations

from datetime import date, timedelta
from math import isfinite
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from pipelines.evaluation.favorita_backtesting import (
    BacktestExample,
    ForecastModelInput,
    run_expanding_window_backtest,
)
from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FORECAST_HORIZONS,
)
from pipelines.features.favorita_model_ready import (
    MODEL_FEATURE_COLUMNS,
    TARGET_COLUMN,
    _fixture_source_frame,
    build_feature_rows_for_origin,
    to_arrow_table,
)
from pipelines.models.favorita_lightgbm import (
    CONTEXTUAL_FEATURE_COLUMNS,
    DEFAULT_FEATURE_COLUMNS,
    NUM_BOOST_ROUND,
    TIME_AWARE_FEATURE_COLUMNS,
    FavoritaLightGBMAdapter,
)


def _features(
    *,
    perishable: int = 0,
    family: str = "GROCERY I",
    missing_feature: str | None = None,
    overrides: dict[str, object] | None = None,
) -> dict[str, object]:
    values: dict[str, object] = {
        name: 1.0
        for name in MODEL_FEATURE_COLUMNS
        if name not in {"store_nbr", "item_nbr"}
    }
    values.update(
        {
            "family": family,
            "class": 1001,
            "perishable": perishable,
            "city": "Quito",
            "state": "Pichincha",
            "store_type": "D",
            "cluster": 13,
            "is_weekend": False,
            "onpromotion": True,
            "is_holiday": False,
            "holiday_type": "Holiday",
            "holiday_locale": "National",
            "holiday_transferred": False,
        }
    )
    if missing_feature is not None:
        values[missing_feature] = None
    if overrides:
        values.update(overrides)
    return values


def _example(
    index: int,
    *,
    origin: date = date(2016, 1, 1),
    horizon: int = 1,
    family: str = "GROCERY I",
    unit_sales: float | None = None,
    missing_feature: str | None = None,
) -> BacktestExample:
    perishable = index % 2
    return BacktestExample(
        forecast_origin=origin,
        forecast_date=origin + timedelta(days=horizon),
        forecast_horizon=horizon,
        store_nbr=1 + index % 3,
        item_nbr=1000 + index,
        unit_sales=float(index if unit_sales is None else unit_sales),
        perishable=perishable,
        features=_features(
            perishable=perishable,
            family=family,
            missing_feature=missing_feature,
        ),
    )


def _training_rows(
    count: int = 32,
    *,
    family: str = "GROCERY I",
    all_null_feature: str | None = None,
) -> tuple[BacktestExample, ...]:
    return tuple(
        _example(
            index,
            family=family,
            unit_sales=-2.0 if index == 0 else float(index),
            missing_feature=all_null_feature,
        )
        for index in range(count)
    )


def _model_input(
    *,
    index: int = 100,
    family: str = "GROCERY I",
    overrides: dict[str, object] | None = None,
) -> ForecastModelInput:
    features = _features(perishable=index % 2, family=family, overrides=overrides)
    return ForecastModelInput(
        forecast_origin=date(2016, 2, 1),
        forecast_date=date(2016, 2, 3),
        forecast_horizon=2,
        store_nbr=1,
        item_nbr=1000 + index,
        features=features,
    )


def _model_ready_frame() -> pd.DataFrame:
    source, origin = _fixture_source_frame()
    return build_feature_rows_for_origin(
        source,
        forecast_origin=origin,
        allow_assumed_future_promotion=True,
        allow_assumed_future_holidays=True,
    )


def _write_model_ready_parquet(frame: pd.DataFrame, path: Path) -> None:
    pq.write_table(to_arrow_table(frame), path, row_group_size=7)


def test_parquet_native_fit_and_frame_prediction_avoid_row_objects(
    tmp_path: Path,
) -> None:
    frame = _model_ready_frame()
    training_path = tmp_path / "training.parquet"
    _write_model_ready_parquet(frame, training_path)
    adapter = FavoritaLightGBMAdapter()

    adapter.fit_parquet(training_path)
    predictions = adapter.predict_frame(frame.iloc[:4].copy())

    assert adapter.is_fitted
    assert adapter.fitted_feature_columns[0] == "forecast_horizon"
    assert TARGET_COLUMN not in adapter.fitted_feature_columns
    assert predictions.shape == (4,)
    assert np.isfinite(predictions).all()


def test_parquet_native_fit_rejects_noncanonical_schema(tmp_path: Path) -> None:
    frame = _model_ready_frame().drop(columns="sales_lag_1")
    training_path = tmp_path / "invalid.parquet"
    frame.to_parquet(training_path, index=False)

    with pytest.raises(ValueError, match="ordered training schema"):
        FavoritaLightGBMAdapter().fit_parquet(training_path)


def test_predict_frame_excludes_target_from_booster_input(tmp_path: Path) -> None:
    frame = _model_ready_frame()
    training_path = tmp_path / "training.parquet"
    _write_model_ready_parquet(frame, training_path)
    adapter = FavoritaLightGBMAdapter()
    adapter.fit_parquet(training_path)
    captured_columns: tuple[str, ...] = ()

    class CapturingBooster:
        def predict(self, model_frame: pd.DataFrame) -> np.ndarray:
            nonlocal captured_columns
            captured_columns = tuple(model_frame.columns)
            return np.zeros(len(model_frame), dtype="float64")

    adapter._booster = CapturingBooster()  # type: ignore[assignment]

    predictions = adapter.predict_frame(frame.iloc[:2].copy())

    assert TARGET_COLUMN not in captured_columns
    assert captured_columns == adapter.fitted_feature_columns
    assert predictions.tolist() == [0.0, 0.0]


def test_adapter_fits_and_predicts_with_tiny_synthetic_data() -> None:
    adapter = FavoritaLightGBMAdapter()
    adapter.fit(_training_rows())

    predictions = adapter.predict((_model_input(),))

    assert adapter.is_fitted
    assert len(predictions) == 1
    assert isfinite(predictions[0].prediction)


def test_prediction_before_fit_is_rejected() -> None:
    with pytest.raises(RuntimeError, match="must be fitted"):
        FavoritaLightGBMAdapter().predict((_model_input(),))


def test_target_is_excluded_and_prediction_input_rejects_it() -> None:
    adapter = FavoritaLightGBMAdapter()
    adapter.fit(_training_rows())
    features = dict(_model_input().features)
    features["unit_sales"] = 99.0
    invalid = ForecastModelInput(
        forecast_origin=date(2016, 2, 1),
        forecast_date=date(2016, 2, 3),
        forecast_horizon=2,
        store_nbr=1,
        item_nbr=1000,
        features=features,
    )

    assert "unit_sales" not in adapter.fitted_feature_columns
    with pytest.raises(ValueError, match="forbidden columns: unit_sales"):
        adapter.predict((invalid,))


def test_forecast_horizon_is_an_explicit_fitted_feature() -> None:
    adapter = FavoritaLightGBMAdapter()
    adapter.fit(_training_rows())

    assert adapter.fitted_feature_columns[0] == "forecast_horizon"


def test_forecast_horizon_outside_active_contract_is_rejected() -> None:
    row = _example(0, horizon=17)

    with pytest.raises(ValueError, match="integer from 1 through 16"):
        FavoritaLightGBMAdapter().fit((row,))


def test_categorical_levels_are_learned_from_training_only() -> None:
    rows = _training_rows(16, family="GROCERY I") + _training_rows(
        16, family="BEVERAGES"
    )
    adapter = FavoritaLightGBMAdapter()
    adapter.fit(rows)

    assert adapter.categorical_levels["family"] == ("BEVERAGES", "GROCERY I")


def test_validation_categories_do_not_refit_training_levels() -> None:
    adapter = FavoritaLightGBMAdapter()
    adapter.fit(_training_rows())
    before = dict(adapter.categorical_levels)

    adapter.predict((_model_input(family="NEW FAMILY"),))

    assert dict(adapter.categorical_levels) == before
    assert "NEW FAMILY" not in adapter.categorical_levels["family"]


def test_unknown_validation_category_is_handled_deterministically() -> None:
    adapter = FavoritaLightGBMAdapter()
    adapter.fit(_training_rows())
    row = _model_input(family="UNKNOWN")

    first = adapter.predict((row,))[0].prediction
    second = adapter.predict((row,))[0].prediction

    assert first == pytest.approx(second)


def test_all_null_training_feature_is_excluded() -> None:
    adapter = FavoritaLightGBMAdapter()
    adapter.fit(_training_rows(all_null_feature="oil_rolling_volatility_7d"))

    assert "oil_rolling_volatility_7d" in adapter.excluded_all_null_features
    assert "oil_rolling_volatility_7d" not in adapter.fitted_feature_columns


def test_partially_missing_usable_feature_is_preserved_without_imputation() -> None:
    rows = list(_training_rows())
    rows[0] = _example(0, missing_feature="sales_lag_1")
    adapter = FavoritaLightGBMAdapter()
    adapter.fit(rows)

    assert "sales_lag_1" in adapter.fitted_feature_columns
    assert adapter.training_missing_counts["sales_lag_1"] == 1


def test_fitted_feature_order_is_stable() -> None:
    adapter = FavoritaLightGBMAdapter()
    adapter.fit(_training_rows())

    assert adapter.fitted_feature_columns == DEFAULT_FEATURE_COLUMNS


def test_prediction_count_and_key_alignment_are_exact() -> None:
    adapter = FavoritaLightGBMAdapter()
    adapter.fit(_training_rows())
    rows = (_model_input(index=100), _model_input(index=101))

    predictions = adapter.predict(rows)

    assert len(predictions) == len(rows)
    assert tuple(prediction.audit_key for prediction in predictions) == tuple(
        row.audit_key for row in rows
    )


def test_predictions_are_finite() -> None:
    adapter = FavoritaLightGBMAdapter()
    adapter.fit(_training_rows())

    assert all(
        isfinite(prediction.prediction)
        for prediction in adapter.predict((_model_input(),))
    )


def test_adapter_instances_keep_independent_fold_state() -> None:
    first = FavoritaLightGBMAdapter()
    second = FavoritaLightGBMAdapter()
    first.fit(_training_rows(family="GROCERY I"))
    second.fit(_training_rows(family="BEVERAGES"))

    assert first.categorical_levels["family"] == ("GROCERY I",)
    assert second.categorical_levels["family"] == ("BEVERAGES",)
    assert first.categorical_levels is not second.categorical_levels


def test_inputs_are_not_mutated() -> None:
    training = list(_training_rows())
    validation = [_model_input()]
    training_features = dict(training[0].features)
    validation_features = dict(validation[0].features)
    adapter = FavoritaLightGBMAdapter()

    adapter.fit(training)
    adapter.predict(validation)

    assert dict(training[0].features) == training_features
    assert dict(validation[0].features) == validation_features


def test_inconsistent_feature_schema_is_rejected() -> None:
    row = _example(0)
    incomplete = dict(row.features)
    incomplete.pop("sales_lag_1")
    invalid = BacktestExample(
        forecast_origin=row.forecast_origin,
        forecast_date=row.forecast_date,
        forecast_horizon=row.forecast_horizon,
        store_nbr=row.store_nbr,
        item_nbr=row.item_nbr,
        unit_sales=row.unit_sales,
        perishable=row.perishable,
        features=incomplete,
    )

    with pytest.raises(ValueError, match="Inconsistent model feature schema"):
        FavoritaLightGBMAdapter().fit((invalid,))


def test_duplicate_feature_names_are_rejected() -> None:
    duplicate = (*DEFAULT_FEATURE_COLUMNS, DEFAULT_FEATURE_COLUMNS[-1])

    with pytest.raises(ValueError, match="duplicate feature names"):
        FavoritaLightGBMAdapter(feature_columns=duplicate)


def test_empty_training_and_prediction_inputs_are_rejected() -> None:
    with pytest.raises(ValueError, match="training_rows must not be empty"):
        FavoritaLightGBMAdapter().fit(())

    adapter = FavoritaLightGBMAdapter()
    adapter.fit(_training_rows())
    with pytest.raises(ValueError, match="validation_rows must not be empty"):
        adapter.predict(())


def test_fixed_training_configuration_is_exposed() -> None:
    adapter = FavoritaLightGBMAdapter()

    assert adapter.model_parameters["objective"] == "regression"
    assert adapter.model_parameters["learning_rate"] == 0.05
    assert adapter.model_parameters["num_leaves"] == 31
    assert adapter.model_parameters["min_data_in_leaf"] == 20
    assert adapter.model_parameters["feature_fraction"] == 0.9
    assert adapter.model_parameters["seed"] == 42
    assert adapter.model_parameters["num_threads"] == 4
    assert adapter.num_boost_round == NUM_BOOST_ROUND == 150


def test_adapter_integrates_with_approved_four_fold_backtester() -> None:
    examples = [_example(9000, origin=date(2016, 12, 31), horizon=1)]
    for fold in APPROVED_FOLDS:
        for horizon in FORECAST_HORIZONS:
            examples.append(
                _example(
                    fold.fold_id * 100 + horizon,
                    origin=fold.forecast_origin,
                    horizon=horizon,
                    unit_sales=float(fold.fold_id + horizon),
                )
            )

    result = run_expanding_window_backtest(
        examples,
        lambda fold: FavoritaLightGBMAdapter(),
    )

    assert len(result.fold_results) == 4
    assert len(result.horizon_results) == 16
    assert all(isfinite(row.prediction) for row in result.predictions)


def test_approved_feature_contracts_are_exact_and_default_is_time_aware() -> None:
    assert len(CONTEXTUAL_FEATURE_COLUMNS) == 22
    assert len(TIME_AWARE_FEATURE_COLUMNS) == 40
    assert TIME_AWARE_FEATURE_COLUMNS[:22] == CONTEXTUAL_FEATURE_COLUMNS
    assert DEFAULT_FEATURE_COLUMNS is TIME_AWARE_FEATURE_COLUMNS


@pytest.mark.parametrize(
    "feature_columns", (CONTEXTUAL_FEATURE_COLUMNS, TIME_AWARE_FEATURE_COLUMNS)
)
def test_adapter_accepts_only_each_approved_ordered_contract(
    feature_columns: tuple[str, ...],
) -> None:
    adapter = FavoritaLightGBMAdapter(feature_columns=feature_columns)
    assert adapter.candidate_feature_columns == feature_columns


def test_contextual_parquet_fit_projects_only_contextual_columns(
    tmp_path: Path,
) -> None:
    frame = _model_ready_frame()
    training_path = tmp_path / "training.parquet"
    _write_model_ready_parquet(frame, training_path)
    adapter = FavoritaLightGBMAdapter(
        feature_columns=CONTEXTUAL_FEATURE_COLUMNS
    )
    adapter.fit_parquet(training_path)
    assert adapter.fitted_feature_columns == CONTEXTUAL_FEATURE_COLUMNS
    assert not any(column.startswith("sales_lag_") for column in adapter.fitted_feature_columns)


@pytest.mark.parametrize(
    "feature_columns",
    (
        CONTEXTUAL_FEATURE_COLUMNS[:-1],
        (*CONTEXTUAL_FEATURE_COLUMNS, "sales_lag_1"),
        (*CONTEXTUAL_FEATURE_COLUMNS[1:], CONTEXTUAL_FEATURE_COLUMNS[0]),
    ),
)
def test_arbitrary_subset_superset_and_reordered_contract_are_rejected(
    feature_columns: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError, match="exactly match an approved ordered"):
        FavoritaLightGBMAdapter(feature_columns=feature_columns)


@pytest.mark.parametrize(
    "forbidden", ("unit_sales", "forecast_origin", "forecast_date")
)
def test_feature_contract_rejects_target_and_audit_columns(forbidden: str) -> None:
    invalid = (*CONTEXTUAL_FEATURE_COLUMNS[:-1], forbidden)
    with pytest.raises(ValueError, match="forbidden audit/target"):
        FavoritaLightGBMAdapter(feature_columns=invalid)
