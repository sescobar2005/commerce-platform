"""Unit tests for JWT token service.

Tests use temporary RSA keys generated in-memory.
No production credentials or private keys are used.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import JWTError, jwt

from src.core.config import settings
from src.core.security.jwt import JWTService, TokenType


def _generate_rsa_keypair() -> tuple[str, str]:
    """Generate a temporary RSA key pair for testing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


class TestJWTServiceAccessToken:
    """Tests for access token generation and validation."""

    def setup_method(self):
        private_pem, public_pem = _generate_rsa_keypair()
        self.private_key_path = tempfile.mktemp(suffix=".pem")
        self.public_key_path = tempfile.mktemp(suffix=".pem")
        Path(self.private_key_path).write_text(private_pem)
        Path(self.public_key_path).write_text(public_pem)

        settings.JWT_PRIVATE_KEY_PATH = self.private_key_path
        settings.JWT_PUBLIC_KEY_PATH = self.public_key_path
        self.service = JWTService()

    def teardown_method(self):
        import os

        if os.path.exists(self.private_key_path):
            os.unlink(self.private_key_path)
        if os.path.exists(self.public_key_path):
            os.unlink(self.public_key_path)

    def test_access_token_returns_string(self):
        """create_access_token should return a non-empty string."""
        token = self.service.create_access_token("user123", "testuser", "user")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_required_claims(self):
        """Access token should contain sub, username, role, iat, exp, type."""
        token = self.service.create_access_token("user123", "testuser", "user")
        payload = self.service.verify_access_token(token)
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["role"] == "user"
        assert payload["type"] == "access"
        assert "iat" in payload
        assert "exp" in payload

    def test_access_token_has_future_expiration(self):
        """Access token expiration should be after issued-at time."""
        token = self.service.create_access_token("user123", "testuser", "user")
        payload = self.service.verify_access_token(token)
        assert payload["exp"] > payload["iat"]

    def test_access_token_rejected_as_refresh(self):
        """Access token should be rejected when verified as refresh token."""
        token = self.service.create_access_token("user123", "testuser", "user")
        with pytest.raises(JWTError):
            self.service.verify_refresh_token(token)


