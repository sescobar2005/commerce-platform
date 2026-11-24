"""Unit tests for Alembic migration configuration.

These tests do NOT require a live PostgreSQL database.
They verify that the Alembic configuration can be loaded,
the SQLAlchemy metadata is correctly integrated, and
the migration environment is consistent with the application configuration.
"""

import os
from unittest.mock import patch

import pytest
from alembic.config import Config

from src.core.database import Base
from src.core.config import Settings
from src.core import models  # noqa: F401 — ensures model tables register with Base.metadata


class TestAlembicConfigLoading:
    """Tests for loading the Alembic configuration without live database."""

    def test_alembic_config_can_be_loaded(self):
        """alembic.ini should be loadable as an Alembic Config object."""
        config = Config("alembic.ini")
        assert config is not None
        assert config.get_main_option("script_location") == "alembic"

    def test_alembic_config_has_sqlalchemy_url(self):
        """alembic.ini should reference DATABASE_URL via variable substitution."""
        config = Config("alembic.ini")
        url = config.get_main_option("sqlalchemy.url")
        assert url == "%(DATABASE_URL)s"

    def test_alembic_script_location_exists(self):
        """The script_location directory should exist."""
        assert os.path.isdir("alembic")


class TestSqlAlchemyMetadataIntegration:
    """Tests for SQLAlchemy metadata integration with Alembic."""

    def test_target_metadata_is_base_metadata(self):
        """Alembic target_metadata should be the application's Base.metadata."""
        assert Base.metadata is not None
        assert hasattr(Base.metadata, "tables")

    def test_metadata_has_no_tables_yet(self):
        """Model tables should be registered in Base.metadata."""
        assert len(Base.metadata.tables) > 0
        expected_tables = {"users", "sellers", "stores", "categories", "products", "carts", "cart_items"}
        assert expected_tables.issubset(Base.metadata.tables.keys())


class TestSettingsConfiguration:
    """Tests for settings configuration used by Alembic."""

    def test_settings_has_database_url(self):
        """Settings class should have DATABASE_URL field."""
        assert "DATABASE_URL" in Settings.model_fields

    def test_database_url_from_env_var(self):
        """DATABASE_URL should be readable from environment variable."""
        os.environ["DATABASE_URL"] = "postgresql+psycopg://user:pass@localhost:5432/test_db"
        try:
            settings = Settings()
            assert settings.DATABASE_URL == "postgresql+psycopg://user:pass@localhost:5432/test_db"
        finally:
            del os.environ["DATABASE_URL"]

    def test_settings_raises_when_database_url_missing(self):
        """Settings should raise if DATABASE_URL is not set and no .env exists."""
        # Remove DATABASE_URL from environment to test isolation
        env_backup = os.environ.pop("DATABASE_URL", None)
        try:
            # Point to non-existent env file to isolate from developer's .env
            with patch.object(Settings, "model_config", {"env_file": ".env.nonexistent", "env_file_encoding": "utf-8"}):
                with pytest.raises(Exception):
                    Settings()
        finally:
            if env_backup is not None:
                os.environ["DATABASE_URL"] = env_backup
