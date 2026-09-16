"""Aggregated API v1 router."""

from fastapi import APIRouter

from opsai.api.v1.auth import router as auth_router
from opsai.api.v1.tenant_demo import router as tenant_demo_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(tenant_demo_router)
