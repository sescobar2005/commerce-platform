"""Unit tests for the source_cart_id and request_fingerprint migration.

These tests verify the Alembic migration script structure without
requiring a live database or applying the migration.
"""

import importlib.util
import os

import pytest

MIGRATION_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "..",
    "alembic",
    "versions",
    "0e9ed90dea55_add_source_cart_id_and_request_.py",
)


def _load_migration_module():
    """Load the migration module by file path."""
    spec = importlib.util.spec_from_file_location(
        "migration_0e9ed90dea55", MIGRATION_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestMigrationFileExists:
    """Tests that the migration file exists at the expected path."""

    def test_migration_file_exists(self):
        """Migration file should exist on disk."""
        assert os.path.isfile(MIGRATION_PATH)


class TestMigrationRevision:
    """Tests migration revision identifiers."""

    def test_revision_id(self):
        """Revision ID should be 0e9ed90dea55."""
        module = _load_migration_module()
        assert module.revision == "0e9ed90dea55"

    def test_down_revision(self):
        """down_revision should point to 8e7f6d5c4b3a."""
        module = _load_migration_module()
        assert module.down_revision == "8e7f6d5c4b3a"

    def test_branch_labels_none(self):
        """branch_labels should be None."""
        module = _load_migration_module()
        assert module.branch_labels is None

    def test_depends_on_none(self):
        """depends_on should be None."""
        module = _load_migration_module()
        assert module.depends_on is None


class TestMigrationUpgrade:
    """Tests the upgrade function adds the expected columns."""

    def test_upgrade_function_exists(self):
        """Migration should have an upgrade function."""
        module = _load_migration_module()
        assert callable(module.upgrade)

    def test_upgrade_adds_source_cart_id_column(self):
        """upgrade() should add source_cart_id column to orders table."""
        module = _load_migration_module()
        source = open(MIGRATION_PATH).read()
        assert "op.add_column('orders', sa.Column('source_cart_id'" in source

    def test_upgrade_adds_request_fingerprint_column(self):
        """upgrade() should add request_fingerprint column to orders table."""
        module = _load_migration_module()
        source = open(MIGRATION_PATH).read()
        assert "op.add_column('orders', sa.Column('request_fingerprint'" in source

    def test_upgrade_columns_are_nullable(self):
        """Both new columns should be nullable in upgrade."""
        module = _load_migration_module()
        source = open(MIGRATION_PATH).read()
        assert "nullable=True" in source


class TestMigrationDowngrade:
    """Tests the downgrade function removes the expected columns."""

    def test_downgrade_function_exists(self):
        """Migration should have a downgrade function."""
        module = _load_migration_module()
        assert callable(module.downgrade)

    def test_downgrade_removes_request_fingerprint_column(self):
        """downgrade() should drop request_fingerprint column."""
        module = _load_migration_module()
        source = open(MIGRATION_PATH).read()
        assert "op.drop_column('orders', 'request_fingerprint')" in source

    def test_downgrade_removes_source_cart_id_column(self):
        """downgrade() should drop source_cart_id column."""
        module = _load_migration_module()
        source = open(MIGRATION_PATH).read()
        assert "op.drop_column('orders', 'source_cart_id')" in source
