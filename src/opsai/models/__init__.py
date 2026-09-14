"""OpsAI database models."""

from opsai.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from opsai.models.audit import AuditEvent, AuditStatus
from opsai.models.conversation import Conversation, Message, MessageRole
from opsai.models.knowledge import Document, DocumentChunk, DocumentStatus, KnowledgeSource
from opsai.models.tenant import Tenant
from opsai.models.user import User, UserRole

__all__ = [
    "AuditEvent",
    "AuditStatus",
    "Base",
    "Conversation",
    "Document",
    "DocumentChunk",
    "DocumentStatus",
    "KnowledgeSource",
    "Message",
    "MessageRole",
    "Tenant",
    "TenantScopedMixin",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "User",
    "UserRole",
]
