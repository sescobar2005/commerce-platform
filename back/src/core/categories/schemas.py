"""Category request/response schemas for Plataforma de Comercio.

Provides Pydantic schemas for category creation, update, listing,
and product-in-category responses.
"""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class CategoryCreateRequest(BaseModel):
    """Request schema for category creation.

    Contains the required category creation fields following the
    existing Category model.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Category display name",
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Category description",
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="URL-friendly category identifier",
    )
    parent_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=36,
        description="Parent category identifier for hierarchy",
    )


class CategoryResponse(BaseModel):
    """Response schema for category profile.

    Returns category information without sensitive fields.
    """

    category_id: str
    name: str
    description: Optional[str]
    slug: str
    parent_id: Optional[str]
    level: int
    path: str
    is_active: bool
    created_at: datetime


class CategoryUpdateRequest(BaseModel):
    """Request schema for category update.

    All fields are optional to support partial updates via PUT.
    Fields omitted from the request are preserved unchanged.
    """

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Category display name",
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Category description",
    )
    slug: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="URL-friendly category identifier",
    )
    parent_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=36,
        description="Parent category identifier for hierarchy",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether the category is active",
    )


class CategoryListResponse(BaseModel):
    """Response schema for category listing with pagination.

    Returns a paginated list of categories with total count and
    pagination metadata.
    """

    items: List[CategoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CategoryProductsListResponse(BaseModel):
    """Response schema for products belonging to a category.

    Returns a paginated list of products within a category.
    """

    items: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int
