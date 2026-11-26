"""Order models for Plataforma de Comercio.

Represents orders, order items, seller sub-orders, payments, and
commissions for the multi-vendor marketplace. Orders capture business
transactions between buyers and sellers with price snapshots, inventory
reservation tracking, and commission accounting.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.product import Product
from src.core.models.seller import Seller
from src.core.models.user import User


class Order(Base):
    """Order model.

    Represents a complete buyer purchase across potentially multiple
    sellers. Each order contains one or more order items and one or
    more seller sub-orders for multi-vendor accounting isolation.
    """

    __tablename__ = "orders"

    order_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique order identifier",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Owning user identifier (buyer)",
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Total order amount across all items",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="Order lifecycle status (pending, confirmed, cancelled, delivered, refunded)",
    )
    payment_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="Payment lifecycle status (pending, paid, failed, refunded)",
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Client-provided idempotency key for duplicate request prevention",
    )
    source_cart_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="Source cart identifier for idempotency retry scenarios",
    )
    request_fingerprint: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 fingerprint of canonical cart representation for idempotency",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the order was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the order was last updated",
    )

    # Table-level constraints
    __table_args__ = (
        # Enforce idempotency uniqueness per user: a nullable key must
        # remain supported, so multiple NULL keys per user are allowed
        # (NULL != NULL in SQL unique constraints).
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_order_user_idempotency_key",
        ),
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
    )
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        foreign_keys="OrderItem.order_id",
        cascade="all, delete-orphan",
    )
    subitems: Mapped[List["OrderSubitem"]] = relationship(
        "OrderSubitem",
        back_populates="order",
        foreign_keys="OrderSubitem.order_id",
        cascade="all, delete-orphan",
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="order",
        foreign_keys="Payment.order_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Order(order_id={self.order_id}, user_id={self.user_id}, status={self.status})>"


class OrderItem(Base):
    """Order item model.

    Represents a single line item in an order, referencing a product
    with a price snapshot taken at order time. Prices are never trusted
    from the client; they are always snapshotted from the product record.
    """

    __tablename__ = "order_items"

    order_item_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique order item identifier",
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent order identifier",
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("products.product_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Referenced product identifier",
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("sellers.seller_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Seller fulfilling this item",
    )
    product_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Product name snapshot at order time",
    )
    product_sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Product SKU snapshot at order time",
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Positive integer quantity of the product",
    )
    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Unit price snapshot at order time",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the item was added to the order",
    )

    # Table-level constraints
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="chk_order_item_quantity_positive",
        ),
    )

    # Relationships
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="items",
        foreign_keys=[order_id],
    )
    product: Mapped[Product] = relationship(
        "Product",
        foreign_keys=[product_id],
    )
    seller: Mapped[Seller] = relationship(
        "Seller",
        foreign_keys=[seller_id],
    )

    def __repr__(self) -> str:
        return f"<OrderItem(order_item_id={self.order_item_id}, order_id={self.order_id}, product_id={self.product_id})>"


class OrderSubitem(Base):
    """Order subitem model.

    Represents a seller-specific group within an order. Each sub-item
    aggregates all order items belonging to one seller for independent
    accounting and commission tracking.
    """

    __tablename__ = "order_subitems"

    order_subitem_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique order subitem identifier",
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent order identifier",
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("sellers.seller_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Seller receiving this sub-order",
    )
    subtotal: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Sum of order item line totals for this seller",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="Sub-order lifecycle status (pending, confirmed, cancelled, delivered, refunded)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the sub-item was created",
    )

    # Table-level constraints
    __table_args__ = (
        # One sub-order per seller per order
        UniqueConstraint(
            "order_id",
            "seller_id",
            name="uq_order_subitem_order_seller",
        ),
    )

    # Relationships
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="subitems",
        foreign_keys=[order_id],
    )
    seller: Mapped[Seller] = relationship(
        "Seller",
        foreign_keys=[seller_id],
    )

    def __repr__(self) -> str:
        return f"<OrderSubitem(order_subitem_id={self.order_subitem_id}, order_id={self.order_id}, seller_id={self.seller_id})>"


class Payment(Base):
    """Payment model.

    Represents a simulated payment associated with an order. Payment
    processing is simulated; no real payment provider integration.
    """

    __tablename__ = "payments"

    payment_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique payment identifier",
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent order identifier",
    )
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Payment amount",
    )
    method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Payment method (e.g., simulated)",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="Payment lifecycle status (pending, paid, failed, refunded)",
    )
    transaction_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Simulated transaction reference",
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the payment was processed",
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Client-provided idempotency key for duplicate payment prevention",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the payment was created",
    )

    # Table-level constraints
    __table_args__ = (
        # Prevent duplicate payment attempts for the same order with
        # the same idempotency key. Null keys are allowed multiple times
        # (NULL != NULL in SQL unique constraints).
        UniqueConstraint(
            "order_id",
            "idempotency_key",
            name="uq_payment_order_idempotency_key",
        ),
    )

    # Relationships
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="payments",
        foreign_keys=[order_id],
    )

    def __repr__(self) -> str:
        return f"<Payment(payment_id={self.payment_id}, order_id={self.order_id}, status={self.status})>"


class Commission(Base):
    """Commission model.

    Represents a commission payment to a seller for a seller-specific
    order subitem. The amount is the authoritative commission value
    calculated from the subitem subtotal.
    """

    __tablename__ = "commissions"

    commission_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique commission identifier",
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("sellers.seller_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Seller receiving the commission",
    )
    order_subitem_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("order_subitems.order_subitem_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Sub-order generating the commission",
    )
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Commission amount (authoritative financial record)",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="Commission payment status (pending, paid)",
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the commission was paid to the seller",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the commission was created",
    )

    # Table-level constraints
    __table_args__ = (
        # MVP creates one commission per seller suborder
        UniqueConstraint(
            "order_subitem_id",
            name="uq_commission_order_subitem",
        ),
    )

    # Relationships
    seller: Mapped[Seller] = relationship(
        "Seller",
        foreign_keys=[seller_id],
    )
    order_subitem: Mapped["OrderSubitem"] = relationship(
        "OrderSubitem",
        foreign_keys=[order_subitem_id],
    )

    def __repr__(self) -> str:
        return f"<Commission(commission_id={self.commission_id}, seller_id={self.seller_id}, amount={self.amount})>"
