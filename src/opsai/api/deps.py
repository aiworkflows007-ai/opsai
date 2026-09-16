"""FastAPI dependencies for authentication, tenant context, and authorization."""

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from opsai.core.security import decode_access_token
from opsai.db.session import get_db
from opsai.models.tenant import Tenant
from opsai.models.user import User, UserRole

# HTTP Bearer token extractor (auto_error=False gives us fine-grained error control)
security_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class TenantContext:
    """Immutable execution context binding the request to an authenticated user and tenant."""

    tenant: Tenant
    user: User

    @property
    def tenant_id(self) -> uuid.UUID:
        return self.tenant.id

    @property
    def user_id(self) -> uuid.UUID:
        return self.user.id

    @property
    def role(self) -> UserRole:
        return self.user.role


async def get_current_user(
    auth: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Extract, decode, and verify the bearer token, returning the authenticated user.

    Validates:
    1. Token presence and bearer scheme
    2. Signature and expiration
    3. User existence and active status
    4. Tenant association and active status
    """
    if not auth or auth.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(auth.credentials)

    try:
        user_uuid = uuid.UUID(payload.sub)
        token_tenant_uuid = uuid.UUID(payload.tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    stmt = select(User).options(selectinload(User.tenant)).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.tenant_id != token_tenant_uuid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tenant does not match user tenant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.tenant or not user.tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant workspace is disabled or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_tenant(
    current_user: Annotated[User, Depends(get_current_user)],
) -> Tenant:
    """Return the tenant strictly bound to the authenticated user.

    Never trusts client-supplied tenant_id query parameters or headers.
    """
    return current_user.tenant


async def get_tenant_context(
    current_user: Annotated[User, Depends(get_current_user)],
) -> TenantContext:
    """Provide combined user and tenant context to downstream endpoints and services."""
    return TenantContext(tenant=current_user.tenant, user=current_user)


class RoleChecker:
    """Authorization dependency verifying that the authenticated user possesses a required role."""

    def __init__(self, *allowed_roles: UserRole):
        self.allowed_roles = set(allowed_roles)

    def __call__(self, current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in self.allowed_roles:
            role_names = [r.value for r in self.allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the following roles: {role_names}",
            )
        return current_user


def require_roles(*roles: UserRole) -> RoleChecker:
    """Factory creating an authorization guard for one or more permitted roles."""
    return RoleChecker(*roles)


def verify_tenant_access(
    resource_tenant_id: uuid.UUID,
    context: TenantContext,
    resource_name: str = "Resource",
) -> None:
    """Enforce object-level multi-tenant isolation.

    Raises HTTP 404 (Not Found) if a resource belongs to another tenant.
    Using 404 instead of 403 prevents leaking resource existence across tenant boundaries.
    """
    if resource_tenant_id != context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} not found",
        )
