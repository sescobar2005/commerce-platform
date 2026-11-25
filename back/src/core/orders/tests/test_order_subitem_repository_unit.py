"""Unit tests for OrderSubitemRepository.

Tests use SQLAlchemy with an in-memory SQLite database to verify
actual repository behavior without requiring a PostgreSQL database.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.database import Base
from src.core.models.order import Order, OrderSubitem
from src.core.orders.repositories import OrderRepository, OrderSubitemRepository


def _create_session() -> Session:
    """Create an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


class TestOrderSubitemRepository:
    """Tests for OrderSubitemRepository."""

    def test_repository_construction(self):
        """Repository should store the database session."""
        session = _create_session()
        repo = OrderSubitemRepository(session)
        assert repo.db is session
        session.close()

    def test_add_and_get_by_id(self):
        """Repository should add and retrieve an order subitem by ID."""
        session = _create_session()
        order_repo = OrderRepository(session)
        subitem_repo = OrderSubitemRepository(session)

        order = Order(
            order_id="order-123",
            user_id="user-456",
            total_amount=99.99,
        )
        order_repo.add(order)
        session.flush()

        subitem = OrderSubitem(
            order_subitem_id="subitem-123",
            order_id="order-123",
            seller_id="seller-abc",
            subtotal=59.98,
            status="pending",
        )
        subitem_repo.add(subitem)
        session.flush()

        result = subitem_repo.get_by_id("subitem-123")
        assert result is not None
        assert result.order_subitem_id == "subitem-123"
        assert result.order_id == "order-123"
        assert result.seller_id == "seller-abc"
        assert result.subtotal == 59.98
        assert result.status == "pending"

        session.close()

    def test_get_by_id_returns_none_for_missing(self):
        """get_by_id should return None for nonexistent subitem."""
        session = _create_session()
        repo = OrderSubitemRepository(session)

        result = repo.get_by_id("nonexistent-id")
        assert result is None

        session.close()

    def test_get_by_order_id_returns_subitems(self):
        """get_by_order_id should return subitems for a specific order."""
        session = _create_session()
        order_repo = OrderRepository(session)
        subitem_repo = OrderSubitemRepository(session)

        order = Order(
            order_id="order-123",
            user_id="user-456",
            total_amount=100.00,
        )
        order_repo.add(order)

        subitem1 = OrderSubitem(
            order_subitem_id="subitem-1",
            order_id="order-123",
            seller_id="seller-1",
            subtotal=30.00,
            status="pending",
        )
        subitem2 = OrderSubitem(
            order_subitem_id="subitem-2",
            order_id="order-123",
            seller_id="seller-2",
            subtotal=70.00,
            status="pending",
        )
        subitem_repo.add(subitem1)
        subitem_repo.add(subitem2)
        session.flush()

        results = subitem_repo.get_by_order_id("order-123")
        assert len(results) == 2
        subitem_ids = {s.order_subitem_id for s in results}
        assert subitem_ids == {"subitem-1", "subitem-2"}

        session.close()

    def test_get_by_order_and_seller_returns_subitem(self):
        """get_by_order_and_seller should return subitem by order and seller."""
        session = _create_session()
        order_repo = OrderRepository(session)
        subitem_repo = OrderSubitemRepository(session)

        order = Order(
            order_id="order-123",
            user_id="user-456",
            total_amount=99.99,
        )
        order_repo.add(order)

        subitem = OrderSubitem(
            order_subitem_id="subitem-123",
            order_id="order-123",
            seller_id="seller-abc",
            subtotal=59.98,
            status="pending",
        )
        subitem_repo.add(subitem)
        session.flush()

        result = subitem_repo.get_by_order_and_seller("order-123", "seller-abc")
        assert result is not None
        assert result.order_subitem_id == "subitem-123"
        assert result.order_id == "order-123"
        assert result.seller_id == "seller-abc"

        result = subitem_repo.get_by_order_and_seller("order-123", "seller-other")
        assert result is None

        result = subitem_repo.get_by_order_and_seller("order-nonexistent", "seller-abc")
        assert result is None

        session.close()

    def test_get_by_order_id_is_isolated_by_order(self):
        """get_by_order_id should only return subitems for the specified order."""
        session = _create_session()
        order_repo = OrderRepository(session)
        subitem_repo = OrderSubitemRepository(session)

        order_a = Order(
            order_id="order-a",
            user_id="user-1",
            total_amount=10.00,
        )
        order_b = Order(
            order_id="order-b",
            user_id="user-2",
            total_amount=20.00,
        )
        order_repo.add(order_a)
        order_repo.add(order_b)

        subitem_a = OrderSubitem(
            order_subitem_id="subitem-a",
            order_id="order-a",
            seller_id="seller-x",
            subtotal=10.00,
            status="pending",
        )
        subitem_b = OrderSubitem(
            order_subitem_id="subitem-b",
            order_id="order-b",
            seller_id="seller-y",
            subtotal=20.00,
            status="pending",
        )
        subitem_repo.add(subitem_a)
        subitem_repo.add(subitem_b)
        session.flush()

        results = subitem_repo.get_by_order_id("order-a")
        assert len(results) == 1
        assert results[0].order_subitem_id == "subitem-a"

        results = subitem_repo.get_by_order_id("order-b")
        assert len(results) == 1
        assert results[0].order_subitem_id == "subitem-b"

        session.close()

    def test_delete_removes_subitem(self):
        """delete should remove a subitem from the session."""
        session = _create_session()
        order_repo = OrderRepository(session)
        subitem_repo = OrderSubitemRepository(session)

        order = Order(
            order_id="order-123",
            user_id="user-456",
            total_amount=99.99,
        )
        order_repo.add(order)

        subitem = OrderSubitem(
            order_subitem_id="subitem-123",
            order_id="order-123",
            seller_id="seller-abc",
            subtotal=59.98,
            status="pending",
        )
        subitem_repo.add(subitem)
        session.flush()

        subitem_repo.delete(subitem)
        session.flush()

        result = subitem_repo.get_by_id("subitem-123")
        assert result is None

        session.close()
