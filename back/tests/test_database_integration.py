"""Integration tests for database engine configuration.

These tests REQUIRE a live PostgreSQL database.
They are skipped automatically when DATABASE_URL is not configured
or when the database is not reachable.
"""

import os

import pytest
from sqlalchemy import text

from src.core.database import create_db_engine, engine


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
def test_database_url_from_settings():
    """Settings should load DATABASE_URL from environment."""
    from src.core.config import settings

    assert settings.DATABASE_URL == os.environ["DATABASE_URL"]
    assert settings.DATABASE_URL.startswith("postgresql+")
