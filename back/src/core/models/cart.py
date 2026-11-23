"""Cart models for Plataforma de Comercio.

Represents shopping carts and cart items for the product catalog.
Carts belong to users and contain items referencing products with
price snapshots taken at time of addition.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
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
from src.core.models.user import User


class Cart(Base):
    """Cart model.

    Represents a shopping cart belonging to exactly one user.
    A user may have multiple carts over time, but business rules
    enforce at most one active cart per user at the application level.

    Attributes:
        cart_id: Unique cart identifier.
        user_id: Foreign key to the owning user.
        created_at: Timestamp when the cart was created.
        last_updated_at: Timestamp when the cart was last modified.
        expires_at: Optional timestamp when the cart expires.
    """

    __tablename__ = "carts"

    cart_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique cart identifier",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owning user identifier",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the cart was created",
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the cart was last updated",
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Optional timestamp when the cart expires",
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
    )
    items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        foreign_keys="CartItem.cart_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Cart(cart_id={self.cart_id}, user_id={self.user_id})>"


class CartItem(Base):
    """Cart item model.

    Represents a single line item in a shopping cart, referencing
    an existing product with a quantity and a price snapshot taken
    at the time of addition. Prices are never trusted from the client;
    they are always snapshotted from the product record.

    Attributes:
        cart_item_id: Unique cart item identifier.
        cart_id: Foreign key to the parent cart.
        product_id: Foreign key to the referenced product.
        quantity: Positive integer quantity of the product.
        price_at_time: Price snapshot of the product at addition time.
        created_at: Timestamp when the item was added to the cart.
    """

    __tablename__ = "cart_items"

    cart_item_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique cart item identifier",
    )
    cart_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("carts.cart_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent cart identifier",
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("products.product_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Referenced product identifier",
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Positive integer quantity of the product",
    )
    price_at_time: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Price snapshot of the product at addition time",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the item was added to the cart",
    )

    # Table-level constraints
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="chk_cart_item_quantity_positive",
        ),
        # Prevent duplicate cart items for the same product in one cart
        # A product can appear only once per cart; quantity is updated instead
        UniqueConstraint(
            "cart_id",
            "product_id",
            name="uq_cart_item_cart_product",
        ),
    )

    # Relationships
    cart: Mapped[Cart] = relationship(
        "Cart",
        back_populates="items",
        foreign_keys=[cart_id],
    )
    product: Mapped[Product] = relationship(
        "Product",
        foreign_keys=[product_id],
    )

    def __repr__(self) -> str:
        return f"<CartItem(cart_item_id={self.cart_item_id}, product_id={self.product_id}, quantity={self.quantity})>"
