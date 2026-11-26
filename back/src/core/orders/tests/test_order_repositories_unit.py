"""Unit tests for order repositories.

Tests use SQLAlchemy with an in-memory SQLite database to verify
actual repository behavior without requiring a PostgreSQL database.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.database import Base
from src.core.models.order import Order, OrderItem, OrderSubitem
from src.core.orders.repositories import OrderRepository, OrderItemRepository


def _create_session() -> Session:
    """Create an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


class TestOrderRepository:
    """Tests for OrderRepository."""

    def test_repository_construction(self):
        """Repository should store the database session."""
        session = _create_session()
        repo = OrderRepository(session)
        assert repo.db is session
        session.close()

    def test_add_and_get_by_id(self):
        """Repository should add and retrieve an order by ID."""
        session = _create_session()
        repo = OrderRepository(session)

        order = Order(
            order_id="order-123",
            user_id="user-456",
            total_amount=99.99,
            status="pending",
            payment_status="pending",
        )
        repo.add(order)
        session.flush()

        result = repo.get_by_id("order-123")
        assert result is not None
        assert result.order_id == "order-123"
        assert result.user_id == "user-456"
        assert result.total_amount == 99.99
        assert result.status == "pending"

        session.close()

    def test_get_by_id_returns_none_for_missing(self):
        """get_by_id should return None for nonexistent order."""
        session = _create_session()
        repo = OrderRepository(session)

        result = repo.get_by_id("nonexistent-id")
        assert result is None

        session.close()

    def test_get_by_user_id_returns_orders(self):
        """get_by_user_id should return orders for a specific user."""
        session = _create_session()
        repo = OrderRepository(session)

        order1 = Order(
            order_id="order-1", user_id="user-1", total_amount=10.00
        )
        order2 = Order(
            order_id="order-2", user_id="user-1", total_amount=20.00
        )
        order3 = Order(
            order_id="order-3", user_id="user-2", total_amount=30.00
        )
        repo.add(order1)
        repo.add(order2)
        repo.add(order3)
        session.flush()

        results = repo.get_by_user_id("user-1")
        assert len(results) == 2
        order_ids = {o.order_id for o in results}
        assert order_ids == {"order-1", "order-2"}

        session.close()

    def test_get_by_user_id_is_paginated(self):
        """get_by_user_id should respect skip and limit parameters."""
        session = _create_session()
        repo = OrderRepository(session)

        for i in range(5):
            order = Order(
                order_id=f"order-{i}",
                user_id="user-1",
                total_amount=float(i),
            )
            repo.add(order)
        session.flush()

        page1 = repo.get_by_user_id("user-1", skip=0, limit=2)
        assert len(page1) == 2

        page2 = repo.get_by_user_id("user-1", skip=2, limit=2)
        assert len(page2) == 2

        page3 = repo.get_by_user_id("user-1", skip=4, limit=2)
        assert len(page3) == 1

        session.close()

    def test_get_by_user_id_isolates_users(self):
        """get_by_user_id should only return orders for the specified user."""
        session = _create_session()
        repo = OrderRepository(session)

        order_a = Order(
            order_id="order-a", user_id="user-a", total_amount=10.00
        )
        order_b = Order(
            order_id="order-b", user_id="user-b", total_amount=20.00
        )
        repo.add(order_a)
        repo.add(order_b)
        session.flush()

        results = repo.get_by_user_id("user-a")
        assert len(results) == 1
        assert results[0].order_id == "order-a"

        results = repo.get_by_user_id("user-b")
        assert len(results) == 1
        assert results[0].order_id == "order-b"

        session.close()

    def test_get_by_user_and_idempotency_key(self):
        """get_by_user_and_idempotency_key should find order by user+key."""
        session = _create_session()
        repo = OrderRepository(session)

        order = Order(
            order_id="order-123",
            user_id="user-456",
            total_amount=99.99,
            idempotency_key="idem-key-1",
        )
        repo.add(order)
        session.flush()

        result = repo.get_by_user_and_idempotency_key(
            "user-456", "idem-key-1"
        )
        assert result is not None
        assert result.order_id == "order-123"

        result = repo.get_by_user_and_idempotency_key(
            "user-wrong", "idem-key-1"
        )
        assert result is None

        result = repo.get_by_user_and_idempotency_key(
            "user-456", "wrong-key"
        )
        assert result is None

        session.close()

    def test_get_by_user_and_idempotency_key_returns_none_for_missing(self):
        """get_by_user_and_idempotency_key should return None for missing key."""
        session = _create_session()
        repo = OrderRepository(session)

        result = repo.get_by_user_and_idempotency_key(
            "user-1", "nonexistent-key"
        )
        assert result is None

        session.close()

    def test_add_and_get_orderitem(self):
        """Repository should add and retrieve an order item."""
        session = _create_session()
        order_repo = OrderRepository(session)
        item_repo = OrderItemRepository(session)

        order = Order(
            order_id="order-123",
            user_id="user-456",
            total_amount=99.99,
        )
        order_repo.add(order)
        session.flush()

        item = OrderItem(
            order_item_id="item-123",
            order_id="order-123",
            product_id="product-789",
            seller_id="seller-abc",
            product_name="Test Product",
            product_sku="SKU-001",
            quantity=2,
            price=29.99,
        )
        item_repo.add(item)
        session.flush()

        result = item_repo.get_by_id("item-123")
        assert result is not None
        assert result.order_item_id == "item-123"
        assert result.order_id == "order-123"
        assert result.product_name == "Test Product"
        assert result.quantity == 2
        assert result.price == 29.99

        session.close()

    def test_get_by_id_returns_none_for_missing_item(self):
        """get_by_id should return None for nonexistent order item."""
        session = _create_session()
        repo = OrderItemRepository(session)

        result = repo.get_by_id("nonexistent-id")
        assert result is None

        session.close()

    def test_get_by_order_id_returns_items(self):
        """get_by_order_id should return items for a specific order."""
        session = _create_session()
        order_repo = OrderRepository(session)
        item_repo = OrderItemRepository(session)

        order = Order(
            order_id="order-123", user_id="user-456", total_amount=0.00
        )
        order_repo.add(order)

        item1 = OrderItem(
            order_item_id="item-1",
            order_id="order-123",
            product_id="product-1",
            seller_id="seller-1",
            product_name="Product 1",
            quantity=1,
            price=10.00,
        )
        item2 = OrderItem(
            order_item_id="item-2",
            order_id="order-123",
            product_id="product-2",
            seller_id="seller-2",
            product_name="Product 2",
            quantity=2,
            price=20.00,
        )
        item_repo.add(item1)
        item_repo.add(item2)
        session.flush()

        results = item_repo.get_by_order_id("order-123")
        assert len(results) == 2
        item_ids = {i.order_item_id for i in results}
        assert item_ids == {"item-1", "item-2"}

        session.close()

    def test_get_by_order_id_returns_empty_for_nonexistent_order(self):
        """get_by_order_id should return empty list for order with no items."""
        session = _create_session()
        repo = OrderItemRepository(session)

        results = repo.get_by_order_id("nonexistent-order")
        assert results == []

        session.close()

    def test_delete_removes_order(self):
        """delete should remove an order from the session."""
        session = _create_session()
        repo = OrderRepository(session)

        order = Order(
            order_id="order-123", user_id="user-456", total_amount=99.99
        )
        repo.add(order)
        session.flush()

        repo.delete(order)
        session.flush()

        result = repo.get_by_id("order-123")
        assert result is None

        session.close()

    def test_delete_removes_order_item(self):
        """delete should remove an order item from the session."""
        session = _create_session()
        order_repo = OrderRepository(session)
        item_repo = OrderItemRepository(session)

        order = Order(
            order_id="order-123", user_id="user-456", total_amount=99.99
        )
        order_repo.add(order)

        item = OrderItem(
            order_item_id="item-123",
            order_id="order-123",
            product_id="product-789",
            seller_id="seller-abc",
            product_name="Test Product",
            quantity=1,
            price=10.00,
        )
        item_repo.add(item)
        session.flush()

        item_repo.delete(item)
        session.flush()

        result = item_repo.get_by_id("item-123")
        assert result is None

        session.close()

    def test_get_by_id_returns_complete_items_collection(self):
        """get_by_id should eagerly load ALL items (not just first row).

        Uses Session.query() legacy API which internally merges joined
        collection rows. Verifies .unique() is NOT required for Query API.
        """
        session = _create_session()
        repo = OrderRepository(session)

        order = Order(
            order_id="order-1",
            user_id="user-1",
            total_amount=60.00,
        )
        repo.add(order)
        session.flush()

        item1 = OrderItem(
            order_item_id="item-1",
            order_id="order-1",
            product_id="product-1",
            seller_id="seller-1",
            product_name="Product 1",
            product_sku="SKU-001",
            quantity=2,
            price=10.00,
        )
        item2 = OrderItem(
            order_item_id="item-2",
            order_id="order-1",
            product_id="product-2",
            seller_id="seller-1",
            product_name="Product 2",
            product_sku="SKU-002",
            quantity=3,
            price=20.00,
        )
        session.add(item1)
        session.add(item2)
        session.flush()

        result = repo.get_by_id("order-1")
        assert result is not None
        assert len(result.items) == 2
        item_ids = {i.order_item_id for i in result.items}
        assert item_ids == {"item-1", "item-2"}

        session.close()

    def test_get_by_id_returns_complete_subitems_collection(self):
        """get_by_id should eagerly load ALL subitems (not just first row).

        Uses Session.query() legacy API which internally merges joined
        collection rows. Verifies .unique() is NOT required for Query API.
        """
        session = _create_session()
        repo = OrderRepository(session)

        order = Order(
            order_id="order-1",
            user_id="user-1",
            total_amount=60.00,
        )
        repo.add(order)
        session.flush()

        subitem1 = OrderSubitem(
            order_subitem_id="subitem-1",
            order_id="order-1",
            seller_id="seller-1",
            subtotal=20.00,
            status="pending",
        )
        subitem2 = OrderSubitem(
            order_subitem_id="subitem-2",
            order_id="order-1",
            seller_id="seller-2",
            subtotal=40.00,
            status="pending",
        )
        session.add(subitem1)
        session.add(subitem2)
        session.flush()

        result = repo.get_by_id("order-1")
        assert result is not None
        assert len(result.subitems) == 2
        subitem_ids = {s.order_subitem_id for s in result.subitems}
        assert subitem_ids == {"subitem-1", "subitem-2"}

        session.close()

    def test_get_by_id_returns_both_collections_complete(self):
        """get_by_id should return complete items AND subitems together."""
        session = _create_session()
        repo = OrderRepository(session)

        order = Order(
            order_id="order-1",
            user_id="user-1",
            total_amount=60.00,
        )
        repo.add(order)
        session.flush()

        item = OrderItem(
            order_item_id="item-1",
            order_id="order-1",
            product_id="product-1",
            seller_id="seller-1",
            product_name="Product 1",
            product_sku="SKU-001",
            quantity=1,
            price=10.00,
        )
        subitem = OrderSubitem(
            order_subitem_id="subitem-1",
            order_id="order-1",
            seller_id="seller-1",
            subtotal=10.00,
            status="pending",
        )
        session.add(item)
        session.add(subitem)
        session.flush()

        result = repo.get_by_id("order-1")
        assert result is not None
        assert len(result.items) == 1
        assert len(result.subitems) == 1
        assert result.items[0].product_name == "Product 1"
        assert result.subitems[0].subtotal == 10.00

        session.close()

    def test_get_by_user_id_deterministic_ordering_same_created_at(self):
        """get_by_user_id should return stable order when created_at ties.

        Orders sharing the same created_at are ordered by order_id desc
        as a stable secondary sort key.
        """
        session = _create_session()
        repo = OrderRepository(session)

        same_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        order_a = Order(
            order_id="order-a",
            user_id="user-1",
            total_amount=10.00,
            created_at=same_time,
        )
        order_b = Order(
            order_id="order-b",
            user_id="user-1",
            total_amount=20.00,
            created_at=same_time,
        )
        order_c = Order(
            order_id="order-c",
            user_id="user-1",
            total_amount=30.00,
            created_at=same_time,
        )
        repo.add(order_a)
        repo.add(order_b)
        repo.add(order_c)
        session.flush()

        results = repo.get_by_user_id("user-1")
        assert len(results) == 3
        # order_id desc: order-c, order-b, order-a
        result_ids = [o.order_id for o in results]
        assert result_ids == ["order-c", "order-b", "order-a"]

        session.close()

