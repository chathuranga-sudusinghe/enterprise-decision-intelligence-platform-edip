from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from pipelines.models.favorita_bundle_inference import FavoritaBundlePredictor
from pipelines.models.favorita_lightgbm import FavoritaLightGBMAdapter
from pipelines.models.favorita_model_bundle import export_favorita_model_bundle
from tests.helpers.favorita import (
    fit_tiny_favorita_adapter,
    tiny_favorita_feature_frame,
)


@pytest.fixture
def tiny_bundle(tmp_path: Path) -> tuple[Path, FavoritaLightGBMAdapter]:
    adapter = fit_tiny_favorita_adapter()
    bundle = export_favorita_model_bundle(
        adapter, tmp_path / "bundle", model_version="api-test"
    )
    return bundle, adapter


def _settings(bundle_path: Path) -> Settings:
    return Settings(app_env="test", favorita_model_bundle_path=bundle_path)


def test_startup_readiness_and_forecast_use_one_loaded_predictor(
    tiny_bundle: tuple[Path, FavoritaLightGBMAdapter],
) -> None:
    bundle, adapter = tiny_bundle
    load_calls = 0

    def counting_loader(path: str | Path) -> FavoritaBundlePredictor:
        nonlocal load_calls
        load_calls += 1
        return FavoritaBundlePredictor.load(path)

    application = create_app(_settings(bundle), predictor_loader=counting_loader)
    frame = tiny_favorita_feature_frame(adapter)
    expected = FavoritaBundlePredictor.load(bundle).predict(frame)

    with TestClient(application) as client:
        assert client.get("/health").json()["status"] == "ok"
        ready = client.get("/ready")
        assert ready.status_code == 200
        assert ready.json() == {
            "status": "ready",
            "favorita_predictor_loaded": True,
        }

        first = client.post(
            "/api/v1/forecast", json={"rows": frame.to_dict(orient="records")}
        )
        second = client.post(
            "/api/v1/forecast", json={"rows": frame.to_dict(orient="records")}
        )

    assert first.status_code == 200
    assert len(first.json()["predictions"]) == len(frame)
    np.testing.assert_allclose(first.json()["predictions"], expected)
    assert second.json() == first.json()
    assert load_calls == 1


@pytest.mark.parametrize("invalid_kind", ("missing", "invalid"))
def test_startup_fails_safely_when_bundle_is_unavailable_or_invalid(
    tmp_path: Path, invalid_kind: str
) -> None:
    bundle = tmp_path / "bundle"
    if invalid_kind == "invalid":
        bundle.mkdir()
        (bundle / "metadata.json").write_text("not-json")
        (bundle / "model.txt").write_text("not-a-model")
    application = create_app(_settings(bundle))

    with pytest.raises(
        RuntimeError, match="Configured Favorita model bundle could not be loaded"
    ) as exc_info:
        with TestClient(application):
            pass

    assert str(bundle) not in str(exc_info.value)


def test_readiness_and_forecast_are_unavailable_before_startup(tmp_path: Path) -> None:
    application = create_app(_settings(tmp_path / "missing"))
    client = TestClient(application)

    ready = client.get("/ready")
    forecast = client.post("/api/v1/forecast", json={"rows": [{"feature": 1}]})

    assert ready.status_code == 503
    assert ready.json() == {"detail": "Favorita predictor is not ready"}
    assert forecast.status_code == 503


def test_invalid_feature_schema_returns_safe_client_error(
    tiny_bundle: tuple[Path, FavoritaLightGBMAdapter],
) -> None:
    bundle, adapter = tiny_bundle
    frame = tiny_favorita_feature_frame(adapter)
    invalid_rows = frame.drop(columns=frame.columns[0]).to_dict(orient="records")
    application = create_app(_settings(bundle))

    with TestClient(application) as client:
        response = client.post("/api/v1/forecast", json={"rows": invalid_rows})

    assert response.status_code == 422
    assert response.json() == {"detail": "Feature rows do not match the model contract"}
    assert str(bundle) not in response.text


def test_serving_path_uses_only_injected_load_and_predict(tmp_path: Path) -> None:
    calls: list[str] = []

    class FakePredictor:
        def predict(self, frame):
            calls.append("predict")
            return np.arange(len(frame), dtype="float64")

    def loader(_: str | Path):
        calls.append("load")
        return FakePredictor()

    application = create_app(
        _settings(tmp_path / "unused"),
        predictor_loader=loader,  # type: ignore[arg-type]
    )
    with TestClient(application) as client:
        response = client.post("/api/v1/forecast", json={"rows": [{"x": 1}, {"x": 2}]})

    assert response.json() == {"predictions": [0.0, 1.0]}
    assert calls == ["load", "predict"]
