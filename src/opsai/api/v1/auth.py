"""Authentication router for tenant registration, user login, and profile resolution."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from opsai.api.deps import TenantContext, get_db, get_tenant_context
from opsai.config import settings
from opsai.core.security import create_access_token, hash_password, verify_password
from opsai.models.tenant import Tenant
from opsai.models.user import User, UserRole
from opsai.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterTenantRequest,
    TenantContextResponse,
)
from opsai.schemas.tenant import TenantRead
from opsai.schemas.user import Token, UserRead

router = APIRouter(prefix="/auth", tags=["Authentication & Tenant"])


@router.post(
    "/register-tenant",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new tenant workspace and administrator",
)
async def register_tenant(
    payload: RegisterTenantRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new isolated company tenant and create its initial admin user."""
    # 1. Verify tenant slug uniqueness
    slug_stmt = select(Tenant).where(Tenant.slug == payload.tenant_slug)
    existing_tenant = (await db.execute(slug_stmt)).scalar_one_or_none()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant slug '{payload.tenant_slug}' is already registered",
        )

    # 2. Create Tenant
    tenant = Tenant(
        name=payload.tenant_name,
        slug=payload.tenant_slug,
        is_active=True,
    )
    db.add(tenant)
    await db.flush()

    # 3. Create Admin User
    admin_user = User(
        tenant_id=tenant.id,
        email=payload.admin_email,
        full_name=payload.admin_name,
        hashed_password=hash_password(payload.admin_password),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin_user)
    await db.commit()
    await db.refresh(tenant)
    await db.refresh(admin_user)

    # 4. Generate JWT access token
    expires_in_seconds = settings.access_token_expire_minutes * 60
    access_token = create_access_token(
        subject=admin_user.id,
        tenant_id=tenant.id,
        role=admin_user.role.value,
    )

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=UserRead.model_validate(admin_user),
        tenant=TenantRead.model_validate(tenant),
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate user and issue JWT access token",
)
async def login(
    credentials: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate user with email and password, returning a signed JWT."""
    stmt = select(User).options(selectinload(User.tenant)).where(User.email == credentials.email)

    if credentials.tenant_slug:
        stmt = stmt.join(Tenant).where(Tenant.slug == credentials.tenant_slug)

    result = await db.execute(stmt)
    users = result.scalars().all()

    if not users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if len(users) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Multiple workspaces found for this email. Please specify 'tenant_slug'.",
        )

    user = users[0]

    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.tenant or not user.tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant workspace is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires_in_seconds = settings.access_token_expire_minutes * 60
    access_token = create_access_token(
        subject=user.id,
        tenant_id=user.tenant_id,
        role=user.role.value,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
    )


@router.get(
    "/me",
    response_model=TenantContextResponse,
    summary="Get current user profile and resolved tenant context",
)
async def get_me(
    context: Annotated[TenantContext, Depends(get_tenant_context)],
):
    """Returns the authenticated identity and the server-side resolved tenant context."""
    return TenantContextResponse(
        user=UserRead.model_validate(context.user),
        tenant=TenantRead.model_validate(context.tenant),
    )
