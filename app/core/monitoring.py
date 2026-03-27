# app\core\monitoring.py

from __future__ import annotations

from typing import Optional

from fastapi import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)


# =========================================================
# HTTP-level metrics
# =========================================================
HTTP_REQUEST_COUNT = Counter(
    "edip_http_requests_total",
    "Total number of HTTP requests received by the EDIP API.",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_ERRORS = Counter(
    "edip_http_request_errors_total",
    "Total number of failed HTTP requests received by the EDIP API.",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "edip_http_request_duration_seconds",
    "HTTP request duration in seconds for the EDIP API.",
    ["method", "path"],
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "edip_http_requests_in_progress",
    "Number of HTTP requests currently being processed by the EDIP API.",
)


# =========================================================
# Workflow-level metrics
# =========================================================
WORKFLOW_RUN_COUNT = Counter(
    "edip_workflow_runs_total",
    "Total number of EDIP workflow runs by scenario and status.",
    ["scenario", "status"],
)

WORKFLOW_RUN_ERRORS = Counter(
    "edip_workflow_run_errors_total",
    "Total number of EDIP workflow run failures by scenario.",
    ["scenario"],
)


# =========================================================
# Endpoint/business-level metrics
# =========================================================
RAG_REQUEST_COUNT = Counter(
    "edip_rag_requests_total",
    "Total number of RAG API requests by status.",
    ["status"],
)

FORECAST_REQUEST_COUNT = Counter(
    "edip_forecast_requests_total",
    "Total number of forecast API requests by status.",
    ["status"],
)


# =========================================================
# Helpers
# =========================================================
def observe_http_request(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    """
    Record one HTTP request in Prometheus metrics.
    """
    status_code_str = str(status_code)

    HTTP_REQUEST_COUNT.labels(
        method=method,
        path=path,
        status_code=status_code_str,
    ).inc()

    HTTP_REQUEST_DURATION.labels(
        method=method,
        path=path,
    ).observe(duration_seconds)

    if status_code >= 400:
        HTTP_REQUEST_ERRORS.labels(
            method=method,
            path=path,
            status_code=status_code_str,
        ).inc()


def increment_http_requests_in_progress() -> None:
    """
    Increment the number of in-progress HTTP requests.
    """
    HTTP_REQUESTS_IN_PROGRESS.inc()


def decrement_http_requests_in_progress() -> None:
    """
    Decrement the number of in-progress HTTP requests.
    """
    HTTP_REQUESTS_IN_PROGRESS.dec()


def record_workflow_run(
    *,
    scenario: Optional[str],
    status: Optional[str],
) -> None:
    """
    Record one workflow run result.

    This should be called from the agent workflow API after the final result is available.
    """
    normalized_scenario = scenario or "unknown"
    normalized_status = status or "unknown"

    WORKFLOW_RUN_COUNT.labels(
        scenario=normalized_scenario,
        status=normalized_status,
    ).inc()


def record_workflow_error(
    *,
    scenario: Optional[str],
) -> None:
    """
    Record one workflow-level failure.

    This should be called from the agent workflow API exception path.
    """
    normalized_scenario = scenario or "unknown"

    WORKFLOW_RUN_ERRORS.labels(
        scenario=normalized_scenario,
    ).inc()


def record_rag_request(
    *,
    status: Optional[str],
) -> None:
    """
    Record one RAG API request by result status.
    """
    normalized_status = status or "unknown"

    RAG_REQUEST_COUNT.labels(
        status=normalized_status,
    ).inc()


def record_forecast_request(
    *,
    status: Optional[str],
) -> None:
    """
    Record one forecast API request by result status.
    """
    normalized_status = status or "unknown"

    FORECAST_REQUEST_COUNT.labels(
        status=normalized_status,
    ).inc()


def metrics_response() -> Response:
    """
    Return the Prometheus metrics payload.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )