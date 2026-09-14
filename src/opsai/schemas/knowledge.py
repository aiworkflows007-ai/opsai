"""Pydantic schemas for Knowledge Sources, Documents, and Chunks."""

import uuid
from datetime import datetime

from pydantic import Field

from opsai.models.knowledge import DocumentStatus
from opsai.schemas.common import ORMModel


class KnowledgeSourceBase(ORMModel):
    name: str = Field(..., min_length=2, max_length=150)
    source_type: str = Field(default="upload", max_length=50)
    description: str | None = None
    config: dict = Field(default_factory=dict)


class KnowledgeSourceCreate(KnowledgeSourceBase):
    pass


class KnowledgeSourceRead(KnowledgeSourceBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DocumentChunkRead(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    content: str
    token_count: int
    metadata_json: dict
    created_at: datetime


class DocumentBase(ORMModel):
    title: str = Field(..., min_length=1, max_length=255)
    source_id: uuid.UUID | None = None
    mime_type: str = "text/plain"
    metadata_json: dict = Field(default_factory=dict)


class DocumentCreate(DocumentBase):
    file_path: str | None = None
    file_size_bytes: int = 0


class DocumentRead(DocumentBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    file_path: str | None
    file_size_bytes: int
    status: DocumentStatus
    error_message: str | None
    version: int
    created_at: datetime
    updated_at: datetime


class DocumentDetailRead(DocumentRead):
    chunks: list[DocumentChunkRead] = Field(default_factory=list)
