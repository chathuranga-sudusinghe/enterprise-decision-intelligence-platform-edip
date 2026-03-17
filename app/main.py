from fastapi import FastAPI

from app.api.rag import router as rag_router

app = FastAPI(
    title="EDIP API",
    version="1.0.0",
)

app.include_router(rag_router)