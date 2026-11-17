"""Unit tests for authentication dependencies.

Tests use mocked JWTService and database session - no live database required.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from src.core.auth.dependencies import get_current_user
from src.core.security.jwt import JWTService
from src.core.security.password import PasswordService
from src.core.security.schemas import UserResponse


class TestGetCurrentUser:
    """Tests for the get_current_user dependency."""

    def setup_method(self):
        self.password_service = PasswordService()
        self.jwt_service = MagicMock()
        self.mock_db = MagicMock()

    def test_successful_authentication(self):
        """Valid access token returns authenticated user."""
        credentials = MagicMock()
        credentials.credentials = "valid_access_token"
        credentials.scheme = "Bearer"

        mock_user = MagicMock()
        mock_user.user_id = "user-123"
        mock_user.username = "johndoe"
        mock_user.email = "john@example.com"
        mock_user.is_seller = False
        mock_user.is_verified = False
        mock_user.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        self.jwt_service.verify_access_token.return_value = {
            "sub": "user-123",
            "username": "johndoe",
            "role": "user",
            "type": "access",
        }

        result = get_current_user(credentials, self.mock_db, self.jwt_service)

        assert result.user_id == "user-123"
        assert result.username == "johndoe"
        assert result.email == "john@example.com"
        assert result.is_seller is False
        assert result.is_verified is False

        self.jwt_service.verify_access_token.assert_called_once_with("valid_access_token")
        self.mock_db.query.return_value.filter.return_value.first.assert_called_once()

    def test_missing_authorization_header_raises_401(self):
        """Missing credentials should raise 401."""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(None, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Missing or invalid" in exc_info.value.detail

    def test_invalid_bearer_format_raises_401(self):
        """Non-Bearer scheme should raise 401."""
        credentials = MagicMock()
        credentials.credentials = "token123"
        credentials.scheme = "Basic"

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Missing or invalid" in exc_info.value.detail

    def test_invalid_jwt_signature_raises_401(self):
        """Invalid JWT signature should raise 401."""
        credentials = MagicMock()
        credentials.credentials = "invalid_token"
        credentials.scheme = "Bearer"

        self.jwt_service.verify_access_token.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_access_token_raises_401(self):
        """Expired access token should raise 401."""
        credentials = MagicMock()
        credentials.credentials = "expired_token"
        credentials.scheme = "Bearer"

        self.jwt_service.verify_access_token.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in exc_info.value.detail.lower()

    def test_refresh_token_rejected_as_access_token(self):
        """Refresh token presented as access token should raise 401."""
        credentials = MagicMock()
        credentials.credentials = "refresh_token_value"
        credentials.scheme = "Bearer"

        self.jwt_service.verify_access_token.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: expected access",
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token type" in exc_info.value.detail

    def test_malformed_jwt_raises_401(self):
        """Malformed JWT should raise 401."""
        credentials = MagicMock()
        credentials.credentials = "not.a.valid.token"
        credentials.scheme = "Bearer"

        self.jwt_service.verify_access_token.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_subject_claim_raises_401(self):
        """Token without subject claim should raise 401."""
        credentials = MagicMock()
        credentials.credentials = "token_without_sub"
        credentials.scheme = "Bearer"

        self.jwt_service.verify_access_token.return_value = {
            "username": "johndoe",
            "role": "user",
            "type": "access",
        }

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "missing subject" in exc_info.value.detail.lower()

    def test_nonexistent_user_raises_401(self):
        """Nonexistent user should raise 401."""
        credentials = MagicMock()
        credentials.credentials = "valid_access_token"
        credentials.scheme = "Bearer"

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        self.jwt_service.verify_access_token.return_value = {
            "sub": "nonexistent_user",
            "username": "nonexistent",
            "role": "user",
            "type": "access",
        }

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, self.mock_db, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User not found" in exc_info.value.detail

    def test_database_error_raises_500(self):
        """Database error should raise 500."""
        credentials = MagicMock()
        credentials.credentials = "valid_access_token"
        credentials.scheme = "Bearer"

        self.mock_db.query.return_value.filter.return_value.first.side_effect = Exception(
            "DB connection failed"
        )

        self.jwt_service.verify_access_token.return_value = {
            "sub": "user-123",
            "username": "johndoe",
            "role": "user",
            "type": "access",
        }

        with pytest.raises(Exception):
            get_current_user(credentials, self.mock_db, self.jwt_service)

    def test_response_excludes_password_hash(self):
        """UserResponse should not include password_hash."""
        credentials = MagicMock()
        credentials.credentials = "valid_access_token"
        credentials.scheme = "Bearer"

        mock_user = MagicMock()
        mock_user.user_id = "user-123"
        mock_user.username = "johndoe"
        mock_user.email = "john@example.com"
        mock_user.is_seller = False
        mock_user.is_verified = False
        mock_user.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.jwt_service.verify_access_token.return_value = {
            "sub": "user-123",
            "username": "johndoe",
            "role": "user",
            "type": "access",
        }

        result = get_current_user(credentials, self.mock_db, self.jwt_service)

        data = result.model_dump()
        assert "password_hash" not in data
        assert "password" not in data

    def test_no_sensitive_token_in_response(self):
        """Response should not contain the raw JWT token."""
        credentials = MagicMock()
        credentials.credentials = "secret_token_value"
        credentials.scheme = "Bearer"

        mock_user = MagicMock()
        mock_user.user_id = "user-123"
        mock_user.username = "johndoe"
        mock_user.email = "john@example.com"
        mock_user.is_seller = False
        mock_user.is_verified = False
        mock_user.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.jwt_service.verify_access_token.return_value = {
            "sub": "user-123",
            "username": "johndoe",
            "role": "user",
            "type": "access",
        }

        result = get_current_user(credentials, self.mock_db, self.jwt_service)

        data = result.model_dump()
        assert "secret_token_value" not in str(data)
        assert "access_token" not in data
        assert "refresh_token" not in data