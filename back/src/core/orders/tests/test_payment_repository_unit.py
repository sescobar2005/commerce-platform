"""Unit tests for PaymentRepository.

Tests use SQLAlchemy with an in-memory SQLite database to verify
actual repository behavior without requiring a PostgreSQL database.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.database import Base
from src.core.models.order import Order, Payment
from src.core.orders.repositories import OrderRepository, PaymentRepository


def _create_session() -> Session:
    """Create an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


class TestPaymentRepository:
    """Tests for PaymentRepository."""

    def test_repository_construction(self):
        """Repository should store the database session."""
        session = _create_session()
        repo = PaymentRepository(session)
        assert repo.db is session
        session.close()

    def test_add_and_get_by_id(self):
        """Repository should add and retrieve a payment by ID."""
        session = _create_session()
        order_repo = OrderRepository(session)
        payment_repo = PaymentRepository(session)

        order = Order(
            order_id="order-123",
            user_id="user-456",
            total_amount=99.99,
        )
        order_repo.add(order)
        session.flush()

        payment = Payment(
            payment_id="payment-123",
            order_id="order-123",
            amount=99.99,
            method="simulated",
            status="pending",
        )
        payment_repo.add(payment)
        session.flush()

        result = payment_repo.get_by_id("payment-123")
        assert result is not None
        assert result.payment_id == "payment-123"
        assert result.order_id == "order-123"
        assert result.amount == 99.99
        assert result.method == "simulated"
        assert result.status == "pending"

        session.close()

    def test_get_by_id_returns_none_for_missing(self):
        """get_by_id should return None for nonexistent payment."""
        session = _create_session()
        repo = PaymentRepository(session)

        result = repo.get_by_id("nonexistent-id")
        assert result is None

        session.close()

    def test_get_by_order_id_returns_payments(self):
        """get_by_order_id should return payments for a specific order."""
        session = _create_session()
        order_repo = OrderRepository(session)
        payment_repo = PaymentRepository(session)

        order = Order(
            order_id="order-123",
            user_id="user-456",
            total_amount=99.99,
        )
        order_repo.add(order)

        payment1 = Payment(
            payment_id="payment-1",
            order_id="order-123",
            amount=50.00,
            method="simulated",
        )
        payment2 = Payment(
            payment_id="payment-2",
            order_id="order-123",
            amount=49.99,
            method="simulated",
        )
        payment_repo.add(payment1)
        payment_repo.add(payment2)
        session.flush()

        results = payment_repo.get_by_order_id("order-123")
        assert len(results) == 2
        payment_ids = {p.payment_id for p in results}
        assert payment_ids == {"payment-1", "payment-2"}

        session.close()

    def test_get_by_order_id_returns_empty_for_nonexistent_order(self):
        """get_by_order_id should return empty list for order with no payments."""
        session = _create_session()
        repo = PaymentRepository(session)

        results = repo.get_by_order_id("nonexistent-order")
        assert results == []

        session.close()

    def test_get_by_order_and_idempotency_key(self):
        """get_by_order_and_idempotency_key should find payment by order+key."""
        session = _create_session()
        order_repo = OrderRepository(session)
        payment_repo = PaymentRepository(session)

        order = Order(
            order_id="order-123",
            user_id="user-456",
            total_amount=99.99,
        )
        order_repo.add(order)

        payment = Payment(
            payment_id="payment-123",
            order_id="order-123",
            amount=99.99,
            method="simulated",
            idempotency_key="idem-key-1",
        )
        payment_repo.add(payment)
        session.flush()

        result = payment_repo.get_by_order_and_idempotency_key(
            "order-123", "idem-key-1"
        )
        assert result is not None
        assert result.payment_id == "payment-123"
        assert result.idempotency_key == "idem-key-1"

        result = payment_repo.get_by_order_and_idempotency_key(
            "order-nonexistent", "idem-key-1"
        )
        assert result is None

        result = payment_repo.get_by_order_and_idempotency_key(
            "order-123", "wrong-key"
        )
        assert result is None

        session.close()

    def test_get_by_order_and_idempotency_key_is_isolated_by_order(self):
        """get_by_order_and_idempotency_key should be scoped by order_id."""
        session = _create_session()
        order_repo = OrderRepository(session)
        payment_repo = PaymentRepository(session)

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

        payment_a = Payment(
            payment_id="payment-a",
            order_id="order-a",
            amount=10.00,
            method="simulated",
            idempotency_key="idem-key-1",
        )
        payment_b = Payment(
            payment_id="payment-b",
            order_id="order-b",
            amount=20.00,
            method="simulated",
            idempotency_key="idem-key-1",
        )
        payment_repo.add(payment_a)
        payment_repo.add(payment_b)
        session.flush()

        result = payment_repo.get_by_order_and_idempotency_key(
            "order-a", "idem-key-1"
        )
        assert result is not None
        assert result.payment_id == "payment-a"

        result = payment_repo.get_by_order_and_idempotency_key(
            "order-b", "idem-key-1"
        )
        assert result is not None
        assert result.payment_id == "payment-b"

        # Same idempotency key, different order should not match across orders
        result = payment_repo.get_by_order_and_idempotency_key(
            "order-a", "idem-key-2"
        )
        assert result is None

        session.close()

    def test_delete_removes_payment(self):
        """delete should remove a payment from the session."""
        session = _create_session()
        order_repo = OrderRepository(session)
        payment_repo = PaymentRepository(session)

        order = Order(
            order_id="order-123",
            user_id="user-456",
            total_amount=99.99,
        )
        order_repo.add(order)

        payment = Payment(
            payment_id="payment-123",
            order_id="order-123",
            amount=99.99,
            method="simulated",
        )
        payment_repo.add(payment)
        session.flush()

        payment_repo.delete(payment)
        session.flush()

        result = payment_repo.get_by_id("payment-123")
        assert result is None

        session.close()
