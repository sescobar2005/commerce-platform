"""Unit tests for password security service.

Tests do NOT require a live database or external services.
No real passwords are used in tests.
"""

import pytest

from src.core.security.password import PasswordService


class TestPasswordServiceHash:
    """Tests for password hashing."""

    def setup_method(self):
        self.service = PasswordService()

    def test_hash_returns_string(self):
        """hash_password should return a non-empty string."""
        result = self.service.hash_password("test_password_123")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_starts_with_argon2id(self):
        """Hash output should start with the Argon2id identifier."""
        result = self.service.hash_password("test_password_123")
        assert result.startswith("$argon2id$v=19$")

    def test_same_password_different_hashes(self):
        """Repeated hashing of the same password should produce different hashes."""
        hash1 = self.service.hash_password("same_password_456")
        hash2 = self.service.hash_password("same_password_456")
        assert hash1 != hash2

    def test_different_passwords_different_hashes(self):
        """Different passwords should produce different hashes."""
        hash1 = self.service.hash_password("password_alpha")
        hash2 = self.service.hash_password("password_beta")
        assert hash1 != hash2

    def test_hash_length_reasonable(self):
        """Hash should be a reasonable length (argon2id output)."""
        result = self.service.hash_password("test_password_789")
        assert len(result) > 50  # Argon2id encoded hash is typically ~120+ chars


class TestPasswordServiceVerify:
    """Tests for password verification."""

    def setup_method(self):
        self.service = PasswordService()

    def test_verify_correct_password(self):
        """verify_password should return True for correct password."""
        password_hash = self.service.hash_password("correct_password")
        assert self.service.verify_password("correct_password", password_hash) is True

    def test_verify_incorrect_password(self):
        """verify_password should return False for incorrect password."""
        password_hash = self.service.hash_password("correct_password")
        assert self.service.verify_password("wrong_password", password_hash) is False

    def test_verify_raises_on_empty_password(self):
        """verify_password should raise ValueError on empty password."""
        password_hash = self.service.hash_password("some_password")
        with pytest.raises(ValueError):
            self.service.verify_password("", password_hash)

    def test_verify_does_not_raise_on_invalid_hash(self):
        """verify_password should not raise on malformed hash."""
        result = self.service.verify_password("some_password", "not_a_valid_hash")
        assert result is False

    def test_verify_does_not_raise_on_garbage_hash(self):
        """verify_password should not raise on completely invalid input."""
        result = self.service.verify_password("some_password", "garbage!!!")
        assert result is False


class TestPasswordServiceInputValidation:
    """Tests for input validation."""

    def setup_method(self):
        self.service = PasswordService()

    def test_hash_raises_on_empty_password(self):
        """hash_password should raise ValueError on empty password."""
        with pytest.raises(ValueError):
            self.service.hash_password("")

    def test_hash_raises_on_non_string(self):
        """hash_password should raise TypeError on non-string input."""
        with pytest.raises(TypeError):
            self.service.hash_password(123)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            self.service.hash_password(None)  # type: ignore[arg-type]

    def test_verify_raises_on_empty_password(self):
        """verify_password should raise ValueError on empty password."""
        password_hash = self.service.hash_password("some_password")
        with pytest.raises(ValueError):
            self.service.verify_password("", password_hash)

    def test_verify_raises_on_empty_hash(self):
        """verify_password should raise ValueError on empty hash."""
        with pytest.raises(ValueError):
            self.service.verify_password("some_password", "")

    def test_verify_raises_on_non_string_password(self):
        """verify_password should raise TypeError on non-string password."""
        password_hash = self.service.hash_password("some_password")
        with pytest.raises(TypeError):
            self.service.verify_password(123, password_hash)  # type: ignore[arg-type]

    def test_verify_raises_on_non_string_hash(self):
        """verify_password should raise TypeError on non-string hash."""
        with pytest.raises(TypeError):
            self.service.verify_password("some_password", 123)  # type: ignore[arg-type]


class TestPasswordServiceConfiguration:
    """Tests for PasswordService configuration parameters."""

    def test_hasher_uses_argon2id(self):
        """PasswordHasher should be configured with argon2id type."""
        from argon2 import Type

        service = PasswordService()
        assert service._hasher.type == Type.ID

    def test_hasher_memory_cost(self):
        """PasswordHasher should use 64 MB memory cost."""
        service = PasswordService()
        assert service._hasher.memory_cost == 65536

    def test_hasher_time_cost(self):
        """PasswordHasher should use 3 iterations."""
        service = PasswordService()
        assert service._hasher.time_cost == 3

    def test_hasher_parallelism(self):
        """PasswordHasher should use 4 parallelism."""
        service = PasswordService()
        assert service._hasher.parallelism == 4

    def test_hasher_hash_length(self):
        """PasswordHasher should use 32 bytes hash length."""
        service = PasswordService()
        assert service._hasher.hash_len == 32

    def test_hasher_salt_length(self):
        """PasswordHasher should use 16 bytes salt length."""
        service = PasswordService()
        assert service._hasher.salt_len == 16
