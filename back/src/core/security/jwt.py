"""JWT token service using RS256 asymmetric encryption.

Provides JWT token generation and validation using RSA key pairs.
Keys are loaded from PEM files via environment-configured paths.

Never logs private keys or complete tokens.
"""

import time
import uuid
from pathlib import Path
from typing import Any, Dict

from jose import JWTError, jwt

from src.core.config import settings


class TokenType:
    """Token type constants."""

    ACCESS = "access"
    REFRESH = "refresh"


class JWTService:
    """JWT token service using RS256.

    Signs tokens with an RSA private key and verifies with the
    corresponding RSA public key. Keys are loaded from PEM files
    via environment-configured paths.
    """

    def __init__(self) -> None:
        self._private_key = self._load_private_key()
        self._public_key = self._load_public_key()

    def _load_private_key(self) -> str:
        """Load RSA private key from PEM file.

        Returns:
            The PEM-encoded private key string.

        Raises:
            ValueError: If JWT_PRIVATE_KEY_PATH is not configured.
            FileNotFoundError: If the private key file does not exist.
        """
        key_path = settings.JWT_PRIVATE_KEY_PATH
        if not key_path:
            raise ValueError("JWT_PRIVATE_KEY_PATH is not configured")
        path = Path(key_path)
        if not path.is_file():
            raise FileNotFoundError(f"Private key file not found: {key_path}")
        return path.read_text()

    def _load_public_key(self) -> str:
        """Load RSA public key from PEM file.

        Returns:
            The PEM-encoded public key string.

        Raises:
            ValueError: If JWT_PUBLIC_KEY_PATH is not configured.
            FileNotFoundError: If the public key file does not exist.
        """
        key_path = settings.JWT_PUBLIC_KEY_PATH
        if not key_path:
            raise ValueError("JWT_PUBLIC_KEY_PATH is not configured")
        path = Path(key_path)
        if not path.is_file():
            raise FileNotFoundError(f"Public key file not found: {key_path}")
        return path.read_text()

    def create_access_token(self, user_id: str, username: str, role: str) -> str:
        """Create an access token.

        Args:
            user_id: The user identifier (sub claim).
            username: The username claim.
            role: The user role claim.

        Returns:
            A signed JWT access token string.
        """
        now = int(time.time())
        expire = now + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        payload: Dict[str, Any] = {
            "sub": user_id,
            "username": username,
            "role": role,
            "iat": now,
            "exp": expire,
            "type": TokenType.ACCESS,
        }
        return jwt.encode(payload, self._private_key, algorithm=settings.JWT_ALGORITHM)

    def create_refresh_token(self, user_id: str) -> str:
        """Create a refresh token.

        Args:
            user_id: The user identifier (sub claim).

        Returns:
            A signed JWT refresh token string.
        """
        now = int(time.time())
        expire = now + settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        payload: Dict[str, Any] = {
            "sub": user_id,
            "iat": now,
            "exp": expire,
            "type": TokenType.REFRESH,
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, self._private_key, algorithm=settings.JWT_ALGORITHM)

    def verify_token(self, token: str, expected_type: str = TokenType.ACCESS) -> Dict[str, Any]:
        """Verify and decode a JWT token.

        Args:
            token: The JWT token string to verify.
            expected_type: Expected token type ("access" or "refresh").

        Returns:
            The decoded token payload as a dictionary.

        Raises:
            JWTError: If the token is invalid, expired, has wrong algorithm,
                or wrong token type.
        """
        try:
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except JWTError:
            raise

        if payload.get("type") != expected_type:
            raise JWTError(f"Invalid token type: expected {expected_type}")

        return payload

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Verify an access token."""
        return self.verify_token(token, TokenType.ACCESS)

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """Verify a refresh token."""
        return self.verify_token(token, TokenType.REFRESH)
