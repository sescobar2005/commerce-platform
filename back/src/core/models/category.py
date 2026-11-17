"""Category model for Plataforma de Comercio.

Represents a product category. Categories support a hierarchical
structure via a self-referential parent_id foreign key.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Category(Base):
    """Category model.

    Represents a product category in the catalog. Categories can be
    nested hierarchically via parent_id, enabling tree-like
    organization of products.
    """

    __tablename__ = "categories"

    category_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique category identifier",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Category display name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Category description",
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="URL-friendly category identifier",
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        String(36),
        ForeignKey("categories.category_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Parent category identifier for hierarchy",
    )
    level: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="Depth level in the category hierarchy (0 = root)",
    )
    path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
        comment="Materialized path from root to this category",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the category is active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the category was created",
    )

    # Self-referential relationship to parent category (many-to-1)
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side=[category_id],
        foreign_keys=[parent_id],
        back_populates="children",
    )

    # Relationship to child categories (1:many)
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        foreign_keys="Category.parent_id",
    )

    # Relationship to Products (1:many)
    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="category",
        foreign_keys="Product.category_id",
    )

    def __repr__(self) -> str:
        return f"<Category(category_id={self.category_id}, name={self.name}, slug={self.slug})>"
