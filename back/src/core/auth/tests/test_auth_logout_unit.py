"""Unit tests for logout endpoint.

Tests use mocked database sessions, JWTService, and TokenRevocationService -
no live database required.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from src.core.auth.router import logout
from src.core.security.jwt import JWTService
from src.core.security.password import PasswordService
from src.core.security.schemas import TokenRefreshRequest, UserResponse


class TestLogoutEndpoint:
    """Tests for the logout endpoint."""

    def setup_method(self):
        self.password_service = PasswordService()
        self.jwt_service = MagicMock()
        self.mock_db = MagicMock()

    def test_successful_logout(self):
        """Successful logout should revoke the refresh token."""
        request = TokenRefreshRequest(refresh_token="valid_refresh_token")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid_access_token"
        )

        self.jwt_service.verify_access_token.return_value = {
            "sub": "user-123",
            "username": "johndoe",
            "role": "user",
            "type": "access",
        }

        self.jwt_service.verify_refresh_token.return_value = {
            "sub": "user-123",
            "jti": "test-jti-123",
            "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 7,
            "type": "refresh",
        }

        # Mock: first query returns user (user lookup), second returns None (not revoked)
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(user_id="user-123", username="johndoe"),
            None,  # Revoked token lookup - not found (not yet revoked)
        ]

        result = logout(request, credentials, self.mock_db, self.jwt_service)

        assert result == {"message": "Successfully logged out"}
        self.jwt_service.verify_access_token.assert_called_once()
        self.jwt_service.verify_refresh_token.assert_called()
        assert self.jwt_service.verify_refresh_token.call_count == 2

        # Verify revocation was attempted (add + commit)
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_invalid_refresh_token_raises_401(self):
        """Invalid refresh token should raise 401."""
        request = TokenRefreshRequest(refresh_token="invalid_token")

        current_user = UserResponse(
            user_id="user-123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        self.jwt_service.verify_access_token.return_value = {
            "sub": "user-123",
            "username": "johndoe",
            "role": "user",
            "type": "access",
        }

        self.jwt_service.verify_refresh_token.side_effect = ValueError(
            "Invalid signature"
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid_access_token"
        )

        with pytest.raises(HTTPException) as exc_info:
            logout(request, credentials, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid or expired refresh token" in exc_info.value.detail

    def test_expired_refresh_token_raises_401(self):
        """Expired refresh token should raise 401."""
        request = TokenRefreshRequest(refresh_token="expired_token")

        current_user = UserResponse(
            user_id="user-123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        self.jwt_service.verify_access_token.return_value = {
            "sub": "user-123",
            "username": "johndoe",
            "role": "user",
            "type": "access",
        }

        self.jwt_service.verify_refresh_token.side_effect = ValueError(
            "Token has expired"
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid_access_token"
        )

        with pytest.raises(HTTPException) as exc_info:
            logout(request, credentials, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_belongs_to_another_user_raises_403(self):
        """Refresh token belonging to another user should raise 403."""
        request = TokenRefreshRequest(refresh_token="valid_refresh_token")

        current_user = UserResponse(
            user_id="user-123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        self.jwt_service.verify_access_token.return_value = {
            "sub": "user-123",
            "username": "johndoe",
            "role": "user",
            "type": "access",
        }

        self.jwt_service.verify_refresh_token.return_value = {
            "sub": "user-456",  # Different user
            "jti": "test-jti-456",
            "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 7,
            "type": "refresh",
        }

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid_access_token"
        )

        with pytest.raises(HTTPException) as exc_info:
            logout(request, credentials, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "does not belong to the authenticated user" in exc_info.value.detail

    def test_repeated_logout_is_idempotent(self):
        """Repeated logout of the same token should succeed (idempotent)."""
        request = TokenRefreshRequest(refresh_token="already_revoked_token")

        current_user = UserResponse(
            user_id="user-123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        self.jwt_service.verify_access_token.return_value = {
            "sub": "user-123",
            "username": "johndoe",
            "role": "user",
            "type": "access",
        }

        self.jwt_service.verify_refresh_token.return_value = {
            "sub": "user-123",
            "jti": "already_revoked_jti",
            "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 7,
            "type": "refresh",
        }

        # Mock: first query returns user, second returns existing revoked token
        existing = MagicMock()
        existing.jti = "already_revoked_jti"
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(user_id="user-123", username="johndoe"),  # User lookup
            existing,  # Revoked token lookup - already revoked
        ]

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid_access_token"
        )

        result = logout(request, credentials, self.mock_db, self.jwt_service)

        assert result == {"message": "Successfully logged out"}
        # Should not add anything new since already revoked
        self.mock_db.add.assert_not_called()
        self.mock_db.commit.assert_not_called()


class TestLogoutInputValidation:
    """Tests for logout input validation."""

    def test_empty_refresh_token_rejected(self):
        """Empty refresh token should be rejected by Pydantic validation."""
        with pytest.raises(ValueError):
            TokenRefreshRequest(refresh_token="")