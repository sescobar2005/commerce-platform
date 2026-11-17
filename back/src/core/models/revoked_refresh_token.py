"""Revoked refresh token model for Plataforma de Comercio.

Tracks revoked refresh token identifiers (jti) to prevent reuse after logout.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.core.models.user import User


class RevokedRefreshToken(Base):
    """Revoked refresh token model.

    Tracks revoked refresh token identifiers (jti) to prevent reuse
    after logout. Each revoked token is linked to the user who owned it
    and records when it was revoked and when it would have expired
    (for cleanup purposes).
    """

    __tablename__ = "revoked_refresh_tokens"

    jti: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        comment="Unique JWT identifier of the revoked refresh token",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user identifier of the revoked token",
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the refresh token was revoked",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timestamp when the refresh token would have expired",
    )

    # Relationship to User (many-to-1)
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
    )

    def __repr__(self) -> str:
        return f"<RevokedRefreshToken(jti={self.jti}, user_id={self.user_id})>"
