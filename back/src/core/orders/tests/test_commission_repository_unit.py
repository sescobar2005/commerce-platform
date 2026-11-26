"""Unit tests for CommissionRepository.

Tests use SQLAlchemy with an in-memory SQLite database to verify
actual repository behavior without requiring a PostgreSQL database.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.database import Base
from src.core.models.order import Commission, Order, OrderSubitem
from src.core.orders.repositories import CommissionRepository, OrderRepository, OrderSubitemRepository


def _create_session() -> Session:
    """Create an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


class TestCommissionRepository:
    """Tests for CommissionRepository."""

    def test_repository_construction(self):
        """Repository should store the database session."""
        session = _create_session()
        repo = CommissionRepository(session)
        assert repo.db is session
        session.close()

    def test_add_and_get_by_id(self):
        """Repository should add and retrieve a commission by ID."""
        session = _create_session()
        order_repo = OrderRepository(session)
        order_subitem_repo = OrderSubitemRepository(session)
        commission_repo = CommissionRepository(session)

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
        order_subitem_repo.add(subitem)
        session.flush()

        commission = Commission(
            commission_id="commission-123",
            seller_id="seller-abc",
            order_subitem_id="subitem-123",
            amount=5.99,
            status="pending",
        )
        commission_repo.add(commission)
        session.flush()

        result = commission_repo.get_by_id("commission-123")
        assert result is not None
        assert result.commission_id == "commission-123"
        assert result.seller_id == "seller-abc"
        assert result.order_subitem_id == "subitem-123"
        assert result.amount == 5.99
        assert result.status == "pending"

        session.close()

    def test_get_by_id_returns_none_for_missing(self):
        """get_by_id should return None for nonexistent commission."""
        session = _create_session()
        repo = CommissionRepository(session)

        result = repo.get_by_id("nonexistent-id")
        assert result is None

        session.close()

    def test_get_by_seller_id_returns_commissions(self):
        """get_by_seller_id should return commissions for a specific seller."""
        session = _create_session()
        order_repo = OrderRepository(session)
        order_subitem_repo = OrderSubitemRepository(session)
        commission_repo = CommissionRepository(session)

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
        order_subitem_repo.add(subitem1)
        order_subitem_repo.add(subitem2)

        commission1 = Commission(
            commission_id="commission-1",
            seller_id="seller-1",
            order_subitem_id="subitem-1",
            amount=3.00,
            status="pending",
        )
        commission2 = Commission(
            commission_id="commission-2",
            seller_id="seller-1",
            order_subitem_id="subitem-2",
            amount=7.00,
            status="pending",
        )
        commission_repo.add(commission1)
        commission_repo.add(commission2)
        session.flush()

        results = commission_repo.get_by_seller_id("seller-1")
        assert len(results) == 2
        commission_ids = {c.commission_id for c in results}
        assert commission_ids == {"commission-1", "commission-2"}

        session.close()

    def test_get_by_seller_id_is_paginated(self):
        """get_by_seller_id should respect skip and limit parameters."""
        session = _create_session()
        order_repo = OrderRepository(session)
        order_subitem_repo = OrderSubitemRepository(session)
        commission_repo = CommissionRepository(session)

        # Create multiple orders, each with one subitem for seller-1
        for i in range(5):
            order = Order(
                order_id=f"order-{i}",
                user_id="user-456",
                total_amount=100.00,
            )
            order_repo.add(order)
            subitem = OrderSubitem(
                order_subitem_id=f"subitem-{i}",
                order_id=f"order-{i}",
                seller_id="seller-1",
                subtotal=10.00,
                status="pending",
            )
            order_subitem_repo.add(subitem)
            commission = Commission(
                commission_id=f"commission-{i}",
                seller_id="seller-1",
                order_subitem_id=f"subitem-{i}",
                amount=1.00,
                status="pending",
            )
            commission_repo.add(commission)
        session.flush()

        page1 = commission_repo.get_by_seller_id("seller-1", skip=0, limit=2)
        assert len(page1) == 2

        page2 = commission_repo.get_by_seller_id("seller-1", skip=2, limit=2)
        assert len(page2) == 2

        page3 = commission_repo.get_by_seller_id("seller-1", skip=4, limit=2)
        assert len(page3) == 1

        session.close()

    def test_get_by_seller_id_isolates_sellers(self):
        """get_by_seller_id should only return commissions for the specified seller."""
        session = _create_session()
        order_repo = OrderRepository(session)
        order_subitem_repo = OrderSubitemRepository(session)
        commission_repo = CommissionRepository(session)

        order = Order(
            order_id="order-123",
            user_id="user-456",
            total_amount=100.00,
        )
        order_repo.add(order)

        subitem_a = OrderSubitem(
            order_subitem_id="subitem-a",
            order_id="order-123",
            seller_id="seller-a",
            subtotal=10.00,
            status="pending",
        )
        subitem_b = OrderSubitem(
            order_subitem_id="subitem-b",
            order_id="order-123",
            seller_id="seller-b",
            subtotal=20.00,
            status="pending",
        )
        order_subitem_repo.add(subitem_a)
        order_subitem_repo.add(subitem_b)

        commission_a = Commission(
            commission_id="commission-a",
            seller_id="seller-a",
            order_subitem_id="subitem-a",
            amount=1.00,
            status="pending",
        )
        commission_b = Commission(
            commission_id="commission-b",
            seller_id="seller-b",
            order_subitem_id="subitem-b",
            amount=2.00,
            status="pending",
        )
        commission_repo.add(commission_a)
        commission_repo.add(commission_b)
        session.flush()

        results = commission_repo.get_by_seller_id("seller-a")
        assert len(results) == 1
        assert results[0].commission_id == "commission-a"

        results = commission_repo.get_by_seller_id("seller-b")
        assert len(results) == 1
        assert results[0].commission_id == "commission-b"

        session.close()

    def test_get_by_order_subitem_id_returns_commission(self):
        """get_by_order_subitem_id should return commission by order subitem ID."""
        session = _create_session()
        order_repo = OrderRepository(session)
        order_subitem_repo = OrderSubitemRepository(session)
        commission_repo = CommissionRepository(session)

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
        order_subitem_repo.add(subitem)

        commission = Commission(
            commission_id="commission-123",
            seller_id="seller-abc",
            order_subitem_id="subitem-123",
            amount=5.99,
            status="pending",
        )
        commission_repo.add(commission)
        session.flush()

        result = commission_repo.get_by_order_subitem_id("subitem-123")
        assert result is not None
        assert result.commission_id == "commission-123"
        assert result.order_subitem_id == "subitem-123"
        assert result.seller_id == "seller-abc"

        result = commission_repo.get_by_order_subitem_id("subitem-nonexistent")
        assert result is None

        session.close()

    def test_delete_removes_commission(self):
        """delete should remove a commission from the session."""
        session = _create_session()
        order_repo = OrderRepository(session)
        order_subitem_repo = OrderSubitemRepository(session)
        commission_repo = CommissionRepository(session)

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
        order_subitem_repo.add(subitem)

        commission = Commission(
            commission_id="commission-123",
            seller_id="seller-abc",
            order_subitem_id="subitem-123",
            amount=5.99,
            status="pending",
        )
        commission_repo.add(commission)
        session.flush()

        commission_repo.delete(commission)
        session.flush()

        result = commission_repo.get_by_id("commission-123")
        assert result is None

        session.close()
