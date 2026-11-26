"""Unit tests for Order source_cart_id and request_fingerprint columns.

Tests use SQLAlchemy with an in-memory SQLite database to verify
the new Order model columns are correctly defined and behave as
nullable fields without foreign key constraints.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.database import Base
from src.core.models.order import Order


def _create_session() -> Session:
    """Create an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


class TestOrderSourceCartIdColumn:
    """Tests for the source_cart_id column on the Order model."""

    def test_column_exists_on_model(self):
        """Order model should have source_cart_id attribute."""
        assert hasattr(Order, "source_cart_id")

    def test_column_is_nullable(self):
        """source_cart_id column should be nullable."""
        column = Order.__table__.columns["source_cart_id"]
        assert column.nullable is True

    def test_column_type_is_string_36(self):
        """source_cart_id column should be String(36)."""
        column = Order.__table__.columns["source_cart_id"]
        assert column.type.length == 36

    def test_column_has_no_foreign_key(self):
        """source_cart_id must NOT have a foreign key to carts."""
        column = Order.__table__.columns["source_cart_id"]
        assert len(column.foreign_keys) == 0

    def test_order_created_with_source_cart_id(self):
        """Order can be persisted with source_cart_id set."""
        session = _create_session()
        order = Order(
            order_id="order-1",
            user_id="user-1",
            total_amount=99.99,
            source_cart_id="cart-abc",
        )
        session.add(order)
        session.flush()

        result = session.query(Order).filter(Order.order_id == "order-1").first()
        assert result is not None
        assert result.source_cart_id == "cart-abc"

        session.close()

    def test_order_created_without_source_cart_id_defaults_none(self):
        """source_cart_id should be None when not provided."""
        session = _create_session()
        order = Order(
            order_id="order-1",
            user_id="user-1",
            total_amount=99.99,
        )
        session.add(order)
        session.flush()

        result = session.query(Order).filter(Order.order_id == "order-1").first()
        assert result.source_cart_id is None

        session.close()


class TestOrderRequestFingerprintColumn:
    """Tests for the request_fingerprint column on the Order model."""

    def test_column_exists_on_model(self):
        """Order model should have request_fingerprint attribute."""
        assert hasattr(Order, "request_fingerprint")

    def test_column_is_nullable(self):
        """request_fingerprint column should be nullable."""
        column = Order.__table__.columns["request_fingerprint"]
        assert column.nullable is True

    def test_column_type_is_string_64(self):
        """request_fingerprint column should be String(64)."""
        column = Order.__table__.columns["request_fingerprint"]
        assert column.type.length == 64

    def test_column_has_no_foreign_key(self):
        """request_fingerprint must NOT have a foreign key."""
        column = Order.__table__.columns["request_fingerprint"]
        assert len(column.foreign_keys) == 0

    def test_order_created_with_request_fingerprint(self):
        """Order can be persisted with request_fingerprint set."""
        session = _create_session()
        order = Order(
            order_id="order-1",
            user_id="user-1",
            total_amount=99.99,
            request_fingerprint="a" * 64,
        )
        session.add(order)
        session.flush()

        result = session.query(Order).filter(Order.order_id == "order-1").first()
        assert result is not None
        assert result.request_fingerprint == "a" * 64

        session.close()

    def test_order_created_without_request_fingerprint_defaults_none(self):
        """request_fingerprint should be None when not provided."""
        session = _create_session()
        order = Order(
            order_id="order-1",
            user_id="user-1",
            total_amount=99.99,
        )
        session.add(order)
        session.flush()

        result = session.query(Order).filter(Order.order_id == "order-1").first()
        assert result.request_fingerprint is None

        session.close()


class TestOrderBothColumnsTogether:
    """Tests for source_cart_id and request_fingerprint used together."""

    def test_order_with_both_columns_set(self):
        """Order can be persisted with both columns set simultaneously."""
        session = _create_session()
        order = Order(
            order_id="order-1",
            user_id="user-1",
            total_amount=150.00,
            source_cart_id="cart-123",
            request_fingerprint="b" * 64,
        )
        session.add(order)
        session.flush()

        result = session.query(Order).filter(Order.order_id == "order-1").first()
        assert result.source_cart_id == "cart-123"
        assert result.request_fingerprint == "b" * 64

        session.close()

    def test_order_queryable_by_source_cart_id(self):
        """Orders can be queried by source_cart_id."""
        session = _create_session()
        order1 = Order(
            order_id="order-1",
            user_id="user-1",
            total_amount=10.00,
            source_cart_id="cart-shared",
        )
        order2 = Order(
            order_id="order-2",
            user_id="user-1",
            total_amount=20.00,
            source_cart_id="cart-other",
        )
        session.add(order1)
        session.add(order2)
        session.flush()

        results = session.query(Order).filter(
            Order.source_cart_id == "cart-shared"
        ).all()
        assert len(results) == 1
        assert results[0].order_id == "order-1"

        session.close()
