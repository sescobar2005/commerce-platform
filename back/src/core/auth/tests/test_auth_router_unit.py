"""Unit tests for authentication router.

Tests use mocked database sessions and PasswordService - no live database required.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.core.auth.router import register
from src.core.models.user import User
from src.core.security.password import PasswordService
from src.core.security.schemas import UserRegisterRequest, UserRegisterResponse


class TestRegisterEndpoint:
    """Tests for the user registration endpoint."""

    def setup_method(self):
        self.password_service = PasswordService()
        self.mock_db = MagicMock()

    def test_successful_registration(self):
        """Successful registration should create user and return response."""
        request = UserRegisterRequest(
            username="johndoe",
            email="john@example.com",
            password="SecurePass123",
        )

        # Mock no existing user
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        # Configure db.refresh to set attributes on the user object (like real SQLAlchemy)
        def refresh_side_effect(user):
            user.user_id = "user-123"
            user.created_at = datetime(2024, 1, 1, 12, 0, 0)

        self.mock_db.add.return_value = None
        self.mock_db.commit.return_value = None
        self.mock_db.refresh.side_effect = refresh_side_effect

        result = register(request, self.mock_db, self.password_service)

        assert result.user_id == "user-123"
        assert result.username == "johndoe"
        assert result.email == "john@example.com"
        assert result.is_seller is False
        assert result.is_verified is False

        # Verify password was hashed (not plaintext in response)
        assert not hasattr(result, "password_hash")

        # Verify db operations
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

        # Verify the user added has a hashed password
        added_user = self.mock_db.add.call_args[0][0]
        assert added_user.password_hash != "SecurePass123"
        assert added_user.password_hash.startswith("$argon2id$")

    def test_duplicate_username_raises_conflict(self):
        """Duplicate username should raise 409 Conflict."""
        request = UserRegisterRequest(
            username="existing_user",
            email="new@example.com",
            password="SecurePass123",
        )

        # Mock existing user with same username
        mock_user = MagicMock()
        mock_user.username = "existing_user"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(HTTPException) as exc_info:
            register(request, self.mock_db, self.password_service)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already registered" in exc_info.value.detail
        self.mock_db.commit.assert_not_called()

    def test_duplicate_email_raises_conflict(self):
        """Duplicate email should raise 409 Conflict."""
        request = UserRegisterRequest(
            username="new_user",
            email="existing@example.com",
            password="SecurePass123",
        )

        # Mock no existing user with username, but existing with email
        mock_email_user = MagicMock()
        mock_email_user.email = "existing@example.com"

        # First query (username check) returns None
        # Second query (email check) returns existing user
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,
            mock_email_user,
        ]

        with pytest.raises(HTTPException) as exc_info:
            register(request, self.mock_db, self.password_service)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already registered" in exc_info.value.detail
        self.mock_db.commit.assert_not_called()

    def test_integrity_error_rolls_back(self):
        """IntegrityError should trigger rollback and 409 Conflict."""
        request = UserRegisterRequest(
            username="johndoe",
            email="john@example.com",
            password="SecurePass123",
        )

        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        # IntegrityError requires (statement, params, orig) arguments
        err = IntegrityError("statement", {}, Exception("duplicate key"))
        self.mock_db.commit.side_effect = err

        with pytest.raises(HTTPException) as exc_info:
            register(request, self.mock_db, self.password_service)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        self.mock_db.rollback.assert_called_once()


class TestUserResponseSerialization:
    """Tests for UserResponse serialization excludes sensitive fields."""

    def test_user_register_response_excludes_password_hash(self):
        """UserRegisterResponse should not include password_hash."""
        response = UserRegisterResponse(
            user_id="user-123",
            username="johndoe",
            email="john@example.com",
            is_seller=False,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        # Verify UserRegisterResponse does not expose password_hash
        data = response.model_dump()
        assert "password_hash" not in data
        assert data["username"] == "johndoe"
        assert data["email"] == "john@example.com"
