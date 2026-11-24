"""Unit tests for authentication Pydantic schemas.

Tests do NOT require a live database or external services.
No real passwords are used in tests.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.core.security.schemas import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
    TokenResponse,
    UserResponse,
)


class TestUserRegisterRequest:
    """Tests for UserRegisterRequest schema."""

    def test_valid_registration_request(self):
        """Valid registration request should be accepted."""
        request = UserRegisterRequest(
            username="johndoe",
            email="john@example.com",
            password="SecurePass123",
        )
        assert request.username == "johndoe"
        assert request.email == "john@example.com"
        assert request.password == "SecurePass123"

    def test_missing_required_fields(self):
        """Missing required fields should raise ValidationError."""
        with pytest.raises(ValidationError):
            UserRegisterRequest()

        with pytest.raises(ValidationError):
            UserRegisterRequest(username="johndoe")

        with pytest.raises(ValidationError):
            UserRegisterRequest(username="johndoe", email="john@example.com")

    def test_invalid_email(self):
        """Invalid email format should raise ValidationError."""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                username="johndoe",
                email="not-an-email",
                password="SecurePass123",
            )

    def test_username_too_long(self):
        """Username exceeding 100 chars should raise ValidationError."""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                username="a" * 101,
                email="john@example.com",
                password="SecurePass123",
            )

    def test_password_too_long(self):
        """Password exceeding 255 chars should raise ValidationError."""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                username="johndoe",
                email="john@example.com",
                password="a" * 256,
            )

    def test_empty_username_rejected(self):
        """Empty username should raise ValidationError."""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                username="",
                email="john@example.com",
                password="SecurePass123",
            )

    def test_empty_password_rejected(self):
        """Empty password should raise ValidationError."""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                username="johndoe",
                email="john@example.com",
                password="",
            )


class TestUserRegisterResponse:
    """Tests for UserRegisterResponse schema."""

    def test_valid_registration_response(self):
        """Valid registration response should be accepted."""
        response = UserRegisterResponse(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        assert response.user_id == "user123"
        assert response.username == "johndoe"
        assert response.email == "john@example.com"
        assert response.is_seller is False
        assert response.is_verified is False


class TestUserLoginRequest:
    """Tests for UserLoginRequest schema."""

    def test_valid_login_request(self):
        """Valid login request should be accepted."""
        request = UserLoginRequest(
            username="johndoe",
            password="SecurePass123",
        )
        assert request.username == "johndoe"
        assert request.password == "SecurePass123"

    def test_missing_required_fields(self):
        """Missing required fields should raise ValidationError."""
        with pytest.raises(ValidationError):
            UserLoginRequest()

        with pytest.raises(ValidationError):
            UserLoginRequest(username="johndoe")

        with pytest.raises(ValidationError):
            UserLoginRequest(password="SecurePass123")

    def test_empty_username_rejected(self):
        """Empty username should raise ValidationError."""
        with pytest.raises(ValidationError):
            UserLoginRequest(
                username="",
                password="SecurePass123",
            )

    def test_empty_password_rejected(self):
        """Empty password should raise ValidationError."""
        with pytest.raises(ValidationError):
            UserLoginRequest(
                username="johndoe",
                password="",
            )


class TestTokenResponse:
    """Tests for TokenResponse schema."""

    def test_valid_token_response(self):
        """Valid token response should be accepted."""
        response = TokenResponse(
            access_token="access-token-123",
            refresh_token="refresh-token-456",
        )
        assert response.access_token == "access-token-123"
        assert response.refresh_token == "refresh-token-456"
        assert response.token_type == "bearer"

    def test_custom_token_type(self):
        """Custom token type should be accepted."""
        response = TokenResponse(
            access_token="access-token-123",
            refresh_token="refresh-token-456",
            token_type="Bearer",
        )
        assert response.token_type == "Bearer"

    def test_missing_required_fields(self):
        """Missing required fields should raise ValidationError."""
        with pytest.raises(ValidationError):
            TokenResponse()


class TestUserLoginResponse:
    """Tests for UserLoginResponse schema."""

    def test_valid_login_response(self):
        """Valid login response should be accepted."""
        response = UserLoginResponse(
            access_token="access-token-123",
            refresh_token="refresh-token-456",
            token_type="bearer",
            user=UserResponse(
                user_id="user123",
                username="johndoe",
                email="john@example.com",
                is_seller=False,
                is_verified=False,
                created_at=datetime(2024, 1, 1, 12, 0, 0),
            ),
        )
        assert response.access_token == "access-token-123"
        assert response.refresh_token == "refresh-token-456"
        assert response.token_type == "bearer"
        assert response.user.user_id == "user123"
        assert response.user.username == "johndoe"


class TestUserResponse:
    """Tests for UserResponse schema."""

    def test_valid_user_response(self):
        """Valid user response should be accepted."""
        response = UserResponse(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        assert response.user_id == "user123"
        assert response.username == "johndoe"
        assert response.email == "john@example.com"

    def test_user_response_no_password_hash(self):
        """UserResponse should not include password_hash field."""
        response = UserResponse(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        # Verify password_hash is not a field
        assert not hasattr(response, "password_hash")
        assert "password_hash" not in response.model_dump()

    def test_user_response_serialization(self):
        """UserResponse should serialize correctly."""
        response = UserResponse(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            is_seller=True,
            is_verified=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        data = response.model_dump()
        assert data["user_id"] == "user123"
        assert data["username"] == "johndoe"
        assert data["email"] == "john@example.com"
        assert data["is_seller"] is True
        assert data["is_verified"] is True
        assert "password_hash" not in data
