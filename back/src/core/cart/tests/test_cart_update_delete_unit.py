"""Unit tests for cart update and delete endpoints.

Tests use mocked database sessions - no live database required.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.core.cart.router import delete_cart, update_cart
from src.core.cart.schemas import CartUpdateRequest
from src.core.models.cart import Cart, CartItem


def make_cart(
    cart_id="cart-123",
    user_id="user-123",
    items=None,
    expires_at=None,
    created_at=None,
    last_updated_at=None,
):
    """Create a SimpleNamespace acting as a Cart model instance."""
    if items is None:
        items = []
    if created_at is None:
        created_at = datetime(2024, 1, 1, 12, 0, 0)
    if last_updated_at is None:
        last_updated_at = datetime(2024, 1, 1, 12, 0, 0)
    return SimpleNamespace(
        cart_id=cart_id,
        user_id=user_id,
        items=items,
        expires_at=expires_at,
        created_at=created_at,
        last_updated_at=last_updated_at,
    )


def make_cart_item(
    cart_item_id="item-123",
    cart_id="cart-123",
    product_id="product-456",
    quantity=2,
    price_at_time=29.99,
):
    """Create a SimpleNamespace acting as a CartItem model instance."""
    return SimpleNamespace(
        cart_item_id=cart_item_id,
        cart_id=cart_id,
        product_id=product_id,
        quantity=quantity,
        price_at_time=price_at_time,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


def make_current_user(
    user_id="user-123",
    username="testuser",
    email="test@example.com",
    is_seller=False,
    is_verified=True,
    is_admin=False,
):
    """Create a SimpleNamespace acting as a CurrentUser."""
    return SimpleNamespace(
        user_id=user_id,
        username=username,
        email=email,
        is_seller=is_seller,
        is_verified=is_verified,
        is_admin=is_admin,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


class TestCartUpdate:
    """Tests for updating a cart (PUT /{cart_id})."""

    def setup_method(self):
        self.mock_db = MagicMock()

    def _setup_cart_query(self, cart):
        """Set up mock so db.query(Cart).filter().first() returns cart."""
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = cart
        # db.query() always returns this mock, regardless of argument
        self.mock_db.query.return_value = mock_query

    def test_successful_cart_update(self):
        """Valid cart update should update expires_at."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        new_expires = datetime(2024, 12, 31, 23, 59, 59)
        cart = make_cart(cart_id=cart_id, user_id="user-123", expires_at=None)
        request = CartUpdateRequest(expires_at=new_expires)

        self._setup_cart_query(cart)

        result = update_cart(
            cart_id=cart_id,
            request=request,
            db=self.mock_db,
            current_user=current_user,
        )

        assert result.cart_id == cart_id
        assert result.user_id == "user-123"
        assert result.expires_at == new_expires
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_cart_update_clear_expiration(self):
        """Setting expires_at to None should clear expiration."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        old_expires = datetime(2024, 12, 31, 23, 59, 59)
        cart = make_cart(cart_id=cart_id, user_id="user-123", expires_at=old_expires)
        request = CartUpdateRequest(expires_at=None)

        self._setup_cart_query(cart)

        result = update_cart(
            cart_id=cart_id,
            request=request,
            db=self.mock_db,
            current_user=current_user,
        )

        assert result.expires_at is None

    def test_cart_update_not_found(self):
        """Nonexistent cart ID should raise 404."""
        cart_id = "nonexistent-cart"
        current_user = make_current_user()
        request = CartUpdateRequest(expires_at=datetime(2024, 12, 31))

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.mock_db.query.return_value = mock_query

        with pytest.raises(HTTPException) as exc_info:
            update_cart(
                cart_id=cart_id,
                request=request,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_cart_update_not_owner_raises_404(self):
        """Cart owned by another user should raise 404."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-456")
        request = CartUpdateRequest(expires_at=datetime(2024, 12, 31))

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = cart
        self.mock_db.query.return_value = mock_query

        with pytest.raises(HTTPException) as exc_info:
            update_cart(
                cart_id=cart_id,
                request=request,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_cart_update_unauthenticated_raises_401(self):
        """Unauthenticated cart update should raise 401."""
        cart_id = "cart-123"
        request = CartUpdateRequest(expires_at=datetime(2024, 12, 31))

        with pytest.raises(HTTPException) as exc_info:
            update_cart(
                cart_id=cart_id,
                request=request,
                db=self.mock_db,
                current_user=None,
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cart_update_database_error_raises_exception(self):
        """Database error during update should rollback."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-123")
        request = CartUpdateRequest(expires_at=datetime(2024, 12, 31))

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = cart
        self.mock_db.query.return_value = mock_query
        self.mock_db.commit.side_effect = IntegrityError(
            "constraint violation", params={}, orig=None
        )

        with pytest.raises(HTTPException) as exc_info:
            update_cart(
                cart_id=cart_id,
                request=request,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        self.mock_db.rollback.assert_called_once()

    def test_cart_update_preserves_items(self):
        """Cart update should not affect existing items."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        item = make_cart_item(cart_item_id="item-1", cart_id=cart_id, quantity=2)
        cart = make_cart(cart_id=cart_id, user_id="user-123", items=[item])
        request = CartUpdateRequest(expires_at=datetime(2024, 12, 31))

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = cart
        self.mock_db.query.return_value = mock_query

        result = update_cart(
            cart_id=cart_id,
            request=request,
            db=self.mock_db,
            current_user=current_user,
        )

        assert len(result.items) == 1
        assert result.items[0].cart_item_id == "item-1"
        assert result.items[0].quantity == 2


class TestCartDelete:
    """Tests for deleting a cart (DELETE /{cart_id})."""

    def setup_method(self):
        self.mock_db = MagicMock()

    def _setup_cart_query(self, cart):
        """Configure mock for cart query: query().options().filter().first()"""
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = cart
        self.mock_db.query.return_value = mock_query

    def test_successful_cart_delete(self):
        """Valid cart deletion should succeed and cascade items."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        item = make_cart_item(cart_item_id="item-1", cart_id=cart_id)
        cart = make_cart(cart_id=cart_id, user_id="user-123", items=[item])

        self._setup_cart_query(cart)

        result = delete_cart(
            cart_id=cart_id,
            db=self.mock_db,
            current_user=current_user,
        )

        assert result["message"] == "Cart deleted"
        assert result["cart_id"] == cart_id
        self.mock_db.delete.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_cart_delete_not_found(self):
        """Nonexistent cart ID should raise 404."""
        cart_id = "nonexistent-cart"
        current_user = make_current_user()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.mock_db.query.return_value = mock_query

        with pytest.raises(HTTPException) as exc_info:
            delete_cart(
                cart_id=cart_id,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_cart_delete_not_owner_raises_404(self):
        """Cart owned by another user should raise 404."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-456")

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = cart
        self.mock_db.query.return_value = mock_query

        with pytest.raises(HTTPException) as exc_info:
            delete_cart(
                cart_id=cart_id,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_cart_delete_unauthenticated_raises_401(self):
        """Unauthenticated cart deletion should raise 401."""
        cart_id = "cart-123"

        with pytest.raises(HTTPException) as exc_info:
            delete_cart(
                cart_id=cart_id,
                db=self.mock_db,
                current_user=None,
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cart_delete_database_error_raises_exception(self):
        """Database error during deletion should rollback."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        item = make_cart_item(cart_item_id="item-1", cart_id=cart_id)
        cart = make_cart(cart_id=cart_id, user_id="user-123", items=[item])

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = cart
        self.mock_db.query.return_value = mock_query
        self.mock_db.commit.side_effect = IntegrityError(
            "constraint violation", params={}, orig=None
        )

        with pytest.raises(HTTPException) as exc_info:
            delete_cart(
                cart_id=cart_id,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        self.mock_db.rollback.assert_called_once()
