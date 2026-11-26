"""Orders request/response schemas for Plataforma de Comercio.

Provides Pydantic v2 schemas for order creation, order item responses,
order subitem responses, order summaries, and full order details.

Monetary values use Decimal throughout -- never float -- to preserve
precision. JSON serialization emits monetary values as decimal strings.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class OrderCreateRequest(BaseModel):
    """Request schema for creating an order from a cart.

    The client supplies only the cart_id. All monetary values, seller
    assignments, statuses, and fingerprints are derived server-side
    from trusted database records. The idempotency key is received via
    the HTTP Idempotency-Key header, not the request body.
    """

    cart_id: UUID = Field(
        ...,
        description="Cart identifier to convert into an order",
    )


class OrderItemResponse(BaseModel):
    """Response schema for a single order line item.

    Preserves historical snapshots of product name, SKU, and price
    taken at order time.
    """

    model_config = {"from_attributes": True}

    order_item_id: UUID
    product_id: UUID
    seller_id: UUID
    product_name: str
    product_sku: Optional[str] = None
    quantity: int = Field(..., gt=0)
    price: Decimal = Field(..., ge=0)
    created_at: datetime

    @field_serializer("price", mode="plain")
    def _serialize_price(self, value: Decimal) -> str:
        return str(value)


class OrderSubitemResponse(BaseModel):
    """Response schema for a seller sub-order within an order.

    Aggregates line items belonging to one seller for independent
    accounting and commission tracking.
    """

    model_config = {"from_attributes": True}

    order_subitem_id: UUID
    seller_id: UUID
    subtotal: Decimal = Field(..., ge=0)
    status: str
    created_at: datetime

    @field_serializer("subtotal", mode="plain")
    def _serialize_subtotal(self, value: Decimal) -> str:
        return str(value)


class OrderSummaryResponse(BaseModel):
    """Lightweight order summary for paginated listings.

    Excludes nested items and subitems for performance.
    """

    model_config = {"from_attributes": True}

    order_id: UUID
    total_amount: Decimal = Field(..., ge=0)
    status: str
    payment_status: str
    created_at: datetime

    @field_serializer("total_amount", mode="plain")
    def _serialize_total_amount(self, value: Decimal) -> str:
        return str(value)


class OrderResponse(BaseModel):
    """Full order detail response for buyer/admin access.

    Includes line items and seller subitems. Does not expose the
    internal request_fingerprint.
    """

    model_config = {"from_attributes": True}

    order_id: UUID
    user_id: UUID
    total_amount: Decimal = Field(..., ge=0)
    status: str
    payment_status: str
    items: List[OrderItemResponse]
    subitems: List[OrderSubitemResponse]
    created_at: datetime
    updated_at: datetime

    @field_serializer("total_amount", mode="plain")
    def _serialize_total_amount(self, value: Decimal) -> str:
        return str(value)


class OrderListResponse(BaseModel):
    """Paginated list of order summaries."""

    orders: List[OrderSummaryResponse]
    total: int = Field(..., ge=0)
    skip: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
