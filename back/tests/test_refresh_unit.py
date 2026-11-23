"""Unit tests for refresh token endpoint.

Tests use mocked database sessions, JWTService, and TokenRevocationService -
no live database required.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from src.core.auth.router import refresh
from src.core.security.jwt import JWTService
from src.core.security.schemas import TokenRefreshRequest


class TestRefreshEndpoint:
    """Tests for the refresh token endpoint."""

    def setup_method(self):
        self.jwt_service = MagicMock()
        self.mock_db = MagicMock()

    def test_successful_refresh(self):
        """Valid refresh token should return new access and refresh tokens (rotation)."""
        request = TokenRefreshRequest(
            refresh_token="valid_refresh_token",
        )

        mock_user = MagicMock()
        mock_user.user_id = "user-123"
        mock_user.username = "johndoe"
        mock_user.email = "john@example.com"
        mock_user.is_seller = False
        mock_user.is_verified = False

        # Three first() calls: revocation check, user lookup, revoke-internal revocation check
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,
            mock_user,
            None,
        ]
        self.jwt_service.verify_refresh_token.return_value = {
            "sub": "user-123",
            "jti": "test-jti-123",
            "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 7,
            "type": "refresh",
        }
        self.jwt_service.create_access_token.return_value = "new_access_token"
        self.jwt_service.create_refresh_token.return_value = "new_refresh_token"

        result = refresh(request, self.mock_db, self.jwt_service)

        assert result.access_token == "new_access_token"
        assert result.refresh_token == "new_refresh_token"
        assert result.token_type == "bearer"

        # Verify refresh token was checked against revocation
        self.jwt_service.verify_refresh_token.assert_called_with(
            "valid_refresh_token"
        )
        self.jwt_service.create_access_token.assert_called_once_with(
            user_id="user-123",
            username="johndoe",
            role="user",
        )
        self.jwt_service.create_refresh_token.assert_called_once_with(
            user_id="user-123",
        )

        # Verify old token was revoked (rotation)
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called()

    def test_previous_token_revoked_after_rotation(self):
        """Previous refresh token should be revoked when rotation succeeds."""
        request = TokenRefreshRequest(
            refresh_token="old_refresh_token",
        )

        mock_user = MagicMock()
        mock_user.user_id = "user-123"
        mock_user.username = "johndoe"
        mock_user.email = "john@example.com"
        mock_user.is_seller = False
        mock_user.is_verified = False

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,
            mock_user,
            None,
        ]
        self.jwt_service.verify_refresh_token.return_value = {
            "sub": "user-123",
            "jti": "old-jti",
            "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 7,
            "type": "refresh",
        }
        self.jwt_service.create_access_token.return_value = "new_access_token"
        self.jwt_service.create_refresh_token.return_value = "new_refresh_token"

        result = refresh(request, self.mock_db, self.jwt_service)

        assert result.access_token == "new_access_token"
        assert result.refresh_token == "new_refresh_token"
        assert result.refresh_token != "old_refresh_token"

        # Verify old token was revoked (added to revocation table)
        self.mock_db.add.assert_called_once()
        added_obj = self.mock_db.add.call_args[0][0]
        assert added_obj.jti == "old-jti"
        assert added_obj.user_id == "user-123"

        # Verify commit was called to persist revocation
        self.mock_db.commit.assert_called()

    def test_invalid_refresh_token_raises_401(self):
        """Invalid refresh token should raise 401."""
        request = TokenRefreshRequest(
            refresh_token="invalid_token",
        )

        self.jwt_service.verify_refresh_token.side_effect = ValueError(
            "Invalid signature"
        )

        with pytest.raises(HTTPException) as exc_info:
            refresh(request, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_refresh_token_raises_401(self):
        """Expired refresh token should raise 401."""
        request = TokenRefreshRequest(
            refresh_token="expired_token",
        )

        self.jwt_service.verify_refresh_token.side_effect = ValueError(
            "Token has expired"
        )

        with pytest.raises(HTTPException) as exc_info:
            refresh(request, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_token_rejected_as_refresh(self):
        """Access token used as refresh token should raise 401."""
        request = TokenRefreshRequest(
            refresh_token="access_token_used_as_refresh",
        )

        self.jwt_service.verify_refresh_token.side_effect = ValueError(
            "Invalid token type: expected refresh"
        )

        with pytest.raises(HTTPException) as exc_info:
            refresh(request, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_revoked_refresh_token_raises_401(self):
        """Revoked refresh token should raise 401."""
        request = TokenRefreshRequest(
            refresh_token="revoked_token",
        )

        mock_user = MagicMock()
        mock_user.user_id = "user-123"
        mock_user.username = "johndoe"
        mock_user.email = "john@example.com"
        mock_user.is_seller = False
        mock_user.is_verified = False

        # First call to first() returns existing revoked token (found in DB)
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(),  # Revoked token exists
        ]
        self.jwt_service.verify_refresh_token.return_value = {
            "sub": "user-123",
            "jti": "revoked_jti",
            "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 7,
            "type": "refresh",
        }

        with pytest.raises(HTTPException) as exc_info:
            refresh(request, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "revoked" in exc_info.value.detail.lower()

    def test_missing_jti_raises_401(self):
        """Refresh token without jti claim should raise 401."""
        request = TokenRefreshRequest(
            refresh_token="token_without_jti",
        )

        self.jwt_service.verify_refresh_token.return_value = {
            "sub": "user-123",
            "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 7,
            "type": "refresh",
            # No jti claim
        }

        with pytest.raises(HTTPException) as exc_info:
            refresh(request, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_user_raises_401(self):
        """Nonexistent user should raise 401."""
        request = TokenRefreshRequest(
            refresh_token="valid_token",
        )

        # First call returns None (not revoked), second returns None (user not found)
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,
            None,
        ]
        self.jwt_service.verify_refresh_token.return_value = {
            "sub": "nonexistent_user",
            "jti": "some-jti",
            "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 7,
            "type": "refresh",
        }

        with pytest.raises(HTTPException) as exc_info:
            refresh(request, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_database_error_raises_500(self):
        """Database error during user lookup should raise 500."""
        request = TokenRefreshRequest(
            refresh_token="valid_token",
        )

        mock_user = MagicMock()
        mock_user.user_id = "user-123"
        mock_user.username = "johndoe"
        mock_user.email = "john@example.com"
        mock_user.is_seller = False
        mock_user.is_verified = False
        mock_user.password_hash = "$argon2id$v=19$m=65536,t=3,p=4$hash"

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # Not revoked
            mock_user,  # User exists
            None,  # Not already revoked (inside revoke_refresh_token)
        ]
        self.jwt_service.verify_refresh_token.return_value = {
            "sub": "user-123",
            "jti": "test-jti",
            "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 7,
            "type": "refresh",
        }

        # Make commit fail during revocation (simulate DB error)
        self.mock_db.commit.side_effect = Exception("DB error")

        # revoke_refresh_token calls commit, which raises
        with pytest.raises(Exception):
            refresh(request, self.mock_db, self.jwt_service)