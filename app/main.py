# app\main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.rag import router as rag_router
from app.api.forecast import router as forecast_router
from app.api.agent_workflow import router as agent_workflow_router

app = FastAPI(
    title="EDIP API",
    version="1.0.0",
)

app.include_router(rag_router)
app.include_router(forecast_router)
app.include_router(agent_workflow_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.8.161:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)