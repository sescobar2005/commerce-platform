"""Product request/response schemas for Plataforma de Comercio.

Provides Pydantic schemas for product creation and product profile
responses.
"""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ProductCreateRequest(BaseModel):
    """Request schema for product creation.

    Contains the required product creation fields following the
    existing Product model.
    """

    store_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        description="Owning store identifier",
    )
    category_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        description="Product category identifier",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Product display name",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Product description",
    )
    price: float = Field(
        ...,
        gt=0,
        description="Product selling price",
    )
    cost: Optional[float] = Field(
        0.0,
        ge=0,
        description="Product cost for margin calculation",
    )
    sku: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Stock keeping unit identifier",
    )
    stock: Optional[int] = Field(
        0,
        ge=0,
        description="Current inventory quantity",
    )
    images_urls: Optional[str] = Field(
        None,
        description="Product image URLs stored as JSON array",
    )


class ProductResponse(BaseModel):
    """Response schema for product profile.

    Returns product information without sensitive fields.
    """

    product_id: str
    store_id: str
    category_id: str
    name: str
    description: Optional[str]
    price: float
    cost: float
    sku: str
    stock: int
    is_active: bool
    images_urls: Optional[str]
    created_at: datetime
    updated_at: datetime


class ProductUpdateRequest(BaseModel):
    """Request schema for product update.

    All fields are optional to support partial updates via PUT.
    Fields omitted from the request are preserved unchanged.
    """

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Product display name",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Product description",
    )
    price: Optional[float] = Field(
        None,
        gt=0,
        description="Product selling price",
    )
    cost: Optional[float] = Field(
        None,
        ge=0,
        description="Product cost for margin calculation",
    )
    sku: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Stock keeping unit identifier",
    )
    stock: Optional[int] = Field(
        None,
        ge=0,
        description="Current inventory quantity",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether the product is active and visible",
    )
    images_urls: Optional[str] = Field(
        None,
        description="Product image URLs stored as JSON array",
    )


class ProductListResponse(BaseModel):
    """Response schema for product listing with pagination.

    Returns a paginated list of products with total count and
    pagination metadata.
    """

    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
