from __future__ import annotations

import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, settings
from app.core.monitoring import (
    decrement_http_requests_in_progress,
    increment_http_requests_in_progress,
    metrics_response,
    observe_http_request,
)
from app.schemas.forecast import FavoritaForecastRequest, FavoritaForecastResponse
from pipelines.models.favorita_bundle_inference import (
    FavoritaBundlePredictor,
    FeatureSchemaError,
)

PredictorLoader = Callable[[str | Path], FavoritaBundlePredictor]


def create_app(
    config: Settings = settings,
    predictor_loader: PredictorLoader = FavoritaBundlePredictor.load,
) -> FastAPI:
    """Create the local API with one application-scoped Favorita predictor."""

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.favorita_predictor = None
        try:
            application.state.favorita_predictor = predictor_loader(
                config.favorita_model_bundle_path
            )
        except Exception:
            raise RuntimeError(
                "Configured Favorita model bundle could not be loaded"
            ) from None
        yield
        application.state.favorita_predictor = None

    application = FastAPI(
        title=config.app_name,
        version=config.app_version,
        lifespan=lifespan,
    )
    application.state.favorita_predictor = None

    @application.get("/health", tags=["Health"])
    def health_check() -> dict[str, str]:
        return {
            "status": "ok",
            "app": config.app_name,
            "version": config.app_version,
        }

    @application.get("/ready", tags=["Health"])
    def readiness_check(request: Request) -> dict[str, str | bool]:
        loaded = request.app.state.favorita_predictor is not None
        if not loaded:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Favorita predictor is not ready",
            )
        return {"status": "ready", "favorita_predictor_loaded": True}

    @application.post(
        "/api/v1/forecast",
        response_model=FavoritaForecastResponse,
        tags=["Forecast"],
    )
    def forecast(
        payload: FavoritaForecastRequest, request: Request
    ) -> FavoritaForecastResponse:
        predictor: Any = request.app.state.favorita_predictor
        if predictor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Favorita predictor is not ready",
            )
        frame = pd.DataFrame.from_records(payload.rows)
        try:
            predictions = predictor.predict(frame)
        except FeatureSchemaError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Feature rows do not match the model contract",
            ) from None
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Forecast prediction failed",
            ) from None
        return FavoritaForecastResponse(
            predictions=[float(value) for value in predictions]
        )

    @application.middleware("http")
    async def prometheus_http_metrics_middleware(request: Request, call_next):
        increment_http_requests_in_progress()
        start_time = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            observe_http_request(
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_seconds=time.perf_counter() - start_time,
            )
            decrement_http_requests_in_progress()

    @application.get("/metrics", tags=["Monitoring"])
    def get_metrics():
        return metrics_response()

    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=config.allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return application


app = create_app()
