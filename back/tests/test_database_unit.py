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

    def test_create_db_engine_raises_value_error_when_url_is_empty(self):
        """create_db_engine should raise ValueError when no URL is provided."""
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
        engine_instance = create_db_engine("sqlite:///:memory:")
        assert engine_instance.pool.size() == 5

    def test_create_db_engine_has_max_overflow_configured(self):
        """Engine should have max_overflow of 10."""
        engine_instance = create_db_engine("sqlite:///:memory:")
        assert engine_instance.pool._max_overflow == 10

    def test_create_db_engine_has_pool_timeout_configured(self):
        """Engine should have pool_timeout of 30 seconds."""
        engine_instance = create_db_engine("sqlite:///:memory:")
        assert engine_instance.pool._timeout == 30

    def test_create_db_engine_has_pool_recycle_configured(self):
        """Engine should have pool_recycle of 1800 seconds."""
        engine_instance = create_db_engine("sqlite:///:memory:")
        assert engine_instance.pool._recycle == 1800


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
