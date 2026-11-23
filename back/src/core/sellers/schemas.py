"""Seller request/response schemas for Plataforma de Comercio.

Provides Pydantic schemas for seller registration, store creation,
and seller profile retrieval.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SellerRegisterRequest(BaseModel):
    """Request schema for seller registration.

    Contains the required seller registration fields following the
    existing Seller model.
    """

    store_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Store name",
    )
    business_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Legal business name",
    )
    tax_id: Optional[str] = Field(
        None,
        max_length=50,
        description="Tax identification number",
    )
    payment_info_json: Optional[str] = Field(
        None,
        description="Payment information stored as JSON",
    )
    bank_account: Optional[str] = Field(
        None,
        max_length=100,
        description="Bank account identifier for payouts",
    )


class SellerResponse(BaseModel):
    """Response schema for seller profile.

    Returns seller information without sensitive fields.
    """

    seller_id: str
    store_name: str
    business_name: Optional[str]
    tax_id: Optional[str]
    payment_info_json: Optional[str]
    bank_account: Optional[str]
    is_verified: bool
    created_at: datetime


class StoreCreateRequest(BaseModel):
    """Request schema for store creation.

    Contains the required store creation fields following the
    existing Store model.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Store name",
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Store description",
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="URL-friendly store identifier",
    )
    logo_url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL to store logo image",
    )
    cover_image_url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL to store cover image",
    )


class StoreResponse(BaseModel):
    """Response schema for store profile."""

    store_id: str
    seller_id: str
    name: str
    description: Optional[str]
    slug: str
    logo_url: Optional[str]
    cover_image_url: Optional[str]
    is_active: bool
    created_at: datetime
