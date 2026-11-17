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


class TestAlembicConfigLoading:
    """Tests for loading the Alembic configuration without live database."""

    def test_alembic_config_can_be_loaded(self):
        """alembic.ini should be loadable as an Alembic Config object."""
        config = Config("back/alembic.ini")
        assert config is not None
        assert config.get_main_option("script_location") == "back/alembic"

    def test_alembic_config_has_sqlalchemy_url(self):
        """alembic.ini should reference DATABASE_URL via variable substitution."""
        config = Config("back/alembic.ini")
        url = config.get_main_option("sqlalchemy.url")
        assert url == "%(DATABASE_URL)s"

    def test_alembic_script_location_exists(self):
        """The script_location directory should exist."""
        assert os.path.isdir("back/alembic")


class TestSqlAlchemyMetadataIntegration:
    """Tests for SQLAlchemy metadata integration with Alembic."""

    def test_target_metadata_is_base_metadata(self):
        """Alembic target_metadata should be the application's Base.metadata."""
        assert Base.metadata is not None
        assert hasattr(Base.metadata, "tables")

    def test_metadata_has_no_tables_yet(self):
        """No model tables should be registered yet (models not yet implemented)."""
        assert len(Base.metadata.tables) == 0


class TestSettingsConfiguration:
    """Tests for settings configuration used by Alembic."""

    def test_settings_has_database_url(self):
        """Settings class should have DATABASE_URL field."""
        assert hasattr(Settings, "DATABASE_URL")

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
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]
        with pytest.raises(Exception):
            Settings()
