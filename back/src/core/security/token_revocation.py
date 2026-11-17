"""Token revocation service for Plataforma de Comercio.

Provides revocation and lookup of revoked refresh tokens using JWT IDs (jti).
Designed for use by the logout endpoint and future refresh endpoint.
"""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.models.revoked_refresh_token import RevokedRefreshToken
from src.core.security.jwt import JWTService


class TokenRevocationService:
    """Service for revoking and checking revoked refresh tokens.

    Provides methods to revoke a refresh token by storing its JWT ID (jti)
    in the database, and to check whether a given jti has been revoked.

    All methods are idempotent where appropriate: revoking an already-revoked
    token is a no-op rather than an error.
    """

    def __init__(self, db: Session, jwt_service: JWTService):
        """Initialize the token revocation service.

        Args:
            db: SQLAlchemy database session.
            jwt_service: JWT service instance for token verification.
        """
        self.db = db
        self.jwt_service = jwt_service

    def revoke_refresh_token(self, refresh_token: str) -> None:
        """Revoke a refresh token by storing its JTI in the revocation table.

        Validates the token before revocation: checks signature, expiration,
        token type, and required claims. If the token is already revoked,
        this is a no-op (idempotent).

        Args:
            refresh_token: The refresh token string to revoke.

        Raises:
            ValueError: If the token is invalid, expired, malformed, or not
                a refresh token.
        """
        # Validate the token before revoking
        payload = self.jwt_service.verify_refresh_token(refresh_token)

        jti = payload.get("jti")
        if not jti:
            raise ValueError("Refresh token missing jti claim")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Refresh token missing subject claim")

        exp = payload.get("exp")
        if not exp:
            raise ValueError("Refresh token missing expiration claim")

        # Check if already revoked (idempotent)
        existing = (
            self.db.query(RevokedRefreshToken)
            .filter(RevokedRefreshToken.jti == jti)
            .first()
        )
        if existing:
            return  # Already revoked, idempotent

        # Create revocation record
        revoked_token = RevokedRefreshToken(
            jti=jti,
            user_id=user_id,
            revoked_at=datetime.now(timezone.utc),
            expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
        )

        self.db.add(revoked_token)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            # Another concurrent request may have already revoked this token
            existing = (
                self.db.query(RevokedRefreshToken)
                .filter(RevokedRefreshToken.jti == jti)
                .first()
            )
            if existing:
                return  # Another request already revoked it, idempotent
            raise

    def is_token_revoked(self, jti: str) -> bool:
        """Check whether a refresh token JTI has been revoked.

        Args:
            jti: The JWT ID to check.

        Returns:
            True if the token has been revoked, False otherwise.
        """
        return (
            self.db.query(RevokedRefreshToken)
            .filter(RevokedRefreshToken.jti == jti)
            .first()
            is not None
        )
