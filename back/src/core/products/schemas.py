"""Product request/response schemas for Plataforma de Comercio.

Provides Pydantic schemas for product creation and product profile
responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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
