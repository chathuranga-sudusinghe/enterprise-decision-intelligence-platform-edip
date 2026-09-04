"""Fold-local LightGBM adapter for Favorita direct-horizon forecasting."""

from __future__ import annotations

import tempfile
from bisect import bisect_right
from collections.abc import Mapping, Sequence
from math import isfinite
from numbers import Integral
from pathlib import Path
from types import MappingProxyType

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pipelines.evaluation.favorita_backtesting import (
    BacktestExample,
    ForecastModelInput,
    ForecastPrediction,
)
from pipelines.evaluation.favorita_temporal_validation import FORECAST_HORIZONS
from pipelines.features.favorita_model_ready import (
    CONTEXTUAL_FEATURE_COLUMNS,
    CONTEXTUAL_FEATURE_PROFILE,
    FORBIDDEN_MODEL_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    PARQUET_ROW_GROUP_SIZE,
    TARGET_COLUMN,
    TIME_AWARE_FEATURE_COLUMNS,
    TIME_AWARE_FEATURE_PROFILE,
    resolve_feature_profile,
)

CONTEXTUAL_FEATURE_CONTRACT = CONTEXTUAL_FEATURE_PROFILE
TIME_AWARE_FEATURE_CONTRACT = TIME_AWARE_FEATURE_PROFILE
DEFAULT_FEATURE_COLUMNS = TIME_AWARE_FEATURE_COLUMNS
FEATURE_CONTRACTS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        CONTEXTUAL_FEATURE_CONTRACT: CONTEXTUAL_FEATURE_COLUMNS,
        TIME_AWARE_FEATURE_CONTRACT: TIME_AWARE_FEATURE_COLUMNS,
    }
)
CATEGORICAL_FEATURE_CANDIDATES: tuple[str, ...] = (
    "store_nbr",
    "item_nbr",
    "family",
    "class",
    "city",
    "state",
    "store_type",
    "cluster",
    "holiday_type",
    "holiday_locale",
)
LIGHTGBM_PARAMETERS: Mapping[str, object] = MappingProxyType(
    {
        "objective": "regression",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_data_in_leaf": 20,
        "feature_fraction": 0.9,
        "seed": 42,
        "num_threads": 4,
        "verbosity": -1,
        "deterministic": True,
        "force_col_wise": True,
    }
)
NUM_BOOST_ROUND = 150

_STRUCTURAL_FEATURES = frozenset({"forecast_horizon", "store_nbr", "item_nbr"})
_EXPECTED_MAPPING_FEATURES = frozenset(MODEL_FEATURE_COLUMNS) - {
    "store_nbr",
    "item_nbr",
}


def _validate_feature_contract(feature_columns: Sequence[str]) -> tuple[str, ...]:
    columns = tuple(feature_columns)
    if not columns:
        raise ValueError("feature_columns must not be empty")
    if len(columns) != len(set(columns)):
        raise ValueError("feature_columns contains duplicate feature names")
    prohibited = set(columns) & (
        FORBIDDEN_MODEL_COLUMNS | {TARGET_COLUMN, "forecast_origin", "forecast_date"}
    )
    if prohibited:
        raise ValueError(
            "feature_columns contains forbidden audit/target columns: "
            + ", ".join(sorted(prohibited))
        )
    if columns not in FEATURE_CONTRACTS.values():
        raise ValueError(
            "feature_columns must exactly match an approved ordered Favorita "
            "feature contract"
        )
    return columns


def resolve_feature_contract(name: str) -> tuple[str, ...]:
    """Return one approved ordered contract by its stable machine name."""

    try:
        return FEATURE_CONTRACTS[name]
    except KeyError as exc:
        supported = ", ".join(FEATURE_CONTRACTS)
        raise ValueError(
            f"Unsupported feature contract {name!r}; use {supported}"
        ) from exc


