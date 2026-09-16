"""Tests for authentication, tenant context resolution, and tenant isolation (Issue #2)."""

import uuid
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from opsai.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from opsai.models.knowledge import Document, DocumentStatus
from opsai.models.tenant import Tenant
from opsai.models.user import User, UserRole

# ---------------------------------------------------------------------------
# Unit tests: Password hashing and JWT token handling
# ---------------------------------------------------------------------------


def test_password_hashing():
    raw_password = "superSecretPassword123"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("wrongPassword", hashed) is False


def test_token_creation_and_decoding():
    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    token = create_access_token(
        subject=user_id,
        tenant_id=tenant_id,
        role="admin",
        expires_delta=timedelta(minutes=15),
    )

    payload = decode_access_token(token)
    assert payload.sub == str(user_id)
    assert payload.tenant_id == str(tenant_id)
    assert payload.role == "admin"


def test_expired_token_rejected():
    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    # Create token that expired 10 seconds ago
    expired_token = create_access_token(
        subject=user_id,
        tenant_id=tenant_id,
        role="employee",
        expires_delta=timedelta(seconds=-10),
    )

    with pytest.raises(Exception) as exc_info:
        decode_access_token(expired_token)
    assert "expired" in str(exc_info.value.detail).lower()


def test_invalid_token_rejected():
    with pytest.raises(Exception) as exc_info:
        decode_access_token("completely-invalid-garbage-token")
    assert "could not validate credentials" in str(exc_info.value.detail).lower()


