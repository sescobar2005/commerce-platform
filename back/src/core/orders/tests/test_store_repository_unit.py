"""Unit tests for StoreRepository.

Tests use SQLAlchemy with an in-memory SQLite database to verify
repository behavior without requiring a PostgreSQL database.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.database import Base
from src.core.models.store import Store
from src.core.orders.repositories import StoreRepository


def _create_session() -> Session:
    """Create an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


class TestStoreRepository:
    """Tests for StoreRepository."""

    def test_repository_construction(self):
        """Repository should store the database session."""
        session = _create_session()
        repo = StoreRepository(session)
        assert repo.db is session
        session.close()

    def test_get_seller_id_returns_seller_id_for_existing_store(self):
        """get_seller_id should return the seller ID for an existing store."""
        session = _create_session()
        repo = StoreRepository(session)

        store = Store(
            store_id="store-1",
            seller_id="seller-abc",
            name="Test Store",
            slug="test-store",
        )
        session.add(store)
        session.flush()

        result = repo.get_seller_id("store-1")
        assert result == "seller-abc"

        session.close()

    def test_get_seller_id_returns_none_for_nonexistent_store(self):
        """get_seller_id should return None for a nonexistent store."""
        session = _create_session()
        repo = StoreRepository(session)

        result = repo.get_seller_id("nonexistent-store")
        assert result is None

        session.close()

    def test_get_seller_ids_bulk_lookup(self):
        """get_seller_ids should return a mapping for multiple stores."""
        session = _create_session()
        repo = StoreRepository(session)

        store1 = Store(
            store_id="store-1",
            seller_id="seller-a",
            name="Store A",
            slug="store-a",
        )
        store2 = Store(
            store_id="store-2",
            seller_id="seller-b",
            name="Store B",
            slug="store-b",
        )
        store3 = Store(
            store_id="store-3",
            seller_id="seller-a",
            name="Store C",
            slug="store-c",
        )
        session.add(store1)
        session.add(store2)
        session.add(store3)
        session.flush()

        result = repo.get_seller_ids(["store-1", "store-2", "store-3"])
        assert result == {
            "store-1": "seller-a",
            "store-2": "seller-b",
            "store-3": "seller-a",
        }

        session.close()

    def test_get_seller_ids_omits_nonexistent_stores(self):
        """get_seller_ids should omit stores that do not exist."""
        session = _create_session()
        repo = StoreRepository(session)

        store = Store(
            store_id="store-1",
            seller_id="seller-a",
            name="Store A",
            slug="store-a",
        )
        session.add(store)
        session.flush()

        result = repo.get_seller_ids(["store-1", "nonexistent-store"])
        assert result == {"store-1": "seller-a"}

        session.close()

    def test_get_seller_ids_deduplicates_input(self):
        """get_seller_ids should deduplicate duplicate store IDs."""
        session = _create_session()
        repo = StoreRepository(session)

        store = Store(
            store_id="store-1",
            seller_id="seller-a",
            name="Store A",
            slug="store-a",
        )
        session.add(store)
        session.flush()

        result = repo.get_seller_ids(["store-1", "store-1", "store-1"])
        assert result == {"store-1": "seller-a"}

        session.close()

    def test_get_seller_ids_empty_input_returns_empty(self):
        """get_seller_ids should return an empty dict for empty input."""
        session = _create_session()
        repo = StoreRepository(session)

        result = repo.get_seller_ids([])
        assert result == {}

        session.close()

    def test_repository_has_no_commit_method(self):
        """Repository should not expose commit method."""
        session = _create_session()
        repo = StoreRepository(session)
        assert not hasattr(repo, "commit")
        session.close()

    def test_repository_has_no_rollback_method(self):
        """Repository should not expose rollback method."""
        session = _create_session()
        repo = StoreRepository(session)
        assert not hasattr(repo, "rollback")
        session.close()

    def test_repository_has_no_refresh_method(self):
        """Repository should not expose refresh method."""
        session = _create_session()
        repo = StoreRepository(session)
        assert not hasattr(repo, "refresh")
        session.close()
