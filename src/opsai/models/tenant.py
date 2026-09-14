"""Tenant model representing an isolated company or workspace."""

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opsai.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from opsai.models.audit import AuditEvent
    from opsai.models.conversation import Conversation
    from opsai.models.knowledge import Document, KnowledgeSource
    from opsai.models.user import User


class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tenant/Company workspace boundary. All company data is isolated by tenant_id."""

    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="tenant", cascade="all, delete-orphan"
    )
    knowledge_sources: Mapped[list["KnowledgeSource"]] = relationship(
        "KnowledgeSource", back_populates="tenant", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="tenant", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="tenant", cascade="all, delete-orphan"
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(
        "AuditEvent", back_populates="tenant", cascade="all, delete-orphan"
    )
