"""Pydantic schemas for Tenant management."""

import uuid
from datetime import datetime

from pydantic import Field

from opsai.schemas.common import ORMModel


class TenantBase(ORMModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Acme Corp"])
    slug: str = Field(
        ...,
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",
        examples=["acme-corp"],
    )
    is_active: bool = True
    config: dict = Field(default_factory=dict)


class TenantCreate(TenantBase):
    pass


class TenantUpdate(ORMModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    is_active: bool | None = None
    config: dict | None = None


class TenantRead(TenantBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
