"""Seller model for Plataforma de Comercio.

Represents a registered seller who can operate stores and sell products.
A seller is linked 1:1 to a User account.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.user import User


class Seller(Base):
    """Seller model.

    Represents a verified seller account linked 1:1 to a User.
    Seller-specific business data is stored here; authentication
    and profile data lives in the User model.
    """

    __tablename__ = "sellers"

    seller_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique seller identifier, links 1:1 to users.user_id",
    )
    store_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Display name of the seller's store",
    )
    business_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Legal business name",
    )
    tax_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Tax identification number",
    )
    payment_info_json: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        comment="Simulated payment information stored as JSON",
    )
    bank_account: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Bank account identifier for payouts",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the seller's identity is verified",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the seller was created",
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of the seller's last login",
    )

    # Relationship to User (1:1)
    user: Mapped[User] = relationship(
        "User",
        back_populates="seller",
        foreign_keys=[seller_id],
    )

    # Relationship to Stores (1:many)
    stores: Mapped[list["Store"]] = relationship(
        "Store",
        back_populates="seller",
        foreign_keys="Store.seller_id",
    )

    def __repr__(self) -> str:
        return f"<Seller(seller_id={self.seller_id}, store_name={self.store_name})>"
