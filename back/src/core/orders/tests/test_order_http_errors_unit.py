"""Unit tests for Orders HTTP exception mapping.

Tests the ``_handle_service_error`` function that translates Orders
domain exceptions into FastAPI HTTP exceptions.

Tests cover every Orders exception, correct HTTP status codes, safe
public error messages, ownership/privacy behavior, and that unexpected
exceptions are not silently misclassified.
"""

import pytest
from fastapi import HTTPException
from starlette import status

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
from src.core.orders.router import _handle_service_error


# -----------------------------------------------------------------------
# OrderNotFoundError -> 404
# ----------------------------------------------------------------------


class TestOrderNotFoundError:
    """Tests for OrderNotFoundError mapping."""

    def test_maps_to_404(self):
        """OrderNotFoundError maps to HTTP 404."""
        exc = OrderNotFoundError(order_id="order-123")
        http_exc = _handle_service_error(exc)
        assert http_exc.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_is_generic(self):
        """Detail does not expose the order ID (privacy)."""
        exc = OrderNotFoundError(order_id="order-123")
        http_exc = _handle_service_error(exc)
        assert http_exc.detail == "Order not found"
        assert "order-123" not in str(http_exc.detail)


# -----------------------------------------------------------------------
# OrderOwnershipError -> 404
# ----------------------------------------------------------------------


class TestOrderOwnershipError:
    """Tests for OrderOwnershipError mapping."""

    def test_maps_to_404(self):
        """OrderOwnershipError maps to HTTP 404."""
        exc = OrderOwnershipError(order_id="order-123", user_id="user-456")
        http_exc = _handle_service_error(exc)
        assert http_exc.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_is_generic(self):
        """Detail does not expose ownership information (privacy)."""
        exc = OrderOwnershipError(order_id="order-123", user_id="user-456")
        http_exc = _handle_service_error(exc)
        assert http_exc.detail == "Order not found"
        assert "user-456" not in str(http_exc.detail)
        assert "order-123" not in str(http_exc.detail)
        assert "own" not in str(http_exc.detail).lower()
        assert "belong" not in str(http_exc.detail).lower()


# -----------------------------------------------------------------------
# OrderItemNotFoundError -> 404
# ----------------------------------------------------------------------


class TestOrderItemNotFoundError:
    """Tests for OrderItemNotFoundError mapping."""

    def test_maps_to_404(self):
        """OrderItemNotFoundError maps to HTTP 404."""
        exc = OrderItemNotFoundError(order_item_id="item-123")
        http_exc = _handle_service_error(exc)
        assert http_exc.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_is_generic(self):
        """Detail does not expose the item ID."""
        exc = OrderItemNotFoundError(order_item_id="item-123")
        http_exc = _handle_service_error(exc)
        assert http_exc.detail == "Order item not found"
        assert "item-123" not in str(http_exc.detail)


# -----------------------------------------------------------------------
# ProductNotFoundError -> 404
# ----------------------------------------------------------------------


class TestProductNotFoundError:
    """Tests for ProductNotFoundError mapping."""

    def test_maps_to_404(self):
        """ProductNotFoundError maps to HTTP 404."""
        exc = ProductNotFoundError(product_id="product-123")
        http_exc = _handle_service_error(exc)
        assert http_exc.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_is_generic(self):
        """Detail does not expose the product ID."""
        exc = ProductNotFoundError(product_id="product-123")
        http_exc = _handle_service_error(exc)
        assert http_exc.detail == "Product not found"
        assert "product-123" not in str(http_exc.detail)


# -----------------------------------------------------------------------
# ProductInactiveError -> 404
# ----------------------------------------------------------------------


class TestProductInactiveError:
    """Tests for ProductInactiveError mapping."""

    def test_maps_to_404(self):
        """ProductInactiveError maps to HTTP 404."""
        exc = ProductInactiveError(product_id="product-123")
        http_exc = _handle_service_error(exc)
        assert http_exc.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_is_generic(self):
        """Detail does not reveal product is inactive (privacy)."""
        exc = ProductInactiveError(product_id="product-123")
        http_exc = _handle_service_error(exc)
        assert http_exc.detail == "Product not found"
        assert "product-123" not in str(http_exc.detail)
        assert "inactive" not in str(http_exc.detail).lower()
        assert "unavailable" not in str(http_exc.detail).lower()


