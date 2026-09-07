from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pipelines.evaluation.favorita_backtesting import BacktestExample
from pipelines.features.favorita_model_ready import MODEL_FEATURE_COLUMNS
from pipelines.models.favorita_bundle_inference import (
    METADATA_FILENAME,
    MODEL_FILENAME,
    BundleIntegrityError,
    FavoritaBundleError,
    FavoritaBundlePredictor,
    FeatureSchemaError,
    UnsupportedBundleSchemaError,
)
from pipelines.models.favorita_lightgbm import FavoritaLightGBMAdapter
from pipelines.models.favorita_model_bundle import export_favorita_model_bundle

FROZEN = {
    "learning_rate": 0.02757359293934948,
    "num_leaves": 123,
    "min_data_in_leaf": 89,
    "feature_fraction": 0.8394633936788146,
}


def _values(index: int, null_column: str | None = None) -> dict[str, object]:
    values: dict[str, object] = {
        name: float(index % 7)
        for name in MODEL_FEATURE_COLUMNS
        if name not in {"store_nbr", "item_nbr"}
    }
    values.update(
        {
            "family": "GROCERY I" if index % 2 else "BEVERAGES",
            "class": 1001,
            "perishable": index % 2,
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
    if null_column:
        values[null_column] = None
    return values


def _fitted() -> FavoritaLightGBMAdapter:
    origin = date(2016, 1, 1)
    rows = tuple(
        BacktestExample(
            origin,
            origin + timedelta(days=1),
            1,
            1 + i % 3,
            1000 + i,
            float(i),
            i % 2,
            _values(i, "oil_rolling_volatility_7d"),
        )
        for i in range(32)
    )
    adapter = FavoritaLightGBMAdapter(model_parameters=FROZEN)
    adapter.fit(rows)
    return adapter


def _frame(adapter: FavoritaLightGBMAdapter) -> pd.DataFrame:
    records = []
    for i in range(3):
        values = _values(i, "oil_rolling_volatility_7d")
        values.update({"forecast_horizon": 1, "store_nbr": 1 + i, "item_nbr": 1000 + i})
        records.append(values)
    return pd.DataFrame.from_records(records).loc[:, adapter.fitted_feature_columns]


def test_native_bundle_round_trip_metadata_order_and_errors(tmp_path: Path) -> None:
    adapter = _fitted()
    frame = _frame(adapter)
    expected = adapter.fitted_booster.predict(
        adapter._prepare_feature_frame(
            frame,
            fitted=adapter.fitted_feature_columns,
            categorical=adapter.categorical_feature_columns,
            levels=adapter.categorical_levels,
        )
    )
    bundle = export_favorita_model_bundle(
        adapter,
        tmp_path / "v1",
        model_version="1.0.0",
        source_dataset_identity="synthetic-test",
    )
    metadata = json.loads((bundle / METADATA_FILENAME).read_text())
    assert (bundle / MODEL_FILENAME).is_file()
    assert metadata["bundle_schema_version"] == 1
    assert metadata["model_arm"] == "time_aware"
    assert metadata["target"] == "unit_sales"
    assert metadata["fitted_feature_columns"] == list(adapter.fitted_feature_columns)
    assert metadata["excluded_all_null_feature_columns"] == [
        "oil_rolling_volatility_7d"
    ]
    predictor = FavoritaBundlePredictor.load(bundle)
    assert predictor.fitted_feature_columns == adapter.fitted_feature_columns
    np.testing.assert_allclose(
        predictor.predict(frame), expected, rtol=1e-12, atol=1e-12
    )
    with pytest.raises(FeatureSchemaError, match="missing=forecast_horizon"):
        predictor.predict(frame.drop(columns="forecast_horizon"))
    with pytest.raises(FeatureSchemaError, match="unexpected=extra"):
        predictor.predict(frame.assign(extra=1))


def test_export_rejects_unfitted_and_existing_bundle(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="unfitted"):
        export_favorita_model_bundle(
            FavoritaLightGBMAdapter(), tmp_path / "x", model_version="1"
        )
    adapter = _fitted()
    export_favorita_model_bundle(adapter, tmp_path / "v1", model_version="1")
    with pytest.raises(FileExistsError, match="overwrite"):
        export_favorita_model_bundle(adapter, tmp_path / "v1", model_version="1")


def test_checksum_corruption_fails(tmp_path: Path) -> None:
    bundle = export_favorita_model_bundle(_fitted(), tmp_path / "v1", model_version="1")
    with (bundle / MODEL_FILENAME).open("ab") as stream:
        stream.write(b"corrupt")
    with pytest.raises(BundleIntegrityError, match="checksum"):
        FavoritaBundlePredictor.load(bundle)


def test_unsupported_schema_fails(tmp_path: Path) -> None:
    bundle = export_favorita_model_bundle(_fitted(), tmp_path / "v1", model_version="1")
    path = bundle / METADATA_FILENAME
    metadata = json.loads(path.read_text())
    metadata["bundle_schema_version"] = 999
    path.write_text(json.dumps(metadata))
    with pytest.raises(UnsupportedBundleSchemaError, match="999"):
        FavoritaBundlePredictor.load(bundle)


def test_incompatible_feature_contract_fails(tmp_path: Path) -> None:
    bundle = export_favorita_model_bundle(_fitted(), tmp_path / "v1", model_version="1")
    path = bundle / METADATA_FILENAME
    metadata = json.loads(path.read_text())
    metadata["feature_contract_name"] = "incompatible"
    path.write_text(json.dumps(metadata))
    with pytest.raises(FavoritaBundleError, match="feature_contract_name"):
        FavoritaBundlePredictor.load(bundle)


def test_relative_bundle_path_is_repository_relative(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    predictor_path = FavoritaBundlePredictor.load
    with pytest.raises(FileNotFoundError) as exc:
        predictor_path("artifacts/models/does-not-exist")
    assert str(tmp_path) not in str(exc.value)
