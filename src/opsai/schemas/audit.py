"""Pydantic schemas for Audit Logging."""

import uuid
from datetime import datetime

from pydantic import Field

from opsai.models.audit import AuditStatus
from opsai.schemas.common import ORMModel


class AuditEventBase(ORMModel):
    action: str = Field(..., max_length=100)
    resource_type: str = Field(..., max_length=100)
    resource_id: str | None = None
    status: AuditStatus = AuditStatus.SUCCESS
    details: dict = Field(default_factory=dict)
    ip_address: str | None = None


class AuditEventCreate(AuditEventBase):
    tenant_id: uuid.UUID
    user_id: uuid.UUID | None = None


class AuditEventRead(AuditEventBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID | None
    created_at: datetime
