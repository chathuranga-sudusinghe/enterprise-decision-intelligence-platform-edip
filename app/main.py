# app\main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent_workflow import router as agent_workflow_router
from app.api.forecast import router as forecast_router
from app.api.rag import router as rag_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(rag_router)
app.include_router(forecast_router)
app.include_router(agent_workflow_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=settings.allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)