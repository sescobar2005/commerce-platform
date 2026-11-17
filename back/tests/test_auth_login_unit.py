"""Unit tests for authentication router login endpoint.

Tests use mocked database sessions, PasswordService, and JWTService -
no live database required.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.core.auth.router import login
from src.core.security.password import PasswordService
from src.core.security.jwt import JWTService
from src.core.security.schemas import UserLoginRequest


class TestLoginEndpoint:
    """Tests for the user login endpoint."""

    def setup_method(self):
        self.password_service = PasswordService()
        self.mock_db = MagicMock()

        # Mock JWTService token generation methods
        self.jwt_service = MagicMock()
        self.jwt_service.create_access_token.return_value = "access_token_123"
        self.jwt_service.create_refresh_token.return_value = "refresh_token_456"

    def test_successful_login(self):
        """Successful login should return access and refresh tokens."""
        request = UserLoginRequest(
            username="johndoe",
            password="SecurePass123",
        )

        # Mock existing user with valid password hash
        mock_user = MagicMock()
        mock_user.user_id = "user-123"
        mock_user.username = "johndoe"
        mock_user.email = "john@example.com"
        mock_user.is_seller = False
        mock_user.is_verified = False
        mock_user.password_hash = "$argon2id$v=19$m=65536,t=3,p=4$hash"
        mock_user.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_user.last_login_at = None

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock password verification
        self.password_service.verify_password = MagicMock(return_value=True)

        result = login(request, self.mock_db, self.password_service, self.jwt_service)

        assert result.access_token == "access_token_123"
        assert result.refresh_token == "refresh_token_456"
        assert result.token_type == "bearer"
        assert result.user.user_id == "user-123"
        assert result.user.username == "johndoe"
        assert result.user.email == "john@example.com"

        # Verify last_login_at was updated
        assert mock_user.last_login_at is not None

        # Verify db commit was called
        self.mock_db.commit.assert_called_once()

        # Verify token service methods were called
        self.jwt_service.create_access_token.assert_called_once_with(
            user_id="user-123",
            username="johndoe",
            role="user",
        )
        self.jwt_service.create_refresh_token.assert_called_once_with(
            user_id="user-123",
        )

    def test_incorrect_password_raises_401(self):
        """Incorrect password should return 401 without revealing account existence."""
        request = UserLoginRequest(
            username="johndoe",
            password="WrongPassword",
        )

        # Mock existing user but wrong password
        mock_user = MagicMock()
        mock_user.username = "johndoe"
        mock_user.password_hash = "$argon2id$v=19$m=65536,t=3,p=4$hash"

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.password_service.verify_password = MagicMock(return_value=False)

        with pytest.raises(HTTPException) as exc_info:
            login(request, self.mock_db, self.password_service, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid" in exc_info.value.detail

    def test_unknown_username_raises_401(self):
        """Unknown username should return 401 (same as wrong password)."""
        request = UserLoginRequest(
            username="nonexistent_user",
            password="SecurePass123",
        )

        # Mock no existing user
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.password_service.verify_password = MagicMock(return_value=False)

        with pytest.raises(HTTPException) as exc_info:
            login(request, self.mock_db, self.password_service, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid" in exc_info.value.detail

    def test_password_verify_called_once(self):
        """Password verification should be called exactly once."""
        request = UserLoginRequest(
            username="johndoe",
            password="SecurePass123",
        )

        mock_user = MagicMock()
        mock_user.username = "johndoe"
        mock_user.email = "john@example.com"
        mock_user.password_hash = "$argon2id$v=19$m=65536,t=3,p=4$hash"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.password_service.verify_password = MagicMock(return_value=True)

        login(request, self.mock_db, self.password_service, self.jwt_service)

        self.password_service.verify_password.assert_called_once_with(
            "SecurePass123", "$argon2id$v=19$m=65536,t=3,p=4$hash"
        )

    def test_last_login_at_updated_on_success(self):
        """last_login_at should be updated on successful login."""
        request = UserLoginRequest(
            username="johndoe",
            password="SecurePass123",
        )

        mock_user = MagicMock()
        mock_user.user_id = "user-123"
        mock_user.username = "johndoe"
        mock_user.email = "john@example.com"
        mock_user.is_seller = False
        mock_user.is_verified = False
        mock_user.password_hash = "$argon2id$v=19$m=65536,t=3,p=4$hash"
        mock_user.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_user.last_login_at = None

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.password_service.verify_password = MagicMock(return_value=True)

        login(request, self.mock_db, self.password_service, self.jwt_service)

        assert mock_user.last_login_at is not None
        self.mock_db.commit.assert_called_once()

    def test_db_failure_rolls_back(self):
        """Database failure should trigger rollback and 500 error."""
        request = UserLoginRequest(
            username="johndoe",
            password="SecurePass123",
        )

        mock_user = MagicMock()
        mock_user.username = "johndoe"
        mock_user.password_hash = "$argon2id$v=19$m=65536,t=3,p=4$hash"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.password_service.verify_password = MagicMock(return_value=True)
        # IntegrityError requires (statement, params, orig) arguments
        err = IntegrityError("statement", {}, Exception("db error"))
        self.mock_db.commit.side_effect = err

        with pytest.raises(HTTPException) as exc_info:
            login(request, self.mock_db, self.password_service, self.jwt_service)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        self.mock_db.rollback.assert_called_once()


class TestLoginInputValidation:
    """Tests for login input validation."""

    def setup_method(self):
        self.password_service = PasswordService()
        self.jwt_service = MagicMock()
        self.jwt_service.create_access_token.return_value = "access_token_123"
        self.jwt_service.create_refresh_token.return_value = "refresh_token_456"
        self.mock_db = MagicMock()

    def test_empty_username_rejected(self):
        """Empty username should raise ValueError via Pydantic validation."""
        with pytest.raises(ValueError):
            UserLoginRequest(username="", password="SecurePass123")

    def test_empty_password_rejected(self):
        """Empty password should raise ValueError via Pydantic validation."""
        with pytest.raises(ValueError):
            UserLoginRequest(username="johndoe", password="")

    def test_username_too_long_rejected(self):
        """Username exceeding 100 chars should raise ValueError via Pydantic validation."""
        with pytest.raises(ValueError):
            UserLoginRequest(
                username="a" * 101,
                password="SecurePass123",
            )

    def test_password_too_long_rejected(self):
        """Password exceeding 255 chars should raise ValueError via Pydantic validation."""
        with pytest.raises(ValueError):
            UserLoginRequest(
                username="johndoe",
                password="a" * 256,
            )