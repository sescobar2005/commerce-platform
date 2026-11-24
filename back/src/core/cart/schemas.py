"""Cart request/response schemas for Plataforma de Comercio.

Provides Pydantic schemas for cart creation, cart item responses,
cart item add/update requests, and cart profile responses.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CartItemAddRequest(BaseModel):
    """Request schema for adding an item to a cart.

    Requires a product ID and positive integer quantity.
    Price is not accepted from the client; it is snapshotted
    from the product record in the database.
    """

    product_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        description="Product identifier to add to the cart",
    )
    quantity: int = Field(
        ...,
        gt=0,
        description="Positive integer quantity of the product",
    )


class CartItemUpdateRequest(BaseModel):
    """Request schema for updating a cart item quantity.

    Only the quantity can be updated. Price snapshots are preserved
    unless the architecture explicitly requires refreshing them.
    """

    quantity: int = Field(
        ...,
        gt=0,
        description="Positive integer quantity of the product",
    )


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
