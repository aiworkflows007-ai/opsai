"""Pydantic schemas for authentication and tenant onboarding."""

from pydantic import EmailStr, Field

from opsai.schemas.common import ORMModel
from opsai.schemas.tenant import TenantRead
from opsai.schemas.user import UserRead


class LoginRequest(ORMModel):
    """Credentials submitted for user login."""

    email: EmailStr
    password: str = Field(..., min_length=1)
    tenant_slug: str | None = Field(
        None,
        description="Optional tenant slug to disambiguate email across tenants",
    )


class RegisterTenantRequest(ORMModel):
    """Payload for registering a new tenant workspace and its initial administrator."""

    tenant_name: str = Field(..., min_length=2, max_length=100, examples=["Acme Corp"])
    tenant_slug: str = Field(
        ...,
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",
        examples=["acme-corp"],
    )
    admin_email: EmailStr = Field(..., examples=["admin@acme.com"])
    admin_name: str = Field(..., min_length=2, max_length=150, examples=["Alice Admin"])
    admin_password: str = Field(..., min_length=8, max_length=100)


class AuthResponse(ORMModel):
    """Authentication response containing JWT token, user info, and resolved tenant."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
    tenant: TenantRead


class TenantContextResponse(ORMModel):
    """Identity and tenant context returned by /auth/me."""

    user: UserRead
    tenant: TenantRead
