"""Model-agnostic SCRUM-16 expanding-window backtesting for Favorita."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from math import isfinite
from numbers import Integral, Real
from types import MappingProxyType
from typing import Protocol

from pipelines.evaluation.favorita_metrics import (
    ForecastMetricResults,
    evaluate_favorita_forecasts,
)
from pipelines.evaluation.favorita_temporal_validation import (
    APPROVED_FOLDS,
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
    TemporalValidationFold,
    is_training_target_eligible,
    validate_approved_contract,
    validate_forecast_date_horizon,
)


@dataclass(frozen=True, slots=True)
class BacktestExample:
    """One labelled direct-horizon example available to the backtester."""

    forecast_origin: date
    forecast_date: date
    forecast_horizon: int
    store_nbr: int
    item_nbr: int
    unit_sales: float
    perishable: int
    features: Mapping[str, object] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "features", MappingProxyType(dict(self.features)))

    @property
    def audit_key(self) -> tuple[date, date, int, int, int]:
        return (
            self.forecast_origin,
            self.forecast_date,
            self.forecast_horizon,
            self.store_nbr,
            self.item_nbr,
        )

    @property
    def validation_key(self) -> tuple[date, date, int, int]:
        return (
            self.forecast_origin,
            self.forecast_date,
            self.store_nbr,
            self.item_nbr,
        )


@dataclass(frozen=True, slots=True)
class ForecastModelInput:
    """Target-free validation input provided to a fold adapter."""

    forecast_origin: date
    forecast_date: date
    forecast_horizon: int
    store_nbr: int
    item_nbr: int
    features: Mapping[str, object] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "features", MappingProxyType(dict(self.features)))

    @property
    def audit_key(self) -> tuple[date, date, int, int, int]:
        return (
            self.forecast_origin,
            self.forecast_date,
            self.forecast_horizon,
            self.store_nbr,
            self.item_nbr,
        )


@dataclass(frozen=True, slots=True)
class ForecastPrediction:
    """One keyed prediction returned by a fold adapter."""

    forecast_origin: date
    forecast_date: date
    forecast_horizon: int
    store_nbr: int
    item_nbr: int
    prediction: float

    @property
    def audit_key(self) -> tuple[date, date, int, int, int]:
        return (
            self.forecast_origin,
            self.forecast_date,
            self.forecast_horizon,
            self.store_nbr,
            self.item_nbr,
        )


class FoldModelAdapter(Protocol):
    """Fresh per-fold model and preprocessing adapter contract."""

    def fit(self, training_rows: Sequence[BacktestExample]) -> None:
        """Fit all fold-specific learned state from eligible training rows."""

    def predict(
        self,
        validation_rows: Sequence[ForecastModelInput],
    ) -> Sequence[ForecastPrediction]:
        """Return keyed predictions in the same order as validation_rows."""


FoldAdapterFactory = Callable[[TemporalValidationFold], FoldModelAdapter]


@dataclass(frozen=True, slots=True)
class FoldBacktestDataset:
    """Immutable chronological training and validation rows for one fold."""

    fold: TemporalValidationFold
    training_rows: tuple[BacktestExample, ...]
    validation_rows: tuple[BacktestExample, ...]


@dataclass(frozen=True, slots=True)
class EvaluationEvidence:
    """Immutable row-level evidence retained from one validation prediction."""

    fold_id: int
    forecast_origin: date
    forecast_date: date
    forecast_horizon: int
    store_nbr: int
    item_nbr: int
    actual_unit_sales: float
    prediction: float
    perishable: int


@dataclass(frozen=True, slots=True)
class FoldBacktestResult:
    """Metrics and row evidence for one independently fitted fold."""

    fold_id: int
    forecast_origin: date
    validation_start: date
    validation_end: date
    metrics: ForecastMetricResults
    predictions: tuple[EvaluationEvidence, ...]


@dataclass(frozen=True, slots=True)
class HorizonBacktestResult:
    """Pooled metrics for one forecast horizon across all folds."""

    forecast_horizon: int
    metrics: ForecastMetricResults
    row_count: int


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Complete immutable SCRUM-16 validation result."""

    overall_metrics: ForecastMetricResults
    fold_results: tuple[FoldBacktestResult, ...]
    horizon_results: tuple[HorizonBacktestResult, ...]
    predictions: tuple[EvaluationEvidence, ...]


def _require_date(value: object, name: str) -> None:
    if type(value) is not date:
        raise TypeError(f"{name} must be a datetime.date")


