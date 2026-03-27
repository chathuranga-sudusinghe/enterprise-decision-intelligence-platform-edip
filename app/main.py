from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent_workflow import router as agent_workflow_router
from app.api.forecast import router as forecast_router
from app.api.rag import router as rag_router
from app.core.config import settings
from app.core.monitoring import (
    decrement_http_requests_in_progress,
    increment_http_requests_in_progress,
    metrics_response,
    observe_http_request,
)

# Create FastAPI app instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

# =========================================================
# Health check endpoint
# =========================================================
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }

# =========================================================
# Middleware
# =========================================================
@app.middleware("http")
async def prometheus_http_metrics_middleware(request: Request, call_next):
    """
    Measure request count, latency, error count, and in-progress requests for all API calls.
    """
    increment_http_requests_in_progress()
    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_seconds = time.perf_counter() - start_time

        observe_http_request(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_seconds=duration_seconds,
        )

        decrement_http_requests_in_progress()


# =========================================================
# Monitoring endpoint
# =========================================================
@app.get("/metrics", tags=["Monitoring"])
def get_metrics():
    """
    Prometheus metrics endpoint.
    """
    return metrics_response()


# =========================================================
# CORS
# =========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=settings.allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Routers
# =========================================================
app.include_router(rag_router)
app.include_router(forecast_router)
app.include_router(agent_workflow_router)