def feature_contract_name(feature_columns: Sequence[str]) -> str:
    """Resolve an exact approved ordered tuple to its stable machine name."""

    columns = _validate_feature_contract(feature_columns)
    return next(
        name for name, approved in FEATURE_CONTRACTS.items() if columns == approved
    )


def _validate_feature_mapping(features: Mapping[str, object]) -> None:
    feature_names = frozenset(features)
    forbidden = feature_names & (FORBIDDEN_MODEL_COLUMNS | {TARGET_COLUMN})
    if forbidden:
        names = ", ".join(sorted(forbidden))
        raise ValueError(f"Model input contains forbidden columns: {names}")
    missing = _EXPECTED_MAPPING_FEATURES - feature_names
    unexpected = feature_names - _EXPECTED_MAPPING_FEATURES
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append(f"missing={','.join(sorted(missing))}")
        if unexpected:
            details.append(f"unexpected={','.join(sorted(unexpected))}")
        raise ValueError("Inconsistent model feature schema: " + "; ".join(details))


def _row_values(
    row: BacktestExample | ForecastModelInput,
    feature_columns: Sequence[str],
) -> dict[str, object]:
    if (
        isinstance(row.forecast_horizon, bool)
        or not isinstance(row.forecast_horizon, Integral)
        or row.forecast_horizon not in FORECAST_HORIZONS
    ):
        raise ValueError("forecast_horizon must be an integer from 1 through 16")
    _validate_feature_mapping(row.features)
    if isinstance(row, BacktestExample):
        if row.features["perishable"] != row.perishable:
            raise ValueError(
                "Training feature perishable must match BacktestExample.perishable"
            )
    structural = {
        "forecast_horizon": row.forecast_horizon,
        "store_nbr": row.store_nbr,
        "item_nbr": row.item_nbr,
    }
    return {
        name: structural[name] if name in _STRUCTURAL_FEATURES else row.features[name]
        for name in feature_columns
    }


def _ordered_categories(series: pd.Series) -> tuple[object, ...]:
    values = series.dropna().unique().tolist()
    return tuple(sorted(values, key=lambda value: (type(value).__name__, repr(value))))


class _ParquetFeatureSequence(lgb.Sequence):
    """Provide LightGBM bounded Parquet row-group feature batches."""

    batch_size = PARQUET_ROW_GROUP_SIZE

    def __init__(
        self,
        path: Path,
        *,
        columns: tuple[str, ...],
        categorical_levels: Mapping[str, tuple[object, ...]],
    ) -> None:
        self._parquet_file = pq.ParquetFile(path)
        self._columns = columns
        self._categorical_levels = categorical_levels
        self._row_group_starts = [0]
        for row_group_index in range(self._parquet_file.metadata.num_row_groups):
            row_count = self._parquet_file.metadata.row_group(
                row_group_index
            ).num_rows
            self._row_group_starts.append(
                self._row_group_starts[-1] + row_count
            )
        self._cached_row_group_index: int | None = None
        self._cached_values: np.ndarray | None = None

    def __len__(self) -> int:
        return self._row_group_starts[-1]

    def close(self) -> None:
        self._cached_values = None
        self._parquet_file.close()

    def _convert(self, table: pa.Table) -> np.ndarray:
        frame = table.to_pandas()
        for column in self._columns:
            if column in self._categorical_levels:
                frame[column] = pd.Categorical(
                    frame[column],
                    categories=self._categorical_levels[column],
                ).codes.astype("float64")
            else:
                frame[column] = pd.to_numeric(frame[column], errors="raise")
                if pd.api.types.is_bool_dtype(frame[column].dtype):
                    frame[column] = frame[column].astype("float64")
        return frame.loc[:, self._columns].to_numpy(
            dtype="float64",
            copy=False,
        )

    def _row_group_values(self, row_group_index: int) -> np.ndarray:
        if self._cached_row_group_index != row_group_index:
            table = self._parquet_file.read_row_group(
                row_group_index,
                columns=list(self._columns),
            )
            self._cached_values = self._convert(table)
            self._cached_row_group_index = row_group_index
        if self._cached_values is None:
            raise AssertionError("Parquet row-group cache was not populated")
        return self._cached_values

    def _range(self, start: int, stop: int) -> np.ndarray:
        if start < 0 or stop < start or stop > len(self):
            raise IndexError("Parquet feature sequence range is out of bounds")
        if start == stop:
            return np.empty((0, len(self._columns)), dtype="float64")
        blocks: list[np.ndarray] = []
        cursor = start
        while cursor < stop:
            row_group_index = bisect_right(
                self._row_group_starts,
                cursor,
            ) - 1
            row_group_start = self._row_group_starts[row_group_index]
            row_group_stop = self._row_group_starts[row_group_index + 1]
            local_start = cursor - row_group_start
            local_stop = min(stop, row_group_stop) - row_group_start
            blocks.append(
                self._row_group_values(row_group_index)[
                    local_start:local_stop
                ]
            )
            cursor = min(stop, row_group_stop)
        return blocks[0] if len(blocks) == 1 else np.concatenate(blocks)

    def __getitem__(
        self,
        index: int | slice | list[int],
    ) -> np.ndarray:
        if isinstance(index, Integral):
            normalized = int(index)
            if normalized < 0:
                normalized += len(self)
            return self._range(normalized, normalized + 1)[0]
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            if step != 1:
                return self._range(start, stop)[::step]
            return self._range(start, stop)
        if isinstance(index, list):
            return np.stack([self[item] for item in index])
        raise TypeError(
            f"Sequence index must be integer, slice or list, got "
            f"{type(index).__name__}"
        )