# -----------------------------------------------------------------------
# InsufficientStockError -> 409
# ----------------------------------------------------------------------


class TestInsufficientStockError:
    """Tests for InsufficientStockError mapping."""

    def test_maps_to_409(self):
        """InsufficientStockError maps to HTTP 409."""
        exc = InsufficientStockError(
            product_id="product-123", requested=10, available=5
        )
        http_exc = _handle_service_error(exc)
        assert http_exc.status_code == status.HTTP_409_CONFLICT

    def test_detail_is_generic(self):
        """Detail does not expose stock quantities."""
        exc = InsufficientStockError(
            product_id="product-123", requested=10, available=5
        )
        http_exc = _handle_service_error(exc)
        assert http_exc.detail == "Insufficient stock"
        assert "product-123" not in str(http_exc.detail)
        assert "10" not in str(http_exc.detail)
        assert "5" not in str(http_exc.detail)


# -----------------------------------------------------------------------
# IdempotencyConflictError -> 409
# ----------------------------------------------------------------------


class TestIdempotencyConflictError:
    """Tests for IdempotencyConflictError mapping."""

    def test_maps_to_409(self):
        """IdempotencyConflictError maps to HTTP 409."""
        exc = IdempotencyConflictError(
            "Idempotency key 'key-123' conflicts with existing order order-1"
        )
        http_exc = _handle_service_error(exc)
        assert http_exc.status_code == status.HTTP_409_CONFLICT

    def test_detail_contains_conflict_message(self):
        """Detail contains the conflict message."""
        exc = IdempotencyConflictError(
            "Idempotency key 'key-123' conflicts with existing order order-1"
        )
        http_exc = _handle_service_error(exc)
        assert "conflicts" in str(http_exc.detail)

    def test_empty_message_uses_default(self):
        """Empty message uses default detail."""
        exc = IdempotencyConflictError("")
        http_exc = _handle_service_error(exc)
        assert http_exc.detail == "Idempotency conflict"


# -----------------------------------------------------------------------
# OrderError fallback -> 400
# ----------------------------------------------------------------------


class TestOrderErrorFallback:
    """Tests for generic OrderError fallback mapping."""

    def test_maps_to_400(self):
        """Generic OrderError maps to HTTP 400."""
        exc = OrderError("Some validation error")
        http_exc = _handle_service_error(exc)
        assert http_exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_detail_contains_message(self):
        """Detail contains the exception message."""
        exc = OrderError("Some validation error")
        http_exc = _handle_service_error(exc)
        assert http_exc.detail == "Some validation error"

    def test_empty_message_uses_default(self):
        """Empty message uses default detail."""
        exc = OrderError("")
        http_exc = _handle_service_error(exc)
        assert http_exc.detail == "Order operation failed"


# -----------------------------------------------------------------------
# Unexpected exceptions are not caught
# ----------------------------------------------------------------------


class TestUnexpectedExceptions:
    """Tests that non-OrderError exceptions are not misclassified."""

    def test_non_order_error_passes_through(self):
        """A non-OrderError exception is not caught by _handle_service_error."""
        exc = ValueError("unexpected value error")
        with pytest.raises(ValueError, match="unexpected value error"):
            _handle_service_error(exc)

    def test_runtime_error_passes_through(self):
        """A RuntimeError is not caught by _handle_service_error."""
        exc = RuntimeError("unexpected runtime error")
        with pytest.raises(RuntimeError, match="unexpected runtime error"):
            _handle_service_error(exc)

    def test_key_error_passes_through(self):
        """A KeyError is not caught by _handle_service_error."""
        exc = KeyError("missing_key")
        with pytest.raises(KeyError, match="missing_key"):
            _handle_service_error(exc)
