from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta
from math import nan

import pytest

from pipelines.evaluation.favorita_backtesting import (
    BacktestExample,
    FoldModelAdapter,
    ForecastModelInput,
    ForecastPrediction,
    build_approved_fold_datasets,
    run_expanding_window_backtest,
)
from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
    MODELING_TARGET_START,
    TemporalValidationFold,
)


def _example(
    forecast_origin: date,
    forecast_horizon: int,
    *,
    store_nbr: int = 1,
    item_nbr: int | None = None,
    unit_sales: float = 10.0,
    perishable: int = 0,
) -> BacktestExample:
    return BacktestExample(
        forecast_origin=forecast_origin,
        forecast_date=forecast_origin + timedelta(days=forecast_horizon),
        forecast_horizon=forecast_horizon,
        store_nbr=store_nbr,
        item_nbr=item_nbr or 1000 + forecast_horizon,
        unit_sales=unit_sales,
        perishable=perishable,
        features={"constant": 1.0},
    )


def _canonical_examples(
    *,
    duplicate_first_fold_population: bool = False,
) -> list[BacktestExample]:
    examples = [_example(date(2016, 12, 31), 1, item_nbr=900)]
    for fold in APPROVED_FOLDS:
        for horizon in FORECAST_HORIZONS:
            examples.append(
                _example(
                    fold.forecast_origin,
                    horizon,
                    perishable=horizon % 2,
                )
            )
            if duplicate_first_fold_population and fold.fold_id == 1:
                examples.append(
                    _example(
                        fold.forecast_origin,
                        horizon,
                        store_nbr=2,
                        perishable=horizon % 2,
                    )
                )
    return examples


def _prediction(
    row: ForecastModelInput,
    value: float,
) -> ForecastPrediction:
    return ForecastPrediction(
        forecast_origin=row.forecast_origin,
        forecast_date=row.forecast_date,
        forecast_horizon=row.forecast_horizon,
        store_nbr=row.store_nbr,
        item_nbr=row.item_nbr,
        prediction=value,
    )


class ConstantAdapter(FoldModelAdapter):
    def __init__(self, prediction_value: float = 10.0) -> None:
        self.prediction_value = prediction_value
        self.fit_calls = 0
        self.training_rows: tuple[BacktestExample, ...] = ()

    def fit(self, training_rows: Sequence[BacktestExample]) -> None:
        self.fit_calls += 1
        self.training_rows = tuple(training_rows)

    def predict(
        self,
        validation_rows: Sequence[ForecastModelInput],
    ) -> Sequence[ForecastPrediction]:
        assert all(not hasattr(row, "unit_sales") for row in validation_rows)
        return tuple(_prediction(row, self.prediction_value) for row in validation_rows)


class RecordingFactory:
    def __init__(self) -> None:
        self.adapters: list[ConstantAdapter] = []

    def __call__(self, fold: TemporalValidationFold) -> ConstantAdapter:
        adapter = ConstantAdapter()
        self.adapters.append(adapter)
        return adapter


def test_canonical_four_fold_definition_is_accepted() -> None:
    result = run_expanding_window_backtest(
        _canonical_examples(),
        RecordingFactory(),
    )

    assert tuple(fold.fold_id for fold in result.fold_results) == tuple(range(1, 5))
    assert tuple(fold.forecast_origin for fold in result.fold_results) == tuple(
        fold.forecast_origin for fold in APPROVED_FOLDS
    )


def test_fold_training_rows_enforce_label_eligibility() -> None:
    datasets = build_approved_fold_datasets(_canonical_examples())

    assert all(
        min(row.forecast_date for row in dataset.training_rows)
        == MODELING_TARGET_START
        for dataset in datasets
    )
    assert all(
        row.forecast_date <= dataset.fold.forecast_origin
        for dataset in datasets
        for row in dataset.training_rows
    )


def test_post_origin_labels_are_excluded_until_they_become_historical() -> None:
    datasets = build_approved_fold_datasets(_canonical_examples())
    first_validation_keys = {row.audit_key for row in datasets[0].validation_rows}

    assert first_validation_keys.isdisjoint(
        row.audit_key for row in datasets[0].training_rows
    )
    assert first_validation_keys.issubset(
        row.audit_key for row in datasets[1].training_rows
    )


def test_each_fold_validation_slice_covers_exactly_sixteen_horizons() -> None:
    datasets = build_approved_fold_datasets(_canonical_examples())

    assert all(
        tuple(sorted({row.forecast_horizon for row in dataset.validation_rows}))
        == FORECAST_HORIZONS
        for dataset in datasets
    )


def test_missing_validation_horizon_is_rejected() -> None:
    examples = _canonical_examples()
    examples = [
        row
        for row in examples
        if not (
            row.forecast_origin == APPROVED_FOLDS[0].forecast_origin
            and row.forecast_horizon == 16
        )
    ]

    with pytest.raises(ValueError, match="must cover horizons 1 through 16"):
        build_approved_fold_datasets(examples)


def test_fold_rows_are_chronological_and_windows_do_not_overlap() -> None:
    datasets = build_approved_fold_datasets(list(reversed(_canonical_examples())))

    assert all(
        tuple(row.forecast_date for row in dataset.training_rows)
        == tuple(sorted(row.forecast_date for row in dataset.training_rows))
        for dataset in datasets
    )
    assert all(
        tuple(row.forecast_date for row in dataset.validation_rows)
        == tuple(sorted(row.forecast_date for row in dataset.validation_rows))
        for dataset in datasets
    )
    assert all(
        current.fold.validation_end < following.fold.validation_start
        for current, following in zip(datasets, datasets[1:])
    )


