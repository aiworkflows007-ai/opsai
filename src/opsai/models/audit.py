"""Audit event logging model for security and compliance tracking."""

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opsai.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from opsai.models.tenant import Tenant


class AuditStatus(enum.StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    DENIED = "denied"


class AuditEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin):
    """Immutable audit trail for all significant user, tool, and system actions."""

    __tablename__ = "audit_events"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[AuditStatus] = mapped_column(
        Enum(AuditStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=AuditStatus.SUCCESS,
        nullable=False,
    )
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="audit_events")
