"""Unit tests for cart concurrency coordination (row-level locking).

Tests verify that CartService mutations acquire a row-level lock on
the parent Cart row before reading or modifying cart items, and that
normal cart reads do not acquire exclusive locks.

SQLite does not provide PostgreSQL row-level locking semantics. These
tests verify that the correct SQLAlchemy query methods are called
(``with_for_update()`` on the locking path, not on the normal read
path). Actual row-locking/concurrency verification must be done with
PostgreSQL integration tests against ``plataforma_comercio_test``.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.core.cart.repositories import CartRepository
from src.core.cart.services import CartService
from src.core.cart.exceptions import (
    CartNotFoundError,
    CartOwnershipError,
)
from src.core.models.cart import Cart
from src.core.security.schemas import CurrentUser


class TestCartRepositoryLocking:
    """Tests for CartRepository row-level locking methods."""

    def test_get_by_id_for_update_calls_with_for_update(self):
        """get_by_id_for_update should call with_for_update() on the query."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mock_query.first.return_value = None

        repo = CartRepository(mock_db)
        repo.get_by_id_for_update("cart-123")

        mock_db.query.assert_called_once_with(Cart)
        mock_query.with_for_update.assert_called_once()

    def test_get_by_id_does_not_call_with_for_update(self):
        """Normal get_by_id should NOT call with_for_update()."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        repo = CartRepository(mock_db)
        repo.get_by_id("cart-123")

        mock_db.query.assert_called_once_with(Cart)
        mock_query.with_for_update.assert_not_called()

    def test_get_by_id_for_update_returns_cart(self):
        """get_by_id_for_update should return the locked cart."""
        mock_cart = MagicMock(spec=Cart)
        mock_cart.cart_id = "cart-123"
        mock_cart.user_id = "user-1"

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mock_query.first.return_value = mock_cart

        repo = CartRepository(mock_db)
        result = repo.get_by_id_for_update("cart-123")

        assert result is mock_cart
        mock_query.with_for_update.assert_called_once()


class TestCartServiceLockedCart:
    """Tests for CartService _get_locked_cart helper."""

    def _make_service(self, mock_db=None):
        if mock_db is None:
            mock_db = MagicMock()
        return CartService(mock_db), mock_db

    def _make_current_user(self, user_id="user-1"):
        return CurrentUser(
            user_id=user_id,
            username="user1",
            email="user1@example.com",
            is_seller=False,
            is_verified=False,
            is_admin=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

    def test_locked_cart_returns_cart_when_owner(self):
        """_get_locked_cart should return the cart when user is the owner."""
        mock_cart = MagicMock(spec=Cart)
        mock_cart.cart_id = "cart-123"
        mock_cart.user_id = "user-1"

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mock_query.first.return_value = mock_cart

        service, _ = self._make_service(mock_db)
        current_user = self._make_current_user("user-1")

        result = service._get_locked_cart("cart-123", current_user)

        assert result is mock_cart
        mock_query.with_for_update.assert_called_once()

    def test_locked_cart_raises_not_found_when_missing(self):
        """_get_locked_cart should raise CartNotFoundError when cart missing."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mock_query.first.return_value = None

        service, _ = self._make_service(mock_db)
        current_user = self._make_current_user("user-1")

        with pytest.raises(CartNotFoundError, match="Cart not found"):
            service._get_locked_cart("cart-123", current_user)

    def test_locked_cart_raises_ownership_when_not_owner(self):
        """_get_locked_cart should raise CartOwnershipError for wrong user."""
        mock_cart = MagicMock(spec=Cart)
        mock_cart.cart_id = "cart-123"
        mock_cart.user_id = "user-other"

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mock_query.first.return_value = mock_cart

        service, _ = self._make_service(mock_db)
        current_user = self._make_current_user("user-1")

        with pytest.raises(CartOwnershipError):
            service._get_locked_cart("cart-123", current_user)

    def test_normal_get_cart_does_not_lock(self):
        """get_cart should NOT call with_for_update() (normal read)."""
        mock_cart = MagicMock(spec=Cart)
        mock_cart.cart_id = "cart-123"
        mock_cart.user_id = "user-1"

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_cart

        service, _ = self._make_service(mock_db)
        current_user = self._make_current_user("user-1")

        result = service.get_cart("cart-123", current_user)

        assert result is mock_cart
        mock_query.with_for_update.assert_not_called()


