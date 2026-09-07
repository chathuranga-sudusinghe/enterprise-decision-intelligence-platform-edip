"""Pydantic contracts for local Favorita forecast serving."""

from __future__ import annotations

from pydantic import BaseModel, Field

FeatureValue = str | int | float | bool | None


class FavoritaForecastRequest(BaseModel):
    """One or more model-ready feature rows."""

    rows: list[dict[str, FeatureValue]] = Field(min_length=1)


class FavoritaForecastResponse(BaseModel):
    """Predictions in the same order as the request rows."""

    predictions: list[float]