def _require_integral(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")


def _require_finite_real(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    if not isfinite(float(value)):
        raise ValueError(f"{name} must be finite")


def _validate_example(example: BacktestExample) -> None:
    _require_date(example.forecast_origin, "forecast_origin")
    _require_date(example.forecast_date, "forecast_date")
    _require_integral(example.forecast_horizon, "forecast_horizon")
    _require_integral(example.store_nbr, "store_nbr")
    _require_integral(example.item_nbr, "item_nbr")
    _require_finite_real(example.unit_sales, "unit_sales")
    if example.perishable not in (0, 1, False, True):
        raise ValueError("perishable must be a binary 0/1 indicator")
    validate_forecast_date_horizon(
        example.forecast_origin,
        example.forecast_date,
        example.forecast_horizon,
    )
    if example.forecast_origin == FINAL_HOLDOUT.forecast_origin or (
        FINAL_HOLDOUT.holdout_start
        <= example.forecast_date
        <= FINAL_HOLDOUT.holdout_end
    ):
        raise ValueError("Final untouched holdout rows are forbidden in backtesting")


def _validated_examples(
    examples: Sequence[BacktestExample],
) -> tuple[BacktestExample, ...]:
    materialized = tuple(examples)
    if not materialized:
        raise ValueError("examples must not be empty")
    for example in materialized:
        if not isinstance(example, BacktestExample):
            raise TypeError("examples must contain only BacktestExample rows")
        _validate_example(example)
    return materialized


def _training_sort_key(example: BacktestExample) -> tuple[date, date, int, int, int]:
    return (
        example.forecast_date,
        example.forecast_origin,
        example.forecast_horizon,
        example.store_nbr,
        example.item_nbr,
    )


def _validation_sort_key(example: BacktestExample) -> tuple[date, int, int]:
    return (example.forecast_date, example.store_nbr, example.item_nbr)


def _require_unique_example_keys(
    rows: Sequence[BacktestExample],
    fold_id: int,
    partition: str,
) -> None:
    keys = tuple(row.validation_key for row in rows)
    if len(keys) != len(set(keys)):
        raise ValueError(f"Fold {fold_id} contains duplicate {partition} keys")


def build_approved_fold_datasets(
    examples: Sequence[BacktestExample],
) -> tuple[FoldBacktestDataset, ...]:
    """Build the canonical eight chronological fold datasets without mutation."""

    validate_approved_contract()
    rows = _validated_examples(examples)
    datasets: list[FoldBacktestDataset] = []

    for fold in APPROVED_FOLDS:
        training_rows = tuple(
            sorted(
                (
                    row
                    for row in rows
                    if is_training_target_eligible(
                        row.forecast_date,
                        fold.forecast_origin,
                    )
                ),
                key=_training_sort_key,
            )
        )
        validation_rows = tuple(
            sorted(
                (
                    row
                    for row in rows
                    if row.forecast_origin == fold.forecast_origin
                    and fold.validation_start
                    <= row.forecast_date
                    <= fold.validation_end
                ),
                key=_validation_sort_key,
            )
        )
        if not training_rows:
            raise ValueError(f"Fold {fold.fold_id} has no eligible training rows")
        if not validation_rows:
            raise ValueError(f"Fold {fold.fold_id} has no validation rows")
        _require_unique_example_keys(training_rows, fold.fold_id, "training")
        if tuple(sorted({row.forecast_horizon for row in validation_rows})) != (
            FORECAST_HORIZONS
        ):
            raise ValueError(
                f"Fold {fold.fold_id} validation rows must cover horizons 1 through 16"
            )
        _require_unique_example_keys(validation_rows, fold.fold_id, "validation")
        datasets.append(
            FoldBacktestDataset(
                fold=fold,
                training_rows=training_rows,
                validation_rows=validation_rows,
            )
        )

    return tuple(datasets)


def _model_inputs(
    rows: Sequence[BacktestExample],
) -> tuple[ForecastModelInput, ...]:
    return tuple(
        ForecastModelInput(
            forecast_origin=row.forecast_origin,
            forecast_date=row.forecast_date,
            forecast_horizon=row.forecast_horizon,
            store_nbr=row.store_nbr,
            item_nbr=row.item_nbr,
            features=row.features,
        )
        for row in rows
    )


def _validated_predictions(
    expected_rows: Sequence[ForecastModelInput],
    predictions: Sequence[ForecastPrediction],
    fold_id: int,
) -> tuple[ForecastPrediction, ...]:
    materialized = tuple(predictions)
    if len(materialized) != len(expected_rows):
        raise ValueError(
            f"Fold {fold_id} prediction row count must match validation row count"
        )
    for expected, prediction in zip(expected_rows, materialized):
        if not isinstance(prediction, ForecastPrediction):
            raise TypeError("Adapter predictions must be ForecastPrediction rows")
        if prediction.audit_key != expected.audit_key:
            raise ValueError(f"Fold {fold_id} prediction audit keys are misaligned")
        _require_finite_real(prediction.prediction, "prediction")
    return materialized


def _metric_results(
    evidence: Sequence[EvaluationEvidence],
) -> ForecastMetricResults:
    return evaluate_favorita_forecasts(
        actual=tuple(row.actual_unit_sales for row in evidence),
        prediction=tuple(row.prediction for row in evidence),
        perishable=tuple(row.perishable for row in evidence),
    )


def run_fold_backtest(
    dataset: FoldBacktestDataset,
    adapter: FoldModelAdapter,
) -> FoldBacktestResult:
    """Fit and score one canonical fold without materializing any other fold."""

    if not isinstance(dataset, FoldBacktestDataset):
        raise TypeError("dataset must be a FoldBacktestDataset")
    if dataset.fold not in APPROVED_FOLDS:
        raise ValueError("dataset must use one canonical approved fold")
    training_rows = _validated_examples(dataset.training_rows)
    validation_rows = _validated_examples(dataset.validation_rows)
    if any(
        not is_training_target_eligible(
            row.forecast_date,
            dataset.fold.forecast_origin,
        )
        for row in training_rows
    ):
        raise ValueError(
            f"Fold {dataset.fold.fold_id} training labels exceed the fold origin"
        )
    if any(
        row.forecast_origin != dataset.fold.forecast_origin
        or not (
            dataset.fold.validation_start
            <= row.forecast_date
            <= dataset.fold.validation_end
        )
        for row in validation_rows
    ):
        raise ValueError(
            f"Fold {dataset.fold.fold_id} validation rows are outside O+1..O+16"
        )
    if tuple(sorted({row.forecast_horizon for row in validation_rows})) != (
        FORECAST_HORIZONS
    ):
        raise ValueError(
            f"Fold {dataset.fold.fold_id} validation rows must cover "
            "horizons 1 through 16"
        )
    _require_unique_example_keys(
        validation_rows,
        dataset.fold.fold_id,
        "validation",
    )

    adapter.fit(training_rows)
    model_inputs = _model_inputs(validation_rows)
    predictions = _validated_predictions(
        model_inputs,
        adapter.predict(model_inputs),
        dataset.fold.fold_id,
    )
    fold_evidence = tuple(
        EvaluationEvidence(
            fold_id=dataset.fold.fold_id,
            forecast_origin=actual.forecast_origin,
            forecast_date=actual.forecast_date,
            forecast_horizon=actual.forecast_horizon,
            store_nbr=actual.store_nbr,
            item_nbr=actual.item_nbr,
            actual_unit_sales=float(actual.unit_sales),
            prediction=float(prediction.prediction),
            perishable=int(actual.perishable),
        )
        for actual, prediction in zip(validation_rows, predictions, strict=True)
    )
    return FoldBacktestResult(
        fold_id=dataset.fold.fold_id,
        forecast_origin=dataset.fold.forecast_origin,
        validation_start=dataset.fold.validation_start,
        validation_end=dataset.fold.validation_end,
        metrics=_metric_results(fold_evidence),
        predictions=fold_evidence,
    )


def aggregate_fold_backtest_results(
    fold_results: Sequence[FoldBacktestResult],
) -> BacktestResult:
    """Aggregate eight completed fold results without retaining fold training rows."""

    results = tuple(fold_results)
    if tuple(result.fold_id for result in results) != tuple(range(1, 9)):
        raise ValueError("Fold results must be the ordered canonical folds 1 through 8")
    for result, fold in zip(results, APPROVED_FOLDS, strict=True):
        if (
            result.forecast_origin != fold.forecast_origin
            or result.validation_start != fold.validation_start
            or result.validation_end != fold.validation_end
        ):
            raise ValueError(
                f"Fold result {result.fold_id} does not match canonical dates"
            )

    predictions = tuple(
        row for result in results for row in result.predictions
    )
    if not predictions:
        raise ValueError("Completed fold results contain no prediction evidence")
    horizon_results = tuple(
        HorizonBacktestResult(
            forecast_horizon=horizon,
            metrics=_metric_results(
                tuple(
                    row
                    for row in predictions
                    if row.forecast_horizon == horizon
                )
            ),
            row_count=sum(
                row.forecast_horizon == horizon for row in predictions
            ),
        )
        for horizon in FORECAST_HORIZONS
    )
    return BacktestResult(
        overall_metrics=_metric_results(predictions),
        fold_results=results,
        horizon_results=horizon_results,
        predictions=predictions,
    )


def run_expanding_window_backtest(
    examples: Sequence[BacktestExample],
    adapter_factory: FoldAdapterFactory,
) -> BacktestResult:
    """Run eight independent fits and return fold, horizon, and pooled metrics."""

    fold_datasets = build_approved_fold_datasets(examples)
    adapters: list[FoldModelAdapter] = []
    fold_results: list[FoldBacktestResult] = []

    for dataset in fold_datasets:
        adapter = adapter_factory(dataset.fold)
        if any(adapter is existing for existing in adapters):
            raise ValueError(
                "adapter_factory must return a fresh adapter for each fold"
            )
        adapters.append(adapter)
        fold_result = run_fold_backtest(dataset, adapter)
        fold_results.append(fold_result)

    return aggregate_fold_backtest_results(fold_results)
