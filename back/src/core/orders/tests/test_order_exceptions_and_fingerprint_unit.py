"""Unit tests for Orders exceptions and request fingerprint utility.

Tests use SimpleNamespace objects acting as Cart and CartItem model
instances -- no live database required.
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from src.core.orders.exceptions import (
    IdempotencyConflictError,
    InsufficientStockError,
    OrderError,
    OrderItemNotFoundError,
    OrderNotFoundError,
    OrderOwnershipError,
    ProductInactiveError,
    ProductNotFoundError,
)
from src.core.orders.fingerprint import generate_cart_fingerprint


def _make_cart(cart_id="cart-123", items=None):
    """Create a SimpleNamespace acting as a Cart model instance."""
    if items is None:
        items = []
    return SimpleNamespace(cart_id=cart_id, items=items)


def _make_cart_item(
    product_id="product-456", quantity=2, price_at_time=Decimal("29.99")
):
    """Create a SimpleNamespace acting as a CartItem model instance."""
    return SimpleNamespace(
        product_id=product_id,
        quantity=quantity,
        price_at_time=price_at_time,
    )


# -----------------------------------------------------------------------
# Exception tests
# -----------------------------------------------------------------------


class TestOrderExceptionsInheritance:
    """Tests for Orders exception inheritance hierarchy."""

    def test_order_error_is_exception(self):
        assert issubclass(OrderError, Exception)

    def test_order_not_found_error_inherits_order_error(self):
        assert issubclass(OrderNotFoundError, OrderError)

    def test_order_ownership_error_inherits_order_error(self):
        assert issubclass(OrderOwnershipError, OrderError)

    def test_order_item_not_found_error_inherits_order_error(self):
        assert issubclass(OrderItemNotFoundError, OrderError)

    def test_product_not_found_error_inherits_order_error(self):
        assert issubclass(ProductNotFoundError, OrderError)

    def test_product_inactive_error_inherits_order_error(self):
        assert issubclass(ProductInactiveError, OrderError)

    def test_insufficient_stock_error_inherits_order_error(self):
        assert issubclass(InsufficientStockError, OrderError)

    def test_idempotency_conflict_error_inherits_order_error(self):
        assert issubclass(IdempotencyConflictError, OrderError)

    def test_idempotency_conflict_distinguishable(self):
        """IdempotencyConflictError is not a subclass of other Order errors."""
        assert not issubclass(
            IdempotencyConflictError, OrderNotFoundError
        )
        assert not issubclass(
            IdempotencyConflictError, OrderOwnershipError
        )
        assert not issubclass(
            IdempotencyConflictError, InsufficientStockError
        )


class TestOrderExceptionMessages:
    """Tests for Orders exception default messages."""

    def test_order_not_found_error_message(self):
        exc = OrderNotFoundError("order-123")
        assert exc.order_id == "order-123"
        assert "order-123" in str(exc)

    def test_order_ownership_error_message(self):
        exc = OrderOwnershipError("order-123", "user-456")
        assert exc.order_id == "order-123"
        assert exc.user_id == "user-456"
        assert "order-123" in str(exc)
        assert "user-456" in str(exc)

    def test_order_item_not_found_error_message(self):
        exc = OrderItemNotFoundError("item-123")
        assert exc.order_item_id == "item-123"
        assert "item-123" in str(exc)

    def test_product_not_found_error_message(self):
        exc = ProductNotFoundError("product-456")
        assert exc.product_id == "product-456"
        assert "product-456" in str(exc)

    def test_product_inactive_error_message(self):
        exc = ProductInactiveError("product-456")
        assert exc.product_id == "product-456"
        assert "product-456" in str(exc)

    def test_insufficient_stock_error_message(self):
        exc = InsufficientStockError("product-456", 10, 5)
        assert exc.product_id == "product-456"
        assert exc.requested == 10
        assert exc.available == 5
        assert "product-456" in str(exc)
        assert "10" in str(exc)
        assert "5" in str(exc)

    def test_idempotency_conflict_error_message(self):
        exc = IdempotencyConflictError("conflicting cart contents")
        assert "conflicting cart contents" in str(exc)


# -----------------------------------------------------------------------
# Fingerprint tests
# -----------------------------------------------------------------------


class TestFingerprintDeterminism:
    """Tests that the fingerprint is deterministic for the same input."""

    def test_same_cart_produces_identical_fingerprint(self):
        cart = _make_cart(
            cart_id="cart-1",
            items=[
                _make_cart_item(product_id="p-1", quantity=2, price_at_time=Decimal("10.00")),
                _make_cart_item(product_id="p-2", quantity=1, price_at_time=Decimal("20.00")),
            ],
        )
        fp1 = generate_cart_fingerprint(cart)
        fp2 = generate_cart_fingerprint(cart)
        assert fp1 == fp2
        assert len(fp1) == 64
        assert all(c in "0123456789abcdef" for c in fp1)

    def test_reordered_items_produce_same_fingerprint(self):
        items_a = [
            _make_cart_item(product_id="p-2", quantity=1, price_at_time=Decimal("20.00")),
            _make_cart_item(product_id="p-1", quantity=2, price_at_time=Decimal("10.00")),
        ]
        items_b = [
            _make_cart_item(product_id="p-1", quantity=2, price_at_time=Decimal("10.00")),
            _make_cart_item(product_id="p-2", quantity=1, price_at_time=Decimal("20.00")),
        ]
        cart_a = _make_cart(cart_id="cart-1", items=items_a)
        cart_b = _make_cart(cart_id="cart-1", items=items_b)
        assert generate_cart_fingerprint(cart_a) == generate_cart_fingerprint(cart_b)

    def test_different_cart_ids_produce_different_fingerprints(self):
        cart_a = _make_cart(
            cart_id="cart-a",
            items=[_make_cart_item(product_id="p-1", quantity=1, price_at_time=Decimal("10.00"))],
        )
        cart_b = _make_cart(
            cart_id="cart-b",
            items=[_make_cart_item(product_id="p-1", quantity=1, price_at_time=Decimal("10.00"))],
        )
        assert generate_cart_fingerprint(cart_a) != generate_cart_fingerprint(cart_b)

    def test_different_product_ids_produce_different_fingerprints(self):
        cart_a = _make_cart(
            cart_id="cart-1",
            items=[_make_cart_item(product_id="p-1", quantity=1, price_at_time=Decimal("10.00"))],
        )
        cart_b = _make_cart(
            cart_id="cart-1",
            items=[_make_cart_item(product_id="p-2", quantity=1, price_at_time=Decimal("10.00"))],
        )
        assert generate_cart_fingerprint(cart_a) != generate_cart_fingerprint(cart_b)

    def test_different_quantities_produce_different_fingerprints(self):
        cart_a = _make_cart(
            cart_id="cart-1",
            items=[_make_cart_item(product_id="p-1", quantity=1, price_at_time=Decimal("10.00"))],
        )
        cart_b = _make_cart(
            cart_id="cart-1",
            items=[_make_cart_item(product_id="p-1", quantity=2, price_at_time=Decimal("10.00"))],
        )
        assert generate_cart_fingerprint(cart_a) != generate_cart_fingerprint(cart_b)

    def test_different_prices_produce_different_fingerprints(self):
        cart_a = _make_cart(
            cart_id="cart-1",
            items=[_make_cart_item(product_id="p-1", quantity=1, price_at_time=Decimal("10.00"))],
        )
        cart_b = _make_cart(
            cart_id="cart-1",
            items=[_make_cart_item(product_id="p-1", quantity=1, price_at_time=Decimal("15.00"))],
        )
        assert generate_cart_fingerprint(cart_a) != generate_cart_fingerprint(cart_b)

    def test_decimal_serialization_is_deterministic(self):
        """Decimal('10') and Decimal('10.00') produce the same fingerprint component."""
        cart_a = _make_cart(
            cart_id="cart-1",
            items=[_make_cart_item(product_id="p-1", quantity=1, price_at_time=Decimal("10"))],
        )
        cart_b = _make_cart(
            cart_id="cart-1",
            items=[_make_cart_item(product_id="p-1", quantity=1, price_at_time=Decimal("10.00"))],
        )
        assert generate_cart_fingerprint(cart_a) == generate_cart_fingerprint(cart_b)

    def test_no_float_conversion(self):
        """Fingerprint must not be affected by float representation of prices."""
        cart = _make_cart(
            cart_id="cart-1",
            items=[
                _make_cart_item(product_id="p-1", quantity=3, price_at_time=Decimal("0.10")),
                _make_cart_item(product_id="p-2", quantity=7, price_at_time=Decimal("0.20")),
            ],
        )
        fp = generate_cart_fingerprint(cart)
        assert len(fp) == 64
        # Re-computing yields the same result
        assert generate_cart_fingerprint(cart) == fp

    def test_empty_items_handled(self):
        """A cart with no items produces a stable fingerprint."""
        cart = _make_cart(cart_id="cart-1", items=[])
        fp = generate_cart_fingerprint(cart)
        assert len(fp) == 64
        assert generate_cart_fingerprint(cart) == fp


class TestFingerprintInvalidInput:
    """Tests that invalid monetary input is rejected."""

    def test_price_at_time_not_decimal_raises(self):
        cart = _make_cart(
            cart_id="cart-1",
            items=[
                SimpleNamespace(
                    product_id="p-1",
                    quantity=1,
                    price_at_time=10.00,  # float, not Decimal
                )
            ],
        )
        with pytest.raises(ValueError, match="Monetary value must be a Decimal"):
            generate_cart_fingerprint(cart)

    def test_price_at_time_none_raises(self):
        cart = _make_cart(
            cart_id="cart-1",
            items=[
                SimpleNamespace(
                    product_id="p-1",
                    quantity=1,
                    price_at_time=None,
                )
            ],
        )
        with pytest.raises(ValueError, match="Monetary value must be a Decimal"):
            generate_cart_fingerprint(cart)

    def test_price_at_time_string_raises(self):
        cart = _make_cart(
            cart_id="cart-1",
            items=[
                SimpleNamespace(
                    product_id="p-1",
                    quantity=1,
                    price_at_time="10.00",  # string, not Decimal
                )
            ],
        )
        with pytest.raises(ValueError, match="Monetary value must be a Decimal"):
            generate_cart_fingerprint(cart)
