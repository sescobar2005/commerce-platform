"""Product model for Plataforma de Comercio.

Represents a product listed in a seller's store. A product belongs
to one store and one category, and tracks inventory and pricing.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.category import Category
from src.core.models.store import Store


class Product(Base):
    """Product model.

    Represents a product listed in a seller's store. Each product
    belongs to exactly one store and one category, and tracks
    inventory levels and pricing information.
    """

    __tablename__ = "products"

    product_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique product identifier",
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("stores.store_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owning store identifier",
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("categories.category_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Category identifier",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Product display name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
        comment="Product description",
    )
    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Product selling price",
    )
    cost: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.0,
        comment="Product cost for margin calculation",
    )
    sku: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Stock keeping unit identifier",
    )
    stock: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="Current inventory quantity",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the product is active and visible",
    )
    images_urls: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        comment="Product image URLs stored as JSON array",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the product was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the product was last updated",
    )

    # Relationships
    store: Mapped[Store] = relationship(
        "Store",
        back_populates="products",
        foreign_keys=[store_id],
    )
    category: Mapped[Category] = relationship(
        "Category",
        back_populates="products",
        foreign_keys=[category_id],
    )

    def __repr__(self) -> str:
        return f"<Product(product_id={self.product_id}, name={self.name}, sku={self.sku})>"
