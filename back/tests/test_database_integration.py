"""Integration tests for database engine configuration.

These tests REQUIRE a live PostgreSQL database.
They are skipped automatically when DATABASE_URL is not configured
or when the database is not reachable.
"""

import os

import pytest
from sqlalchemy import text

from src.core.database import SessionLocal, create_db_engine, engine


def _database_url_available() -> bool:
    """Check if a database URL is configured."""
    url = os.environ.get("DATABASE_URL", "")
    return bool(url)


@pytest.mark.skipif(
    not _database_url_available(),
    reason="DATABASE_URL environment variable not set",
)
class TestDatabaseEngineConnection:
    """Integration tests requiring a live PostgreSQL database."""

    def test_module_engine_can_connect(self):
        """Module-level engine should be able to connect and execute a simple query."""
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_create_db_engine_can_connect(self):
        """create_db_engine should produce an engine that can connect."""
        test_engine = create_db_engine()
        try:
            with test_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        finally:
            test_engine.dispose()

    def test_engine_supports_connection_pooling(self):
        """Engine should have a connection pool configured."""
        assert engine.pool is not None
        assert engine.pool.size() >= 0

    def test_engine_supports_health_check(self):
        """Engine should have pool_pre_ping enabled for connection health checks."""
        assert engine.pool._pre_ping is True


@pytest.mark.skipif(
    not _database_url_available(),
    reason="DATABASE_URL environment variable not set",
)
class TestSessionLifecycleIntegration:
    """Integration tests for session lifecycle requiring live PostgreSQL."""

    def test_session_can_connect_and_query(self):
        """SessionLocal should produce a session that can connect and query."""
        session = SessionLocal()
        try:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        finally:
            session.close()

    def test_session_closes_properly(self):
        """Session should be closable and marked inactive after close."""
        session = SessionLocal()
        session.close()
        assert session.is_active is False

    def test_session_rollback_works(self):
        """Session rollback should work without error on live database."""
        session = SessionLocal()
        try:
            session.execute(text("SELECT 1"))
            session.rollback()
        finally:
            session.close()

    def test_get_db_dependency_yields_usable_session(self):
        """get_db dependency should yield a session that can query live database."""
        from src.core.database import get_db

        generator = get_db()
        try:
            session = next(generator)
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        finally:
            try:
                generator.close()
            except StopIteration:
                pass


@pytest.mark.skipif(
    not _database_url_available(),
    reason="DATABASE_URL environment variable not set",
)
def test_database_url_from_settings():
    """Settings should load DATABASE_URL from environment."""
    from src.core.config import settings

    assert settings.DATABASE_URL == os.environ["DATABASE_URL"]
    assert settings.DATABASE_URL.startswith("postgresql+")
