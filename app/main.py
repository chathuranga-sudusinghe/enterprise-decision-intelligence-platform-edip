from fastapi import FastAPI

from app.api.rag import router as rag_router
from app.api.forecast import router as forecast_router

app = FastAPI(
    title="EDIP API",
    version="1.0.0",
)

app.include_router(rag_router)
app.include_router(forecast_router)