# ---------------------------------------------------------------------------
# API Integration tests: Tenant Registration and Login Endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_tenant_endpoint(client: AsyncClient):
    payload = {
        "tenant_name": "Globex Corp",
        "tenant_slug": "globex-corp",
        "admin_email": "hank.scorpio@globex.com",
        "admin_name": "Hank Scorpio",
        "admin_password": "superVillainPassword99",
    }
    response = await client.post("/api/v1/auth/register-tenant", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data
    assert data["tenant"]["slug"] == "globex-corp"
    assert data["user"]["email"] == "hank.scorpio@globex.com"
    assert data["user"]["role"] == "admin"

    # Duplicate slug registration rejected (409)
    dup_response = await client.post("/api/v1/auth/register-tenant", json=payload)
    assert dup_response.status_code == 409


@pytest.mark.asyncio
async def test_login_endpoint(client: AsyncClient, db_session: AsyncSession):
    # Setup tenant and user
    tenant = Tenant(name="Cyberdyne Systems", slug="cyberdyne")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email="miles.dyson@cyberdyne.com",
        hashed_password=hash_password("terminator2026"),
        full_name="Miles Dyson",
        role=UserRole.MANAGER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Successful login
    login_payload = {
        "email": "miles.dyson@cyberdyne.com",
        "password": "terminator2026",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Incorrect password rejected (401)
    bad_login = {
        "email": "miles.dyson@cyberdyne.com",
        "password": "wrongPassword!",
    }
    bad_resp = await client.post("/api/v1/auth/login", json=bad_login)
    assert bad_resp.status_code == 401


# ---------------------------------------------------------------------------
# API Integration tests: Authentication & Tenant Context Enforcement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(client: AsyncClient):
    """Requirement: Reject unauthenticated requests appropriately."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers


@pytest.mark.asyncio
async def test_valid_authenticated_request_accepted(client: AsyncClient, db_session: AsyncSession):
    """Requirement: Valid authenticated request accepted, resolving identity and tenant."""
    tenant = Tenant(name="Wayne Enterprises", slug="wayne")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email="bruce@wayne.com",
        hashed_password=hash_password("batcave123"),
        full_name="Bruce Wayne",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(subject=user.id, tenant_id=tenant.id, role=user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "bruce@wayne.com"
    assert data["tenant"]["slug"] == "wayne"
    assert data["tenant"]["id"] == str(tenant.id)


@pytest.mark.asyncio
async def test_invalid_and_expired_tokens_rejected(client: AsyncClient, db_session: AsyncSession):
    """Requirement: Invalid and expired authentication rejected."""
    tenant = Tenant(name="Acme", slug="acme-test")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email="test@acme.com",
        hashed_password=hash_password("pwd"),
        full_name="Test User",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()

    # 1. Tampered / invalid token
    bad_headers = {"Authorization": "Bearer not.a.valid.jwt.token"}
    resp_bad = await client.get("/api/v1/auth/me", headers=bad_headers)
    assert resp_bad.status_code == 401

    # 2. Expired token
    expired_token = create_access_token(
        subject=user.id,
        tenant_id=tenant.id,
        role="employee",
        expires_delta=timedelta(seconds=-1),
    )
    resp_expired = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert resp_expired.status_code == 401
    assert "expired" in resp_expired.json()["detail"].lower()


@pytest.mark.asyncio
async def test_authenticated_user_resolves_to_correct_tenant(
    client: AsyncClient, db_session: AsyncSession
):
    """Requirement: Authenticated user resolves to correct tenant."""
    t1 = Tenant(name="Tenant Alpha", slug="alpha")
    t2 = Tenant(name="Tenant Beta", slug="beta")
    db_session.add_all([t1, t2])
    await db_session.flush()

    u1 = User(
        tenant_id=t1.id,
        email="u1@alpha.com",
        hashed_password="h",
        full_name="User 1",
        role=UserRole.EMPLOYEE,
    )
    u2 = User(
        tenant_id=t2.id,
        email="u2@beta.com",
        hashed_password="h",
        full_name="User 2",
        role=UserRole.EMPLOYEE,
    )
    db_session.add_all([u1, u2])
    await db_session.commit()

    token1 = create_access_token(subject=u1.id, tenant_id=t1.id, role=u1.role.value)
    token2 = create_access_token(subject=u2.id, tenant_id=t2.id, role=u2.role.value)

    res1 = await client.get(
        "/api/v1/workspaces/context", headers={"Authorization": f"Bearer {token1}"}
    )
    assert res1.status_code == 200
    assert res1.json()["authenticated_tenant_id"] == str(t1.id)
    assert res1.json()["authenticated_tenant_slug"] == "alpha"

    res2 = await client.get(
        "/api/v1/workspaces/context", headers={"Authorization": f"Bearer {token2}"}
    )
    assert res2.status_code == 200
    assert res2.json()["authenticated_tenant_id"] == str(t2.id)
    assert res2.json()["authenticated_tenant_slug"] == "beta"


@pytest.mark.asyncio
async def test_client_supplied_tenant_id_cannot_override_authenticated_tenant(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Requirement: Client-supplied tenant_id cannot override authenticated tenant context."""
    real_tenant = Tenant(name="Real Tenant", slug="real-tenant")
    victim_tenant = Tenant(name="Victim Tenant", slug="victim-tenant")
    db_session.add_all([real_tenant, victim_tenant])
    await db_session.flush()

    attacker_user = User(
        tenant_id=real_tenant.id,
        email="attacker@realtemp.com",
        hashed_password="pwd",
        full_name="Attacker",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(attacker_user)
    await db_session.commit()

    token = create_access_token(
        subject=attacker_user.id,
        tenant_id=real_tenant.id,
        role=attacker_user.role.value,
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to spoof context by supplying victim tenant id as query param
    spoofed_id = str(victim_tenant.id)
    resp = await client.get(
        f"/api/v1/workspaces/context?spoofed_tenant_id={spoofed_id}", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()

    # Verify that the active tenant used remains strictly the authenticated real tenant
    assert data["active_tenant_used"] == str(real_tenant.id)
    assert data["authenticated_tenant_id"] == str(real_tenant.id)
    assert data["client_spoofed_tenant_id_attempt"] == spoofed_id


@pytest.mark.asyncio
async def test_cross_tenant_resource_access_rejected(client: AsyncClient, db_session: AsyncSession):
    """Requirement: Cross-tenant resource access is rejected (404 to avoid information leakage)."""
    tenant_a = Tenant(name="Company A", slug="comp-a")
    tenant_b = Tenant(name="Company B", slug="comp-b")
    db_session.add_all([tenant_a, tenant_b])
    await db_session.flush()

    user_a = User(
        tenant_id=tenant_a.id,
        email="user@comp-a.com",
        hashed_password="pwd",
        full_name="User A",
        role=UserRole.EMPLOYEE,
    )
    user_b = User(
        tenant_id=tenant_b.id,
        email="user@comp-b.com",
        hashed_password="pwd",
        full_name="User B",
        role=UserRole.EMPLOYEE,
    )
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    # Company B owns a secret document
    secret_doc = Document(
        tenant_id=tenant_b.id,
        title="Company B Secret Blueprint",
        status=DocumentStatus.INDEXED,
    )
    db_session.add(secret_doc)
    await db_session.commit()

    token_a = create_access_token(subject=user_a.id, tenant_id=tenant_a.id, role=user_a.role.value)
    token_b = create_access_token(subject=user_b.id, tenant_id=tenant_b.id, role=user_b.role.value)

    # 1. User B can access their own document
    resp_b = await client.get(
        f"/api/v1/workspaces/documents/{secret_doc.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 200
    assert resp_b.json()["title"] == "Company B Secret Blueprint"

    # 2. User A attempting to access Company B's document is rejected with 404 (preventing leakage)
    resp_a = await client.get(
        f"/api/v1/workspaces/documents/{secret_doc.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_a.status_code == 404
    assert "not found" in resp_a.json()["detail"].lower()


@pytest.mark.asyncio
async def test_role_based_authorization_guard(client: AsyncClient, db_session: AsyncSession):
    """Requirement: Authorization foundation distinguishing employee vs admin roles."""
    tenant = Tenant(name="Pied Piper", slug="piedpiper")
    db_session.add(tenant)
    await db_session.flush()

    admin_user = User(
        tenant_id=tenant.id,
        email="richard@piedpiper.com",
        hashed_password="pwd",
        full_name="Richard Hendricks",
        role=UserRole.ADMIN,
    )
    employee_user = User(
        tenant_id=tenant.id,
        email="dinesh@piedpiper.com",
        hashed_password="pwd",
        full_name="Dinesh Chugtai",
        role=UserRole.EMPLOYEE,
    )
    db_session.add_all([admin_user, employee_user])
    await db_session.commit()

    admin_token = create_access_token(
        subject=admin_user.id, tenant_id=tenant.id, role=admin_user.role.value
    )
    employee_token = create_access_token(
        subject=employee_user.id, tenant_id=tenant.id, role=employee_user.role.value
    )

    # Admin access succeeds
    resp_admin = await client.get(
        "/api/v1/workspaces/admin-only",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_admin.status_code == 200
    assert resp_admin.json()["message"] == "Administrative access authorized"

    # Employee access is forbidden (403)
    resp_employee = await client.get(
        "/api/v1/workspaces/admin-only",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert resp_employee.status_code == 403
    assert "requires one of the following roles" in resp_employee.json()["detail"]


@pytest.mark.asyncio
async def test_disabled_user_or_tenant_rejected(client: AsyncClient, db_session: AsyncSession):
    """Requirement: Security handling for disabled user accounts and inactive tenants."""
    active_tenant = Tenant(name="Active Co", slug="active-co", is_active=True)
    disabled_tenant = Tenant(name="Disabled Co", slug="disabled-co", is_active=False)
    db_session.add_all([active_tenant, disabled_tenant])
    await db_session.flush()

    disabled_user = User(
        tenant_id=active_tenant.id,
        email="disabled@active.com",
        hashed_password="pwd",
        full_name="Disabled User",
        role=UserRole.EMPLOYEE,
        is_active=False,
    )
    user_in_disabled_tenant = User(
        tenant_id=disabled_tenant.id,
        email="user@disabled.com",
        hashed_password="pwd",
        full_name="User Disabled Tenant",
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    db_session.add_all([disabled_user, user_in_disabled_tenant])
    await db_session.commit()

    # Disabled user token
    token1 = create_access_token(
        subject=disabled_user.id, tenant_id=active_tenant.id, role="employee"
    )
    r1 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token1}"})
    assert r1.status_code == 401
    assert "disabled" in r1.json()["detail"].lower()

    # User in disabled tenant token
    token2 = create_access_token(
        subject=user_in_disabled_tenant.id, tenant_id=disabled_tenant.id, role="employee"
    )
    r2 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token2}"})
    assert r2.status_code == 401
    assert "disabled or inactive" in r2.json()["detail"].lower()