class TestJWTServiceRefreshToken:
    """Tests for refresh token generation and validation."""

    def setup_method(self):
        private_pem, public_pem = _generate_rsa_keypair()
        self.private_key_path = tempfile.mktemp(suffix=".pem")
        self.public_key_path = tempfile.mktemp(suffix=".pem")
        Path(self.private_key_path).write_text(private_pem)
        Path(self.public_key_path).write_text(public_pem)

        settings.JWT_PRIVATE_KEY_PATH = self.private_key_path
        settings.JWT_PUBLIC_KEY_PATH = self.public_key_path
        self.service = JWTService()

    def teardown_method(self):
        import os

        if os.path.exists(self.private_key_path):
            os.unlink(self.private_key_path)
        if os.path.exists(self.public_key_path):
            os.unlink(self.public_key_path)

    def test_refresh_token_returns_string(self):
        """create_refresh_token should return a non-empty string."""
        token = self.service.create_refresh_token("user123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_refresh_token_contains_required_claims(self):
        """Refresh token should contain sub, iat, exp, type."""
        token = self.service.create_refresh_token("user123")
        payload = self.service.verify_refresh_token(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
        assert "iat" in payload
        assert "exp" in payload

    def test_refresh_token_has_future_expiration(self):
        """Refresh token expiration should be after issued-at time."""
        token = self.service.create_refresh_token("user123")
        payload = self.service.verify_refresh_token(token)
        assert payload["exp"] > payload["iat"]

    def test_refresh_token_rejected_as_access(self):
        """Refresh token should be rejected when verified as access token."""
        token = self.service.create_refresh_token("user123")
        with pytest.raises(JWTError):
            self.service.verify_access_token(token)


class TestJWTServiceSecurity:
    """Tests for JWT security properties."""

    def setup_method(self):
        private_pem, public_pem = _generate_rsa_keypair()
        self.private_key_path = tempfile.mktemp(suffix=".pem")
        self.public_key_path = tempfile.mktemp(suffix=".pem")
        Path(self.private_key_path).write_text(private_pem)
        Path(self.public_key_path).write_text(public_pem)

        settings.JWT_PRIVATE_KEY_PATH = self.private_key_path
        settings.JWT_PUBLIC_KEY_PATH = self.public_key_path
        self.service = JWTService()

    def teardown_method(self):
        import os

        if os.path.exists(self.private_key_path):
            os.unlink(self.private_key_path)
        if os.path.exists(self.public_key_path):
            os.unlink(self.public_key_path)

    def test_tampered_token_rejected(self):
        """Tampered token should be rejected."""
        token = self.service.create_access_token("user123", "testuser", "user")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            self.service.verify_access_token(tampered)

    def test_wrong_key_rejected(self):
        """Token signed with different key should be rejected."""
        other_private, other_public = _generate_rsa_keypair()
        other_private_path = tempfile.mktemp(suffix=".pem")
        other_public_path = tempfile.mktemp(suffix=".pem")
        Path(other_private_path).write_text(other_private)
        Path(other_public_path).write_text(other_public)

        other_service = JWTService.__new__(JWTService)
        other_service._private_key = other_private
        other_service._public_key = other_public

        token = other_service.create_access_token("user123", "testuser", "user")
        with pytest.raises(JWTError):
            self.service.verify_access_token(token)

        # Cleanup
        if os.path.exists(other_private_path):
            os.unlink(other_private_path)
        if os.path.exists(other_public_path):
            os.unlink(other_public_path)

    def test_malformed_token_rejected(self):
        """Malformed token should be rejected."""
        with pytest.raises(JWTError):
            self.service.verify_access_token("not.a.valid.token")

    def test_empty_token_rejected(self):
        """Empty token should be rejected."""
        with pytest.raises(JWTError):
            self.service.verify_access_token("")

    def test_access_and_refresh_tokens_are_different(self):
        """Access and refresh tokens for same user should be different."""
        access_token = self.service.create_access_token("user123", "testuser", "user")
        refresh_token = self.service.create_refresh_token("user123")
        assert access_token != refresh_token


class TestJWTServiceConfiguration:
    """Tests for JWT service configuration validation."""

    def setup_method(self):
        private_pem, public_pem = _generate_rsa_keypair()
        self.private_key_path = tempfile.mktemp(suffix=".pem")
        self.public_key_path = tempfile.mktemp(suffix=".pem")
        Path(self.private_key_path).write_text(private_pem)
        Path(self.public_key_path).write_text(public_pem)

        settings.JWT_PRIVATE_KEY_PATH = self.private_key_path
        settings.JWT_PUBLIC_KEY_PATH = self.public_key_path

    def teardown_method(self):
        import os

        if os.path.exists(self.private_key_path):
            os.unlink(self.private_key_path)
        if os.path.exists(self.public_key_path):
            os.unlink(self.public_key_path)

    def test_missing_private_key_path_raises(self):
        """JWTService should raise ValueError when private key path is missing."""
        original_path = settings.JWT_PRIVATE_KEY_PATH
        settings.JWT_PRIVATE_KEY_PATH = ""
        try:
            with pytest.raises(ValueError):
                JWTService()
        finally:
            settings.JWT_PRIVATE_KEY_PATH = original_path

    def test_missing_public_key_path_raises(self):
        """JWTService should raise ValueError when public key path is missing."""
        original_path = settings.JWT_PUBLIC_KEY_PATH
        settings.JWT_PUBLIC_KEY_PATH = ""
        try:
            with pytest.raises(ValueError):
                JWTService()
        finally:
            settings.JWT_PUBLIC_KEY_PATH = original_path

    def test_missing_private_key_file_raises(self):
        """JWTService should raise FileNotFoundError when private key file missing."""
        original_path = settings.JWT_PRIVATE_KEY_PATH
        settings.JWT_PRIVATE_KEY_PATH = "/nonexistent/private.pem"
        try:
            with pytest.raises(FileNotFoundError):
                JWTService()
        finally:
            settings.JWT_PRIVATE_KEY_PATH = original_path

    def test_missing_public_key_file_raises(self):
        """JWTService should raise FileNotFoundError when public key file missing."""
        original_path = settings.JWT_PUBLIC_KEY_PATH
        settings.JWT_PUBLIC_KEY_PATH = "/nonexistent/public.pem"
        try:
            with pytest.raises(FileNotFoundError):
                JWTService()
        finally:
            settings.JWT_PUBLIC_KEY_PATH = original_path
