"""Endpoints demonstrating and verifying tenant context, isolation, and authorization."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opsai.api.deps import (
    TenantContext,
    get_db,
    get_tenant_context,
    require_roles,
    verify_tenant_access,
)
from opsai.models.knowledge import Document, DocumentStatus
from opsai.models.user import User, UserRole
from opsai.schemas.knowledge import DocumentCreate, DocumentRead

router = APIRouter(prefix="/workspaces", tags=["Workspace & Tenant Isolation"])


@router.get(
    "/context",
    summary="Inspect current tenant context and demonstrate client override immunity",
)
async def inspect_context(
    context: Annotated[TenantContext, Depends(get_tenant_context)],
    spoofed_tenant_id: Annotated[
        uuid.UUID | None,
        Query(
            description="Simulated client attempt to spoof tenant context via query parameter",
        ),
    ] = None,
):
    """Demonstrates that client-provided tenant_id is completely ignored
    in favor of the trusted token.
    """
    return {
        "authenticated_user_id": str(context.user_id),
        "authenticated_tenant_id": str(context.tenant_id),
        "authenticated_tenant_slug": context.tenant.slug,
        "user_role": context.role.value,
        "client_spoofed_tenant_id_attempt": str(spoofed_tenant_id) if spoofed_tenant_id else None,
        "active_tenant_used": str(context.tenant_id),
    }


@router.post(
    "/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a document strictly scoped to the authenticated tenant",
)
async def create_document(
    payload: DocumentCreate,
    context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Creates a document automatically bound to context.tenant_id,
    ignoring any client attempt to set tenant.
    """
    doc = Document(
        tenant_id=context.tenant_id,
        title=payload.title,
        source_id=payload.source_id,
        file_path=payload.file_path,
        mime_type=payload.mime_type,
        file_size_bytes=payload.file_size_bytes,
        status=DocumentStatus.INDEXED,
        metadata_json=payload.metadata_json,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return DocumentRead.model_validate(doc)


@router.get(
    "/documents",
    response_model=list[DocumentRead],
    summary="List documents strictly scoped to the authenticated tenant",
)
async def list_documents(
    context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Returns documents strictly matching the authenticated tenant ID."""
    stmt = (
        select(Document)
        .where(Document.tenant_id == context.tenant_id)
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(stmt)
    documents = result.scalars().all()
    return [DocumentRead.model_validate(doc) for doc in documents]


@router.get(
    "/documents/{document_id}",
    response_model=DocumentRead,
    summary="Get document by ID with object-level tenant isolation enforcement",
)
async def get_document(
    document_id: uuid.UUID,
    context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Enforces object-level tenant access. If document belongs to another tenant, returns 404."""
    doc = await db.get(Document, document_id)
    if not doc:
        verify_tenant_access(uuid.uuid4(), context, "Document")  # raises 404

    # Verify object-level tenant boundary
    verify_tenant_access(doc.tenant_id, context, "Document")
    return DocumentRead.model_validate(doc)


@router.get(
    "/admin-only",
    summary="Verify role-based authorization for administrative operations",
)
async def admin_only_action(
    admin_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    context: Annotated[TenantContext, Depends(get_tenant_context)],
):
    """Endpoint accessible only to users with the 'admin' role."""
    return {
        "message": "Administrative access authorized",
        "admin_user_id": str(admin_user.id),
        "tenant_id": str(context.tenant_id),
    }
