"""User model for Plataforma de Comercio.

Represents a system user who can act as a buyer and/or seller.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func, sql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class User(Base):
    """User model.

    Represents a registered user of the platform. A user can act as
    a buyer, a seller, or both. Core authentication and profile data
    is stored here; seller-specific data lives in the Seller model.
    """

    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique user identifier",
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique username for login",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique email address",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Argon2id hashed password",
    )
    is_seller: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=sql.false(),
        comment="Whether the user can operate as a seller",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=sql.false(),
        comment="Whether the user's email is verified",
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=sql.false(),
        comment="Whether the user is an administrator",
    )
    is_moderator: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=sql.false(),
        comment="Whether the user is a content moderator",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the user was created",
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of the user's last login",
    )
    preferences_json: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        comment="User preferences stored as JSON",
    )

    # Relationship to Seller (1:1)
    seller: Mapped[Optional["Seller"]] = relationship(
        "Seller",
        back_populates="user",
        foreign_keys="Seller.seller_id",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, username={self.username}, email={self.email})>"
