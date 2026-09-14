"""Common Pydantic schema utilities and pagination."""

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base Pydantic schema configured to read from ORM models."""

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse[T](BaseModel):
    items: Sequence[T]
    total: int
    page: int
    page_size: int
    has_more: bool