def test_factory_creates_one_independently_fitted_adapter_per_fold() -> None:
    factory = RecordingFactory()

    run_expanding_window_backtest(_canonical_examples(), factory)

    assert len(factory.adapters) == 4
    assert len({id(adapter) for adapter in factory.adapters}) == 4
    assert all(adapter.fit_calls == 1 for adapter in factory.adapters)


def test_reused_adapter_instance_is_rejected() -> None:
    shared_adapter = ConstantAdapter()

    with pytest.raises(ValueError, match="fresh adapter"):
        run_expanding_window_backtest(
            _canonical_examples(),
            lambda fold: shared_adapter,
        )


def test_prediction_length_mismatch_is_rejected() -> None:
    class ShortPredictionAdapter(ConstantAdapter):
        def predict(
            self,
            validation_rows: Sequence[ForecastModelInput],
        ) -> Sequence[ForecastPrediction]:
            return super().predict(validation_rows)[:-1]

    with pytest.raises(ValueError, match="row count must match"):
        run_expanding_window_backtest(
            _canonical_examples(),
            lambda fold: ShortPredictionAdapter(),
        )


def test_non_finite_prediction_is_rejected() -> None:
    class NonFiniteAdapter(ConstantAdapter):
        def predict(
            self,
            validation_rows: Sequence[ForecastModelInput],
        ) -> Sequence[ForecastPrediction]:
            predictions = list(super().predict(validation_rows))
            predictions[0] = _prediction(validation_rows[0], nan)
            return predictions

    with pytest.raises(ValueError, match="prediction must be finite"):
        run_expanding_window_backtest(
            _canonical_examples(),
            lambda fold: NonFiniteAdapter(),
        )


def test_misaligned_prediction_audit_keys_are_rejected() -> None:
    class ReorderedAdapter(ConstantAdapter):
        def predict(
            self,
            validation_rows: Sequence[ForecastModelInput],
        ) -> Sequence[ForecastPrediction]:
            return tuple(reversed(super().predict(validation_rows)))

    with pytest.raises(ValueError, match="audit keys are misaligned"):
        run_expanding_window_backtest(
            _canonical_examples(),
            lambda fold: ReorderedAdapter(),
        )


def test_duplicate_validation_keys_are_rejected() -> None:
    examples = _canonical_examples()
    duplicate = next(
        row
        for row in examples
        if row.forecast_origin == APPROVED_FOLDS[0].forecast_origin
    )
    examples.append(duplicate)

    with pytest.raises(ValueError, match="duplicate validation keys"):
        build_approved_fold_datasets(examples)


def test_duplicate_training_keys_are_rejected() -> None:
    examples = _canonical_examples()
    duplicate = _example(date(2017, 2, 1), 1, item_nbr=777)
    examples.extend((duplicate, duplicate))

    with pytest.raises(
        ValueError,
        match="Fold 1 contains duplicate training keys",
    ):
        build_approved_fold_datasets(examples)


def test_per_fold_metrics_and_row_evidence_are_produced() -> None:
    result = run_expanding_window_backtest(
        _canonical_examples(),
        RecordingFactory(),
    )

    assert len(result.fold_results) == 4
    assert all(fold.metrics.mae == 0.0 for fold in result.fold_results)
    assert all(len(fold.predictions) == 16 for fold in result.fold_results)
    assert len(result.predictions) == 4 * 16
    assert all(row.actual_unit_sales == 10.0 for row in result.predictions)


def test_per_horizon_metrics_cover_exact_horizons_one_through_sixteen() -> None:
    result = run_expanding_window_backtest(
        _canonical_examples(),
        RecordingFactory(),
    )

    assert (
        tuple(horizon.forecast_horizon for horizon in result.horizon_results)
        == FORECAST_HORIZONS
    )
    assert all(horizon.row_count == 4 for horizon in result.horizon_results)
    assert all(horizon.metrics.mae == 0.0 for horizon in result.horizon_results)


def test_overall_metrics_are_recomputed_from_pooled_row_evidence() -> None:
    examples = _canonical_examples(duplicate_first_fold_population=True)

    def factory(fold: TemporalValidationFold) -> ConstantAdapter:
        return ConstantAdapter(20.0 if fold.fold_id == 1 else 10.0)

    result = run_expanding_window_backtest(examples, factory)
    average_fold_mae = sum(fold.metrics.mae for fold in result.fold_results) / len(
        result.fold_results
    )

    assert result.overall_metrics.mae == pytest.approx(320.0 / 80.0)
    assert average_fold_mae == 2.5
    assert result.overall_metrics.mae != average_fold_mae


def test_final_untouched_holdout_rows_are_rejected() -> None:
    examples = _canonical_examples()
    examples.append(_example(FINAL_HOLDOUT.forecast_origin, 1))

    with pytest.raises(ValueError, match="Final untouched holdout"):
        build_approved_fold_datasets(examples)


def test_input_sequence_and_feature_mapping_are_not_mutated() -> None:
    feature_values = {"constant": 1.0}
    first = BacktestExample(
        forecast_origin=date(2016, 12, 31),
        forecast_date=date(2017, 1, 1),
        forecast_horizon=1,
        store_nbr=1,
        item_nbr=900,
        unit_sales=10.0,
        perishable=0,
        features=feature_values,
    )
    examples = [first, *_canonical_examples()[1:]]
    original_order = tuple(examples)

    run_expanding_window_backtest(examples, RecordingFactory())

    assert tuple(examples) == original_order
    assert feature_values == {"constant": 1.0}
    with pytest.raises(TypeError):
        first.features["constant"] = 2.0