class TestCartServiceMutationLocking:
    """Tests that mutation methods lock the cart before modifying items."""

    def _make_service(self, mock_db=None):
        if mock_db is None:
            mock_db = MagicMock()
        return CartService(mock_db), mock_db

    def _make_current_user(self, user_id="user-1"):
        return CurrentUser(
            user_id=user_id,
            username="user1",
            email="user1@example.com",
            is_seller=False,
            is_verified=False,
            is_admin=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

    def test_add_item_locks_cart_before_reading_items(self):
        """add_item should lock the cart row before accessing items."""
        mock_cart = MagicMock(spec=Cart)
        mock_cart.cart_id = "cart-123"
        mock_cart.user_id = "user-1"
        mock_cart.items = []

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mock_query.first.return_value = mock_cart

        # Product lookup returns a mock product
        mock_product = MagicMock()
        mock_product.product_id = "product-1"
        mock_product.is_active = True
        mock_product.stock = 100
        mock_product.price = 10.00

        # The second query (Product) returns the mock product
        product_query = MagicMock()
        product_query.filter.return_value = product_query
        product_query.first.return_value = mock_product

        # First query (Cart) returns mock_cart query chain
        cart_query = MagicMock()
        cart_query.options.return_value = cart_query
        cart_query.filter.return_value = cart_query
        cart_query.with_for_update.return_value = cart_query
        cart_query.first.return_value = mock_cart

        mock_db.query.side_effect = [cart_query, product_query]

        service, _ = self._make_service(mock_db)
        current_user = self._make_current_user("user-1")

        with patch.object(
            service.item_repo, "get_by_cart_and_product", return_value=None
        ) as mock_get_item, patch.object(
            service.item_repo, "commit"
        ) as mock_commit, patch.object(
            service.item_repo, "refresh"
        ) as mock_refresh, patch.object(
            service.item_repo, "add"
        ) as mock_add:
            service.add_item("cart-123", "product-1", 1, current_user)

        # Verify cart was locked (with_for_update called on cart query)
        cart_query.with_for_update.assert_called_once()
        # Verify item repo add was called (item was created)
        mock_add.assert_called_once()
        mock_commit.assert_called_once()

    def test_add_item_ownership_checked_before_product_validation(self):
        """add_item should verify ownership before querying products."""
        mock_cart = MagicMock(spec=Cart)
        mock_cart.cart_id = "cart-123"
        mock_cart.user_id = "user-other"  # Not the current user

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mock_query.first.return_value = mock_cart

        service, _ = self._make_service(mock_db)
        current_user = self._make_current_user("user-1")

        with pytest.raises(CartOwnershipError):
            service.add_item("cart-123", "product-1", 1, current_user)

        # Product query should never be reached due to ownership check
        assert mock_db.query.call_count == 1  # Only the cart query

    def test_add_item_missing_cart_raises_not_found(self):
        """add_item should raise CartNotFoundError when cart does not exist."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mock_query.first.return_value = None

        service, _ = self._make_service(mock_db)
        current_user = self._make_current_user("user-1")

        with pytest.raises(CartNotFoundError):
            service.add_item("cart-123", "product-1", 1, current_user)

    def test_update_item_locks_cart_before_reading_items(self):
        """update_item should lock the cart row before accessing items."""
        mock_cart = MagicMock(spec=Cart)
        mock_cart.cart_id = "cart-123"
        mock_cart.user_id = "user-1"

        # Mock cart item
        mock_item = MagicMock()
        mock_item.cart_item_id = "item-1"
        mock_item.product_id = "product-1"
        mock_cart.items = [mock_item]

        mock_db = MagicMock()
        cart_query = MagicMock()
        cart_query.options.return_value = cart_query
        cart_query.filter.return_value = cart_query
        cart_query.with_for_update.return_value = cart_query
        cart_query.first.return_value = mock_cart

        product_query = MagicMock()
        product_query.filter.return_value = product_query
        product_query.first.return_value = MagicMock(
            product_id="product-1", is_active=True, stock=100, price=10.00
        )

        mock_db.query.side_effect = [cart_query, product_query]

        service, _ = self._make_service(mock_db)
        current_user = self._make_current_user("user-1")

        service.item_repo.commit = MagicMock()
        service.item_repo.refresh = MagicMock()
        service.item_repo.add = MagicMock()

        service.update_item("cart-123", "item-1", 2, current_user)

        cart_query.with_for_update.assert_called_once()
        service.item_repo.commit.assert_called_once()

    def test_remove_item_locks_cart_before_reading_items(self):
        """remove_item should lock the cart row before accessing items."""
        mock_cart = MagicMock(spec=Cart)
        mock_cart.cart_id = "cart-123"
        mock_cart.user_id = "user-1"

        mock_item = MagicMock()
        mock_item.cart_item_id = "item-1"
        mock_cart.items = [mock_item]

        mock_db = MagicMock()
        cart_query = MagicMock()
        cart_query.options.return_value = cart_query
        cart_query.filter.return_value = cart_query
        cart_query.with_for_update.return_value = cart_query
        cart_query.first.return_value = mock_cart

        mock_db.query.return_value = cart_query

        service, _ = self._make_service(mock_db)
        current_user = self._make_current_user("user-1")

        service.item_repo.commit = MagicMock()
        service.item_repo.delete = MagicMock()

        service.remove_item("cart-123", "item-1", current_user)

        cart_query.with_for_update.assert_called_once()
        service.item_repo.delete.assert_called_once_with(mock_item)
        service.item_repo.commit.assert_called_once()
