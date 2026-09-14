"""FastAPI application entrypoint for OpsAI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from opsai.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-tenant AI Business Operating System API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to OpsAI Business Operating System API",
        "docs": "/docs",
        "health": "/health",
    }
