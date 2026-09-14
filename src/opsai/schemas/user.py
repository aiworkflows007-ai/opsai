"""Pydantic schemas for User authentication and profiles."""

import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from opsai.models.user import UserRole
from opsai.schemas.common import ORMModel


class UserBase(ORMModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)
    role: UserRole = UserRole.EMPLOYEE
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    tenant_id: uuid.UUID


class UserUpdate(ORMModel):
    full_name: str | None = Field(None, min_length=2, max_length=150)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(None, min_length=8, max_length=100)


class UserRead(UserBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class Token(ORMModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(ORMModel):
    sub: str  # user_id
    tenant_id: str
    role: str
    exp: int
