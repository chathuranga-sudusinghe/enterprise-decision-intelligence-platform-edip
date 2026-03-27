# app/core/metrics.py

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram


# Total HTTP requests by method, path, and status code
HTTP_REQUESTS_TOTAL = Counter(
    "edip_http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status_code"],
)

# HTTP request latency in seconds by method and path
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "edip_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)

# Current in-flight requests
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "edip_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
)

# Total workflow runs by scenario and status
WORKFLOW_RUNS_TOTAL = Counter(
    "edip_workflow_runs_total",
    "Total number of workflow runs",
    ["scenario", "status"],
)

# Total forecast requests by status
FORECAST_REQUESTS_TOTAL = Counter(
    "edip_forecast_requests_total",
    "Total number of forecast API requests",
    ["status"],
)

# Total RAG requests by status
RAG_REQUESTS_TOTAL = Counter(
    "edip_rag_requests_total",
    "Total number of RAG API requests",
    ["status"],
)