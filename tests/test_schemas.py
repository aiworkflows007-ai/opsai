"""Unit tests for OpsAI Pydantic schemas."""

import uuid

import pytest
from pydantic import ValidationError

from opsai.models.user import UserRole
from opsai.schemas import (
    AuditEventCreate,
    ConversationCreate,
    DocumentCreate,
    MessageCreate,
    TenantCreate,
    UserCreate,
)


def test_tenant_schema_valid():
    data = {"name": "Acme Corp", "slug": "acme-corp"}
    schema = TenantCreate(**data)
    assert schema.name == "Acme Corp"
    assert schema.slug == "acme-corp"
    assert schema.is_active is True


def test_tenant_schema_invalid_slug():
    # Slug with spaces or uppercase should fail regex ^[a-z0-9-]+$
    with pytest.raises(ValidationError):
        TenantCreate(name="Acme", slug="Invalid Slug!")


def test_user_schema_valid():
    tid = uuid.uuid4()
    data = {
        "email": "john.doe@example.com",
        "full_name": "John Doe",
        "password": "strongPassword123",
        "tenant_id": tid,
        "role": "manager",
    }
    schema = UserCreate(**data)
    assert schema.email == "john.doe@example.com"
    assert schema.role == UserRole.MANAGER


def test_user_schema_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            email="not-an-email",
            full_name="John Doe",
            password="strongPassword123",
            tenant_id=uuid.uuid4(),
        )


def test_document_create_schema():
    doc = DocumentCreate(
        title="Engineering Onboarding.pdf",
        mime_type="application/pdf",
        metadata_json={"department": "Engineering"},
    )
    assert doc.title == "Engineering Onboarding.pdf"
    assert doc.mime_type == "application/pdf"


def test_conversation_and_message_schema():
    conv = ConversationCreate(title="Sprint planning questions")
    assert conv.title == "Sprint planning questions"

    msg = MessageCreate(content="What are the sprint goals?")
    assert msg.content == "What are the sprint goals?"

    with pytest.raises(ValidationError):
        MessageCreate(content="")  # min_length=1


def test_audit_event_schema():
    event = AuditEventCreate(
        tenant_id=uuid.uuid4(),
        action="user.login",
        resource_type="auth",
        status="success",
        details={"method": "password"},
    )
    assert event.action == "user.login"
    assert event.status == "success"