class _LabelMemmapContext:
    """Close a Windows memmap before deleting its temporary directory."""

    def __init__(self, row_count: int) -> None:
        self._row_count = row_count
        self._temporary_directory: tempfile.TemporaryDirectory[str] | None = None
        self._labels: np.memmap | None = None

    def __enter__(self) -> np.memmap:
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="favorita-lightgbm-labels-"
        )
        label_path = Path(self._temporary_directory.name) / "labels.float64"
        self._labels = np.memmap(
            label_path,
            dtype="float64",
            mode="w+",
            shape=(self._row_count,),
        )
        return self._labels

    def __exit__(self, *args: object) -> None:
        if self._labels is not None:
            self._labels.flush()
            memory_map = self._labels._mmap
            self._labels = None
            if memory_map is not None:
                memory_map.close()
        if self._temporary_directory is not None:
            self._temporary_directory.cleanup()
            self._temporary_directory = None


class FavoritaLightGBMAdapter:
    """One independently fitted global LightGBM model for one validation fold."""

    def __init__(
        self,
        *,
        feature_columns: Sequence[str] = DEFAULT_FEATURE_COLUMNS,
        model_parameters: Mapping[str, object] | None = None,
        num_boost_round: int = NUM_BOOST_ROUND,
    ) -> None:
        if isinstance(num_boost_round, bool) or not isinstance(
            num_boost_round, Integral
        ):
            raise TypeError("num_boost_round must be an integer")
        if num_boost_round <= 0:
            raise ValueError("num_boost_round must be positive")
        supplied_parameters = dict(model_parameters or {})
        if any(not isinstance(name, str) or not name for name in supplied_parameters):
            raise ValueError("model parameter names must be non-empty strings")
        if "num_boost_round" in supplied_parameters:
            raise ValueError(
                "num_boost_round must be supplied through its explicit argument"
            )
        effective_parameters = dict(LIGHTGBM_PARAMETERS)
        effective_parameters.update(supplied_parameters)
        self._model_parameters: Mapping[str, object] = MappingProxyType(
            effective_parameters
        )
        self._num_boost_round = int(num_boost_round)
        self._candidate_feature_columns = _validate_feature_contract(feature_columns)
        self._feature_contract_name = feature_contract_name(
            self._candidate_feature_columns
        )
        self._feature_profile = resolve_feature_profile(
            self._feature_contract_name
        )
        self._booster: lgb.Booster | None = None
        self._fitted_feature_columns: tuple[str, ...] = ()
        self._excluded_all_null_features: tuple[str, ...] = ()
        self._categorical_feature_columns: tuple[str, ...] = ()
        self._categorical_levels: Mapping[str, tuple[object, ...]] = MappingProxyType(
            {}
        )
        self._training_missing_counts: Mapping[str, int] = MappingProxyType({})

    @property
    def is_fitted(self) -> bool:
        return self._booster is not None

    @property
    def feature_contract_name(self) -> str:
        return self._feature_contract_name

    @property
    def candidate_feature_columns(self) -> tuple[str, ...]:
        return self._candidate_feature_columns

    @property
    def fitted_feature_columns(self) -> tuple[str, ...]:
        return self._fitted_feature_columns

    @property
    def excluded_all_null_features(self) -> tuple[str, ...]:
        return self._excluded_all_null_features

    @property
    def categorical_feature_columns(self) -> tuple[str, ...]:
        return self._categorical_feature_columns

    @property
    def categorical_levels(self) -> Mapping[str, tuple[object, ...]]:
        return self._categorical_levels

    @property
    def training_missing_counts(self) -> Mapping[str, int]:
        return self._training_missing_counts

    @property
    def model_parameters(self) -> Mapping[str, object]:
        return self._model_parameters

    @property
    def num_boost_round(self) -> int:
        return self._num_boost_round

    def _materialize_frame(
        self,
        rows: Sequence[BacktestExample | ForecastModelInput],
    ) -> pd.DataFrame:
        return pd.DataFrame.from_records(
            [_row_values(row, self._candidate_feature_columns) for row in rows],
            columns=self._candidate_feature_columns,
        )

    @staticmethod
    def _coerce_numeric(frame: pd.DataFrame, categorical: set[str]) -> None:
        for column in frame.columns:
            if column not in categorical:
                frame[column] = pd.to_numeric(frame[column], errors="raise")
                if pd.api.types.is_bool_dtype(frame[column].dtype):
                    frame[column] = frame[column].astype(float)

    def _validate_model_ready_frame(self, frame: pd.DataFrame) -> None:
        if tuple(frame.columns) != self._feature_profile.output_columns:
            raise ValueError(
                "Model-ready frame must match the ordered training schema"
            )
        if frame.empty:
            raise ValueError("Model-ready frame must not be empty")
        if not frame["forecast_horizon"].isin(FORECAST_HORIZONS).all():
            raise ValueError("forecast_horizon must be an integer from 1 through 16")

    @classmethod
    def _prepare_feature_frame(
        cls,
        frame: pd.DataFrame,
        *,
        fitted: tuple[str, ...],
        categorical: tuple[str, ...],
        levels: Mapping[str, tuple[object, ...]],
    ) -> pd.DataFrame:
        prepared = frame.loc[:, fitted].copy()
        for column in categorical:
            values = prepared[column]
            known_or_missing = values.isna() | values.isin(levels[column])
            prepared[column] = pd.Categorical(
                values.where(known_or_missing),
                categories=levels[column],
            ).codes.astype("float64")
        cls._coerce_numeric(prepared, set(categorical))
        return prepared

    def _record_fitted_state(
        self,
        *,
        booster: lgb.Booster,
        fitted: tuple[str, ...],
        excluded: tuple[str, ...],
        categorical: tuple[str, ...],
        levels: Mapping[str, tuple[object, ...]],
        missing_counts: Mapping[str, int],
    ) -> None:
        self._booster = booster
        self._fitted_feature_columns = fitted
        self._excluded_all_null_features = excluded
        self._categorical_feature_columns = categorical
        self._categorical_levels = MappingProxyType(dict(levels))
        self._training_missing_counts = MappingProxyType(dict(missing_counts))

    def fit(self, training_rows: Sequence[BacktestExample]) -> None:
        if self.is_fitted:
            raise RuntimeError("FavoritaLightGBMAdapter instances cannot be refitted")
        rows = tuple(training_rows)
        if not rows:
            raise ValueError("training_rows must not be empty")
        if not all(isinstance(row, BacktestExample) for row in rows):
            raise TypeError("training_rows must contain only BacktestExample rows")

        frame = self._materialize_frame(rows)
        excluded = tuple(
            column for column in frame.columns if frame[column].isna().all()
        )
        fitted = tuple(
            column
            for column in self._candidate_feature_columns
            if column not in excluded
        )
        if not fitted:
            raise ValueError("No usable training features remain after null inspection")
        categorical = tuple(
            column for column in CATEGORICAL_FEATURE_CANDIDATES if column in fitted
        )
        levels = {column: _ordered_categories(frame[column]) for column in categorical}
        model_frame = self._prepare_feature_frame(
            frame,
            fitted=fitted,
            categorical=categorical,
            levels=levels,
        )

        targets = pd.Series(
            [row.unit_sales for row in rows], dtype="float64", name=TARGET_COLUMN
        )
        if not all(isfinite(value) for value in targets):
            raise ValueError("Training targets must be finite")

        dataset = lgb.Dataset(
            model_frame,
            label=targets,
            feature_name=list(fitted),
            categorical_feature=list(categorical),
            free_raw_data=True,
        )
        booster = lgb.train(
            dict(self._model_parameters),
            dataset,
            num_boost_round=self._num_boost_round,
        )

        self._record_fitted_state(
            booster=booster,
            fitted=fitted,
            excluded=excluded,
            categorical=categorical,
            levels=levels,
            missing_counts={
                column: int(frame[column].isna().sum()) for column in fitted
            },
        )

    def fit_parquet(self, training_path: Path) -> None:
        """Fit from batched Parquet features without row-object materialization."""

        if self.is_fitted:
            raise RuntimeError("FavoritaLightGBMAdapter instances cannot be refitted")
        if not training_path.is_file():
            raise FileNotFoundError(training_path)
        parquet_file = pq.ParquetFile(training_path)
        try:
            if not parquet_file.schema_arrow.equals(
                self._feature_profile.arrow_schema
            ):
                raise ValueError(
                    "Parquet must match the ordered training schema "
                    f"for profile {self._feature_contract_name}"
                )
            row_count = parquet_file.metadata.num_rows
            if row_count <= 0:
                raise ValueError("Training Parquet must not be empty")
        finally:
            parquet_file.close()

        missing_counts = {
            column: 0 for column in self._candidate_feature_columns
        }
        category_values: dict[str, set[object]] = {
            column: set()
            for column in CATEGORICAL_FEATURE_CANDIDATES
            if column in self._candidate_feature_columns
        }
        observed_horizons: set[int] = set()
        with _LabelMemmapContext(row_count) as labels:
            parquet_file = pq.ParquetFile(training_path)
            cursor = 0
            try:
                for batch in parquet_file.iter_batches(
                    batch_size=131_072,
                    columns=[
                        *self._candidate_feature_columns,
                        TARGET_COLUMN,
                    ],
                ):
                    frame = batch.to_pandas()
                    batch_rows = len(frame)
                    for column in self._candidate_feature_columns:
                        missing_counts[column] += int(
                            frame[column].isna().sum()
                        )
                    for column in category_values:
                        category_values[column].update(
                            frame[column].dropna().unique().tolist()
                        )
                    observed_horizons.update(
                        int(value)
                        for value in frame["forecast_horizon"].dropna().unique()
                    )
                    targets = pd.to_numeric(
                        frame[TARGET_COLUMN],
                        errors="raise",
                    ).to_numpy(dtype="float64", copy=False)
                    if not np.isfinite(targets).all():
                        raise ValueError("Training targets must be finite")
                    labels[cursor : cursor + batch_rows] = targets
                    cursor += batch_rows
            finally:
                parquet_file.close()
            if cursor != row_count:
                raise AssertionError("Training label scan row count changed")
            if not observed_horizons.issubset(set(FORECAST_HORIZONS)):
                raise ValueError(
                    "forecast_horizon must be an integer from 1 through 16"
                )
            labels.flush()

            excluded = tuple(
                column
                for column in self._candidate_feature_columns
                if missing_counts[column] == row_count
            )
            fitted = tuple(
                column
                for column in self._candidate_feature_columns
                if column not in excluded
            )
            if not fitted:
                raise ValueError(
                    "No usable training features remain after null inspection"
                )
            categorical = tuple(
                column
                for column in CATEGORICAL_FEATURE_CANDIDATES
                if column in fitted
            )
            levels = {
                column: tuple(
                    sorted(
                        category_values[column],
                        key=lambda value: (
                            type(value).__name__,
                            repr(value),
                        ),
                    )
                )
                for column in categorical
            }
            sequence = _ParquetFeatureSequence(
                training_path,
                columns=fitted,
                categorical_levels=levels,
            )
            try:
                dataset = lgb.Dataset(
                    sequence,
                    label=labels,
                    feature_name=list(fitted),
                    categorical_feature=list(categorical),
                    free_raw_data=True,
                )
                booster = lgb.train(
                    dict(self._model_parameters),
                    dataset,
                    num_boost_round=self._num_boost_round,
                )
            finally:
                sequence.close()
            self._record_fitted_state(
                booster=booster,
                fitted=fitted,
                excluded=excluded,
                categorical=categorical,
                levels=levels,
                missing_counts={
                    column: missing_counts[column] for column in fitted
                },
            )

    def _predict_frame_values(self, frame: pd.DataFrame) -> np.ndarray:
        if self._booster is None:
            raise RuntimeError(
                "FavoritaLightGBMAdapter must be fitted before prediction"
            )
        prepared = self._prepare_feature_frame(
            frame,
            fitted=self._fitted_feature_columns,
            categorical=self._categorical_feature_columns,
            levels=self._categorical_levels,
        )
        values = np.asarray(self._booster.predict(prepared), dtype="float64")
        if len(values) != len(frame):
            raise ValueError("LightGBM returned an unexpected prediction count")
        if not np.isfinite(values).all():
            raise ValueError("LightGBM returned a non-finite prediction")
        return values

    def predict_frame(self, validation_frame: pd.DataFrame) -> np.ndarray:
        """Predict a model-ready validation frame while excluding its target."""

        self._validate_model_ready_frame(validation_frame)
        return self._predict_frame_values(validation_frame)

    def predict(
        self,
        validation_rows: Sequence[ForecastModelInput],
    ) -> tuple[ForecastPrediction, ...]:
        if self._booster is None:
            raise RuntimeError(
                "FavoritaLightGBMAdapter must be fitted before prediction"
            )
        rows = tuple(validation_rows)
        if not rows:
            raise ValueError("validation_rows must not be empty")
        if not all(isinstance(row, ForecastModelInput) for row in rows):
            raise TypeError(
                "validation_rows must contain only target-free ForecastModelInput rows"
            )

        frame = self._materialize_frame(rows)
        values = self._predict_frame_values(frame)

        return tuple(
            ForecastPrediction(
                forecast_origin=row.forecast_origin,
                forecast_date=row.forecast_date,
                forecast_horizon=row.forecast_horizon,
                store_nbr=row.store_nbr,
                item_nbr=row.item_nbr,
                prediction=float(value),
            )
            for row, value in zip(rows, values, strict=True)
        )
