"""Unit tests for database engine configuration.

These tests do NOT require a live PostgreSQL database.
They use in-memory SQLite URLs for engine creation tests
and mock settings for error-handling tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase

from src.core.config import Settings
from src.core.database import Base, create_db_engine, engine


class TestDatabaseEngineCreation:
    """Tests for create_db_engine function without live database."""

    def test_create_db_engine_raises_value_error_when_url_is_empty(self, monkeypatch):
        """create_db_engine should raise ValueError when no URL is provided."""
        from src.core import database

        monkeypatch.setattr(database.settings, 'DATABASE_URL', '')
        with pytest.raises(ValueError, match="DATABASE_URL is not configured"):
            create_db_engine("")

    def test_create_db_engine_returns_engine_instance(self):
        """create_db_engine should return a SQLAlchemy Engine instance."""
        engine_instance = create_db_engine("sqlite:///:memory:")
        assert isinstance(engine_instance, Engine)

    def test_create_db_engine_has_pool_pre_ping_enabled(self):
        """Engine should have pool_pre_ping enabled for connection health checks."""
        engine_instance = create_db_engine("sqlite:///:memory:")
        assert engine_instance.pool._pre_ping is True

    def test_create_db_engine_has_pool_size_configured(self):
        """Engine should have pool_size of 5."""
        engine_instance = create_db_engine("postgresql+psycopg://user:pass@localhost:5432/test_db")
        try:
            from sqlalchemy.pool import QueuePool
            assert isinstance(engine_instance.pool, QueuePool)
            assert engine_instance.pool.size() == 5
        finally:
            engine_instance.dispose()

    def test_create_db_engine_has_max_overflow_configured(self):
        """Engine should have max_overflow of 10."""
        engine_instance = create_db_engine("postgresql+psycopg://user:pass@localhost:5432/test_db")
        try:
            from sqlalchemy.pool import QueuePool
            assert isinstance(engine_instance.pool, QueuePool)
            assert engine_instance.pool._max_overflow == 10
        finally:
            engine_instance.dispose()

    def test_create_db_engine_has_pool_timeout_configured(self):
        """Engine should have pool_timeout of 30 seconds."""
        engine_instance = create_db_engine("postgresql+psycopg://user:pass@localhost:5432/test_db")
        try:
            from sqlalchemy.pool import QueuePool
            assert isinstance(engine_instance.pool, QueuePool)
            assert engine_instance.pool._timeout == 30
        finally:
            engine_instance.dispose()

    def test_create_db_engine_has_pool_recycle_configured(self):
        """Engine should have pool_recycle of 1800 seconds."""
        engine_instance = create_db_engine("postgresql+psycopg://user:pass@localhost:5432/test_db")
        try:
            from sqlalchemy.pool import QueuePool
            assert isinstance(engine_instance.pool, QueuePool)
            assert engine_instance.pool._recycle == 1800
        finally:
            engine_instance.dispose()


class TestDatabaseBase:
    """Tests for the declarative base class."""

    def test_base_is_declarative_base(self):
        """Base should be a subclass of DeclarativeBase."""
        assert issubclass(Base, DeclarativeBase)


class TestModuleLevelEngine:
    """Tests for the module-level engine instance."""

    def test_module_engine_is_engine_instance(self):
        """Module-level engine should be a SQLAlchemy Engine instance."""
        assert isinstance(engine, Engine)

    def test_module_engine_has_pool_pre_ping(self):
        """Module-level engine should have pool_pre_ping enabled."""
        assert engine.pool._pre_ping is True

    def test_module_engine_has_pool_size_configured(self):
        """Module-level engine should have pool_size of 5."""
        assert engine.pool.size() == 5


class TestDatabaseEngineDialectCompatibility:
    """Tests for database engine compatibility across dialects.

    These tests verify that create_db_engine() correctly handles
    both SQLite (SingletonThreadPool) and PostgreSQL (QueuePool)
    database URLs without passing unsupported pool parameters.
    """

    def test_create_sqlite_engine_succeeds(self):
        """SQLite engine creation should succeed without TypeError."""
        engine_instance = create_db_engine("sqlite:///:memory:")
        assert isinstance(engine_instance, Engine)

    def test_sqlite_engine_has_pool_pre_ping(self):
        """SQLite engine should have pool_pre_ping enabled."""
        engine_instance = create_db_engine("sqlite:///:memory:")
        assert engine_instance.pool._pre_ping is True

    def test_sqlite_engine_does_not_receive_unsupported_pool_args(self):
        """SQLite engine should not receive QueuePool-only parameters.

        SingletonThreadPool does not accept max_overflow, pool_timeout,
        or pool_recycle. These must only be passed for QueuePool dialects.
        """
        engine_instance = create_db_engine("sqlite:///:memory:")
        assert not hasattr(engine_instance.pool, '_max_overflow')
        assert not hasattr(engine_instance.pool, '_timeout')

    def test_create_postgres_engine_preserves_pool_configuration(self):
        """PostgreSQL engine creation should pass all pool parameters."""
        from unittest.mock import MagicMock, patch

        with patch('src.core.database.create_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.pool._pre_ping = True
            mock_engine.pool.size = MagicMock(return_value=5)
            mock_engine.pool._max_overflow = 10
            mock_engine.pool._timeout = 30
            mock_engine.pool._recycle = 1800
            mock_create.return_value = mock_engine

            create_db_engine("postgresql+psycopg://user:pass@localhost:5432/test_db")

            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs['pool_pre_ping'] is True
            assert call_kwargs['pool_size'] == 5
            assert call_kwargs['max_overflow'] == 10
            assert call_kwargs['pool_timeout'] == 30
            assert call_kwargs['pool_recycle'] == 1800

    def test_create_db_engine_raises_value_error_when_no_url_available(self, monkeypatch):
        """create_db_engine should raise ValueError when no URL is available."""
        from src.core import database

        monkeypatch.setattr(database.settings, 'DATABASE_URL', '')
        with pytest.raises(ValueError, match="DATABASE_URL is not configured"):
            database.create_db_engine("")
