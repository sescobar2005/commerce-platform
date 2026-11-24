"""Cart request/response schemas for Plataforma de Comercio.

Provides Pydantic schemas for cart creation, cart item responses,
and cart profile responses.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CartItemResponse(BaseModel):
    """Response schema for a cart item.

    Returns cart item information including the product reference
    and price snapshot at time of addition.
    """

    cart_item_id: str
    cart_id: str
    product_id: str
    quantity: int
    price_at_time: float
    created_at: datetime


class CartResponse(BaseModel):
    """Response schema for cart profile.

    Returns cart information including all items.
    """

    cart_id: str
    user_id: str
    items: List[CartItemResponse]
    created_at: datetime
    last_updated_at: datetime
    expires_at: Optional[datetime]
