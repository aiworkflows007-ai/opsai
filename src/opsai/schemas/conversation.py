"""Pydantic schemas for Conversations and Messages."""

import uuid
from datetime import datetime

from pydantic import Field

from opsai.models.conversation import MessageRole
from opsai.schemas.common import ORMModel


class Citation(ORMModel):
    document_id: uuid.UUID
    chunk_id: uuid.UUID
    document_title: str
    content_snippet: str
    relevance_score: float | None = None


class MessageBase(ORMModel):
    role: MessageRole
    content: str = Field(..., min_length=1)
    citations: list[dict] = Field(default_factory=list)
    metadata_json: dict = Field(default_factory=dict)


class MessageCreate(ORMModel):
    content: str = Field(..., min_length=1)


class MessageRead(MessageBase):
    id: uuid.UUID
    conversation_id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime


class ConversationBase(ORMModel):
    title: str = Field(default="New Conversation", max_length=255)
    metadata_json: dict = Field(default_factory=dict)


class ConversationCreate(ConversationBase):
    pass


class ConversationRead(ConversationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ConversationDetailRead(ConversationRead):
    messages: list[MessageRead] = Field(default_factory=list)
