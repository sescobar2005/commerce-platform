"""Store model for Plataforma de Comercio.

Represents a seller's storefront. A store belongs to a single seller
and contains products.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.seller import Seller


class Store(Base):
    """Store model.

    Represents a seller's storefront. Each store belongs to exactly
    one seller and contains products managed by that seller.
    """

    __tablename__ = "stores"

    store_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique store identifier",
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("sellers.seller_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner seller identifier",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Store display name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="Store description",
    )
    slug: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False,
        index=True,
        comment="URL-friendly store identifier",
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to store logo image",
    )
    cover_image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to store cover image",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the store is active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the store was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the store was last updated",
    )

    # Relationship to Seller (many-to-1)
    seller: Mapped[Seller] = relationship(
        "Seller",
        back_populates="stores",
        foreign_keys=[seller_id],
    )

    # Relationship to Products (1:many)
    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="store",
        foreign_keys="Product.store_id",
    )

    def __repr__(self) -> str:
        return f"<Store(store_id={self.store_id}, name={self.name}, slug={self.slug})>"
