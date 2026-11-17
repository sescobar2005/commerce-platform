"""Password security service using Argon2id.

Provides secure password hashing and verification following the
project's security configuration defined in SECURITY.md:

- Algorithm: argon2id
- Memory cost: 64 MB (65536 KB)
- Time cost: 3 iterations
- Parallelism: 4
- Hash length: 32 bytes
- Salt: Random 16 bytes per hash
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError


class PasswordService:
    """Password security service using Argon2id.

    All passwords are hashed with Argon2id using the parameters
    approved in SECURITY.md. Each hash uses a randomly generated
    salt, ensuring that identical passwords produce different hashes.
    """

    def __init__(self) -> None:
        self._hasher = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_length=32,
            salt_length=16,
            type=2,  # argon2id
        )

    def hash_password(self, password: str) -> str:
        """Hash a plain-text password using Argon2id.

        Args:
            password: The plain-text password to hash.

        Returns:
            An Argon2id hash string suitable for storage in a database.

        Raises:
            TypeError: If password is not a string.
            ValueError: If password is empty.
        """
        if not isinstance(password, str):
            raise TypeError("Password must be a string")
        if not password:
            raise ValueError("Password must not be empty")
        return self._hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a plain-text password against an Argon2id hash.

        Args:
            password: The plain-text password to verify.
            password_hash: The Argon2id hash to verify against.

        Returns:
            True if the password matches the hash, False otherwise.

        Raises:
            TypeError: If password or password_hash is not a string.
            ValueError: If password or password_hash is empty.
        """
        if not isinstance(password, str):
            raise TypeError("Password must be a string")
        if not isinstance(password_hash, str):
            raise TypeError("Password hash must be a string")
        if not password:
            raise ValueError("Password must not be empty")
        if not password_hash:
            raise ValueError("Password hash must not be empty")
        try:
            return self._hasher.verify(password_hash, password)
        except (VerifyMismatchError, InvalidHashError):
            return False
