"""Unit tests for token revocation service.

Tests use mocked database sessions and JWTService - no live database required.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from src.core.security.jwt import JWTService
from src.core.security.token_revocation import TokenRevocationService


class TestTokenRevocationService:
    """Tests for token revocation service."""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.jwt_service = MagicMock()
        self.service = TokenRevocationService(self.mock_db, self.jwt_service)

    def test_revoke_valid_refresh_token(self):
        """Revoking a valid refresh token should store its JTI."""
        refresh_token = "valid_refresh_token"
        jti = "test-jti-123"
        user_id = "user-123"
        exp = int(datetime.now(timezone.utc).timestamp()) + 86400 * 7

        self.jwt_service.verify_refresh_token.return_value = {
            "sub": user_id,
            "jti": jti,
            "exp": exp,
            "type": "refresh",
        }

        # No existing revoked token
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        self.service.revoke_refresh_token(refresh_token)

        self.mock_db.add.assert_called_once()
        added_obj = self.mock_db.add.call_args[0][0]
        assert added_obj.jti == jti
        assert added_obj.user_id == user_id
        assert added_obj.revoked_at is not None
        assert added_obj.expires_at is not None
        self.mock_db.commit.assert_called_once()

    def test_revoke_already_revoked_token_is_idempotent(self):
        """Revoking an already-revoked token should be a no-op."""
        refresh_token = "already_revoked_token"
        jti = "already_revoked_jti"
        user_id = "user-123"
        exp = int(datetime.now(timezone.utc).timestamp()) + 86400 * 7

        self.jwt_service.verify_refresh_token.return_value = {
            "sub": user_id,
            "jti": jti,
            "exp": exp,
            "type": "refresh",
        }

        # Mock existing revoked token
        existing = MagicMock()
        existing.jti = jti
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing

        self.service.revoke_refresh_token(refresh_token)

        # Should not add anything new
        self.mock_db.add.assert_not_called()
        self.mock_db.commit.assert_not_called()

    def test_is_token_revoked_returns_true(self):
        """is_token_revoked should return True for revoked JTI."""
        jti = "revoked_jti"
        existing = MagicMock()
        existing.jti = jti
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing

        assert self.service.is_token_revoked(jti) is True

    def test_is_token_revoked_returns_false(self):
        """is_token_revoked should return False for non-revoked JTI."""
        jti = "not_revoked_jti"
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        assert self.service.is_token_revoked(jti) is False

    def test_invalid_jwt_signature_raises_value_error(self):
        """Revoking a token with invalid signature should raise ValueError."""
        refresh_token = "invalid_signature_token"
        self.jwt_service.verify_refresh_token.side_effect = ValueError("Invalid signature")

        with pytest.raises(ValueError, match="Invalid signature"):
            self.service.revoke_refresh_token(refresh_token)

    def test_expired_refresh_token_raises_value_error(self):
        """Revoking an expired refresh token should raise ValueError."""
        refresh_token = "expired_token"
        self.jwt_service.verify_refresh_token.side_effect = ValueError("Token has expired")

        with pytest.raises(ValueError, match="Token has expired"):
            self.service.revoke_refresh_token(refresh_token)

    def test_access_token_rejected_as_refresh_token(self):
        """Revoking an access token (wrong type) should raise ValueError."""
        refresh_token = "access_token_used_as_refresh"
        self.jwt_service.verify_refresh_token.side_effect = ValueError(
            "Invalid token type: expected refresh"
        )

        with pytest.raises(ValueError, match="Invalid token type"):
            self.service.revoke_refresh_token(refresh_token)

    def test_missing_jti_raises_value_error(self):
        """Refresh token without jti claim should raise ValueError."""
        refresh_token = "token_without_jti"
        self.jwt_service.verify_refresh_token.return_value = {
            "sub": "user-123",
            "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 7,
            "type": "refresh",
            # No jti claim
        }

        with pytest.raises(ValueError, match="missing jti claim"):
            self.service.revoke_refresh_token(refresh_token)

    def test_missing_user_id_raises_value_error(self):
        """Refresh token without subject claim should raise ValueError."""
        refresh_token = "token_without_sub"
        self.jwt_service.verify_refresh_token.return_value = {
            "jti": "some-jti",
            "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 7,
            "type": "refresh",
            # No sub claim
        }

        with pytest.raises(ValueError, match="missing subject claim"):
            self.service.revoke_refresh_token(refresh_token)

    def test_missing_expiration_raises_value_error(self):
        """Refresh token without expiration claim should raise ValueError."""
        refresh_token = "token_without_exp"
        self.jwt_service.verify_refresh_token.return_value = {
            "sub": "user-123",
            "jti": "some-jti",
            "type": "refresh",
            # No exp claim
        }

        with pytest.raises(ValueError, match="missing expiration claim"):
            self.service.revoke_refresh_token(refresh_token)

    def test_database_error_rolls_back(self):
        """Database error during revocation should trigger rollback."""
        refresh_token = "valid_refresh_token"
        jti = "test-jti-123"
        user_id = "user-123"
        exp = int(datetime.now(timezone.utc).timestamp()) + 86400 * 7

        self.jwt_service.verify_refresh_token.return_value = {
            "sub": user_id,
            "jti": jti,
            "exp": exp,
            "type": "refresh",
        }

        # No existing revoked token
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        # Simulate database error on add
        err = IntegrityError("statement", {}, Exception("db error"))
        self.mock_db.add.side_effect = err

        with pytest.raises(IntegrityError):
            self.service.revoke_refresh_token(refresh_token)

        self.mock_db.rollback.assert_called_once()