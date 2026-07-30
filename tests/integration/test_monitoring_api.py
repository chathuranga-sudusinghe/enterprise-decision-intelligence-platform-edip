from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

EXPECTED_METRIC_FAMILIES = (
    "edip_http_requests_total",
    "edip_http_request_duration_seconds",
    "edip_http_requests_in_progress",
    "edip_workflow_runs_total",
    "edip_rag_requests_total",
    "edip_forecast_requests_total",
)


def test_app_main_imports_successfully() -> None:
    assert app is not None


def test_exactly_one_metrics_route_is_registered() -> None:
    metrics_routes = [route for route in app.routes if route.path == "/metrics"]

    assert len(metrics_routes) == 1


def test_metrics_endpoint_exposes_active_prometheus_families() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200

    content_type = response.headers["content-type"].lower()
    assert content_type.startswith("text/plain")

    for metric_family in EXPECTED_METRIC_FAMILIES:
        assert metric_family in response.text
