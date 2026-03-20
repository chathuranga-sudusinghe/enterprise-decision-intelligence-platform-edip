from __future__ import annotations

from collections.abc import Generator
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from app.api import forecast as forecast_api
from app.main import app


class FakeForecastService:
    def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "service": "forecast_service",
            "artifacts_ready": True,
        }

    def get_forecast_overview(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_items": 2,
                "high_priority_count": 1,
                "medium_priority_count": 1,
            },
            "model_info": {
                "model_name": "forecast_model_v1",
                "status": "ready",
            },
        }

    def get_recommendations(
        self,
        top_n: int = 20,
        priority_filter: list[str] | None = None,
        action_only: bool = True,
    ) -> list[Dict[str, Any]]:
        recommendations = [
            {
                "sku_code": "SKU-100245",
                "location_code": "WH-001",
                "recommended_order_qty": 120,
                "recommended_transfer_qty": 0,
                "priority_level": "high",
                "reason_code": "stockout_risk",
                "expected_stockout_risk": 0.82,
                "expected_service_level": 0.91,
                "approval_status": "pending",
            },
            {
                "sku_code": "SKU-100300",
                "location_code": "WH-002",
                "recommended_order_qty": 80,
                "recommended_transfer_qty": 0,
                "priority_level": "medium",
                "reason_code": "coverage_gap",
                "expected_stockout_risk": 0.45,
                "expected_service_level": 0.95,
                "approval_status": "pending",
            },
        ]

        if priority_filter:
            recommendations = [
                item
                for item in recommendations
                if item["priority_level"].lower() in priority_filter
            ]

        if action_only:
            recommendations = [
                item for item in recommendations if item["recommended_order_qty"] > 0
            ]

        return recommendations[:top_n]

    def get_forecast_response(
        self,
        top_n: int = 20,
        priority_filter: list[str] | None = None,
        action_only: bool = True,
    ) -> Dict[str, Any]:
        recommendations = self.get_recommendations(
            top_n=top_n,
            priority_filter=priority_filter,
            action_only=action_only,
        )

        return {
            "overview": self.get_forecast_overview(),
            "recommendations": recommendations,
            "filters": {
                "top_n": top_n,
                "priority_filter": priority_filter,
                "action_only": action_only,
            },
        }


class FailingForecastService:
    def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "service": "forecast_service",
            "artifacts_ready": False,
        }

    def get_forecast_overview(self) -> Dict[str, Any]:
        raise RuntimeError("Forecast overview is not available.")

    def get_recommendations(
        self,
        top_n: int = 20,
        priority_filter: list[str] | None = None,
        action_only: bool = True,
    ) -> list[Dict[str, Any]]:
        raise RuntimeError("Forecast artifacts are not available.")

    def get_forecast_response(
        self,
        top_n: int = 20,
        priority_filter: list[str] | None = None,
        action_only: bool = True,
    ) -> Dict[str, Any]:
        raise RuntimeError("Combined forecast response is not available.")


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setattr(
        forecast_api,
        "get_forecast_service",
        lambda: FakeForecastService(),
    )
    test_client = TestClient(app)
    yield test_client


def test_forecast_health_returns_200(client: TestClient) -> None:
    response = client.get("/forecast/health")

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"] == "forecast_service"
    assert payload["artifacts_ready"] is True


def test_forecast_overview_returns_200_and_payload(client: TestClient) -> None:
    response = client.get("/forecast/overview")

    assert response.status_code == 200
    payload = response.json()

    assert "summary" in payload
    assert "model_info" in payload
    assert payload["summary"]["total_items"] == 2
    assert payload["summary"]["high_priority_count"] == 1
    assert payload["model_info"]["model_name"] == "forecast_model_v1"
    assert payload["model_info"]["status"] == "ready"


def test_forecast_recommendations_returns_200_and_payload(client: TestClient) -> None:
    response = client.get(
        "/forecast/recommendations",
        params={
            "top_n": 5,
            "priority": "high",
            "action_only": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["count"] == 1
    assert payload["top_n"] == 5
    assert payload["priority_filter"] == ["high"]
    assert payload["action_only"] is True
    assert isinstance(payload["recommendations"], list)
    assert len(payload["recommendations"]) == 1
    assert payload["recommendations"][0]["sku_code"] == "SKU-100245"
    assert payload["recommendations"][0]["priority_level"] == "high"


def test_forecast_response_returns_200_and_payload(client: TestClient) -> None:
    response = client.get(
        "/forecast",
        params={
            "top_n": 5,
            "priority": "high",
            "action_only": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert "overview" in payload
    assert "recommendations" in payload
    assert "filters" in payload
    assert payload["filters"]["top_n"] == 5
    assert payload["filters"]["priority_filter"] == ["high"]
    assert payload["filters"]["action_only"] is True
    assert isinstance(payload["recommendations"], list)
    assert len(payload["recommendations"]) == 1
    assert payload["recommendations"][0]["sku_code"] == "SKU-100245"


def test_forecast_recommendations_validation_error_for_invalid_top_n(
    client: TestClient,
) -> None:
    response = client.get(
        "/forecast/recommendations",
        params={"top_n": 0},
    )

    assert response.status_code == 422


def test_forecast_recommendations_handles_service_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        forecast_api,
        "get_forecast_service",
        lambda: FailingForecastService(),
    )
    test_client = TestClient(app)

    response = test_client.get(
        "/forecast/recommendations",
        params={
            "top_n": 5,
            "priority": "high",
            "action_only": True,
        },
    )

    assert response.status_code == 500
    payload = response.json()
    assert "detail" in payload


def test_forecast_overview_handles_service_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        forecast_api,
        "get_forecast_service",
        lambda: FailingForecastService(),
    )
    test_client = TestClient(app)

    response = test_client.get("/forecast/overview")

    assert response.status_code == 500
    payload = response.json()
    assert "detail" in payload


def test_forecast_response_handles_service_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        forecast_api,
        "get_forecast_service",
        lambda: FailingForecastService(),
    )
    test_client = TestClient(app)

    response = test_client.get(
        "/forecast",
        params={
            "top_n": 5,
            "priority": "high",
            "action_only": True,
        },
    )

    assert response.status_code == 500
    payload = response.json()
    assert "detail" in payload