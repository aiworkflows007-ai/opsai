"""Unit tests for OpsAI SQLAlchemy models and multi-tenant isolation."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opsai.models import (
    AuditEvent,
    AuditStatus,
    Conversation,
    Document,
    DocumentChunk,
    DocumentStatus,
    KnowledgeSource,
    Message,
    MessageRole,
    Tenant,
    User,
    UserRole,
)


@pytest.mark.asyncio
async def test_create_tenant_and_user(db_session: AsyncSession):
    # 1. Create Tenant
    tenant = Tenant(name="Acme Corporation", slug="acme")
    db_session.add(tenant)
    await db_session.flush()

    assert tenant.id is not None
    assert tenant.slug == "acme"
    assert tenant.is_active is True

    # 2. Create User with Employee role
    user = User(
        tenant_id=tenant.id,
        email="alice@acme.com",
        hashed_password="secure_password_hash",
        full_name="Alice Smith",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()

    assert user.id is not None
    assert user.tenant_id == tenant.id
    assert user.role == UserRole.EMPLOYEE


@pytest.mark.asyncio
async def test_user_roles(db_session: AsyncSession):
    tenant = Tenant(name="Cyberdyne", slug="cyberdyne")
    db_session.add(tenant)
    await db_session.flush()

    # Verify all three roles from PRD Section 3
    admin = User(
        tenant_id=tenant.id,
        email="admin@cyberdyne.com",
        hashed_password="hash",
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    manager = User(
        tenant_id=tenant.id,
        email="manager@cyberdyne.com",
        hashed_password="hash",
        full_name="Manager User",
        role=UserRole.MANAGER,
    )
    employee = User(
        tenant_id=tenant.id,
        email="emp@cyberdyne.com",
        hashed_password="hash",
        full_name="Employee User",
        role=UserRole.EMPLOYEE,
    )

    db_session.add_all([admin, manager, employee])
    await db_session.commit()

    assert admin.role == "admin"
    assert manager.role == "manager"
    assert employee.role == "employee"


@pytest.mark.asyncio
async def test_multi_tenant_isolation(db_session: AsyncSession):
    """PRD Section 5 & 12: Tenant boundary enforced in application and data access."""
    # Create two separate tenants
    tenant_a = Tenant(name="Company A", slug="company-a")
    tenant_b = Tenant(name="Company B", slug="company-b")
    db_session.add_all([tenant_a, tenant_b])
    await db_session.flush()

    # Add document to Company A
    doc_a = Document(
        tenant_id=tenant_a.id,
        title="Confidential Strategy Company A",
        status=DocumentStatus.INDEXED,
    )
    # Add document to Company B
    doc_b = Document(
        tenant_id=tenant_b.id,
        title="Secret Roadmap Company B",
        status=DocumentStatus.INDEXED,
    )
    db_session.add_all([doc_a, doc_b])
    await db_session.commit()

    # Query strictly scoped to tenant_a
    stmt = select(Document).where(Document.tenant_id == tenant_a.id)
    result = await db_session.execute(stmt)
    tenant_a_docs = result.scalars().all()

    # Verify Company A only sees its own document
    assert len(tenant_a_docs) == 1
    assert tenant_a_docs[0].title == "Confidential Strategy Company A"
    assert all(doc.tenant_id == tenant_a.id for doc in tenant_a_docs)


@pytest.mark.asyncio
async def test_knowledge_and_chunk_vector(db_session: AsyncSession):
    """PRD Section 10: Ingestion -> Chunking -> Vector Storage."""
    tenant = Tenant(name="Initech", slug="initech")
    db_session.add(tenant)
    await db_session.flush()

    # Knowledge source
    source = KnowledgeSource(
        tenant_id=tenant.id,
        name="HR Policies",
        source_type="upload",
    )
    db_session.add(source)
    await db_session.flush()

    # Document
    doc = Document(
        tenant_id=tenant.id,
        source_id=source.id,
        title="Leave Policy 2026.pdf",
        mime_type="application/pdf",
        status=DocumentStatus.INDEXED,
    )
    db_session.add(doc)
    await db_session.flush()

    # Chunks with embeddings (1536 dims)
    mock_vector = [0.05] * 1536
    chunk = DocumentChunk(
        tenant_id=tenant.id,
        document_id=doc.id,
        chunk_index=0,
        content="Employees receive 20 days of paid annual leave.",
        token_count=12,
        embedding=mock_vector,
    )
    db_session.add(chunk)
    await db_session.commit()

    # Retrieve chunk
    stmt = select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    retrieved = (await db_session.execute(stmt)).scalar_one()

    assert retrieved.content == "Employees receive 20 days of paid annual leave."
    assert retrieved.chunk_index == 0
    assert len(retrieved.embedding) == 1536


@pytest.mark.asyncio
async def test_conversation_and_citations(db_session: AsyncSession):
    """PRD Section 6 & 8: Grounded generation with citation attribution."""
    tenant = Tenant(name="Hooli", slug="hooli")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email="richard@hooli.com",
        hashed_password="hash",
        full_name="Richard Hendricks",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.flush()

    conv = Conversation(
        tenant_id=tenant.id,
        user_id=user.id,
        title="Leave policy inquiry",
    )
    db_session.add(conv)
    await db_session.flush()

    doc_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    # Message with citation metadata
    msg = Message(
        tenant_id=tenant.id,
        conversation_id=conv.id,
        role=MessageRole.ASSISTANT,
        content="You are entitled to 20 days of annual leave.",
        citations=[
            {
                "document_id": str(doc_id),
                "chunk_id": str(chunk_id),
                "document_title": "HR Handbook.pdf",
                "score": 0.94,
            }
        ],
    )
    db_session.add(msg)
    await db_session.commit()

    stmt = select(Message).where(Message.conversation_id == conv.id)
    retrieved_msg = (await db_session.execute(stmt)).scalar_one()

    assert retrieved_msg.role == MessageRole.ASSISTANT
    assert len(retrieved_msg.citations) == 1
    assert retrieved_msg.citations[0]["score"] == 0.94


@pytest.mark.asyncio
async def test_audit_event_logging(db_session: AsyncSession):
    """PRD Section 11: Audit events record important actions and outcomes."""
    tenant = Tenant(name="Stark Industries", slug="stark")
    db_session.add(tenant)
    await db_session.flush()

    audit = AuditEvent(
        tenant_id=tenant.id,
        action="document.upload",
        resource_type="document",
        resource_id=str(uuid.uuid4()),
        status=AuditStatus.SUCCESS,
        details={"file_name": "arc_reactor_schematics.pdf", "size_bytes": 1048576},
        ip_address="192.168.1.100",
    )
    db_session.add(audit)
    await db_session.commit()

    assert audit.id is not None
    assert audit.action == "document.upload"
    assert audit.status == AuditStatus.SUCCESS


@pytest.mark.asyncio
async def test_cascade_delete_tenant(db_session: AsyncSession):
    """Deleting a tenant must cleanly cascade-delete its users and documents."""
    tenant = Tenant(name="Massive Dynamic", slug="massive-dynamic")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email="walter@massive.com",
        hashed_password="hash",
        full_name="Walter Bishop",
        role=UserRole.ADMIN,
    )
    doc = Document(tenant_id=tenant.id, title="Project Cortexiphan")
    db_session.add_all([user, doc])
    await db_session.commit()

    # Delete tenant
    await db_session.delete(tenant)
    await db_session.commit()

    # Verify user and doc are deleted
    user_check = await db_session.get(User, user.id)
    doc_check = await db_session.get(Document, doc.id)
    assert user_check is None
    assert doc_check is None
