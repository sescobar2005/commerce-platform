"""Unit tests for cart management endpoints.

Tests use mocked database sessions - no live database required.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from src.core.cart.router import create_cart, get_cart, _cart_to_response
from src.core.cart.schemas import CartItemResponse, CartResponse
from src.core.models.cart import Cart, CartItem


def make_cart(
    cart_id="cart-123",
    user_id="user-123",
    items=None,
    created_at=None,
    last_updated_at=None,
    expires_at=None,
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
        created_at=created_at,
        last_updated_at=last_updated_at,
        expires_at=expires_at,
    )


def make_cart_item(
    cart_item_id="item-123",
    cart_id="cart-123",
    product_id="product-456",
    quantity=2,
    price_at_time=29.99,
    product=None,
):
    """Create a SimpleNamespace acting as a CartItem model instance."""
    return SimpleNamespace(
        cart_item_id=cart_item_id,
        cart_id=cart_id,
        product_id=product_id,
        quantity=quantity,
        price_at_time=price_at_time,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        product=product,
    )


def make_product(
    product_id="product-456",
    name="Test Product",
    sku="SKU-001",
    price=29.99,
):
    """Create a SimpleNamespace acting as a Product model instance."""
    return SimpleNamespace(
        product_id=product_id,
        name=name,
        sku=sku,
        price=price,
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


class TestCartEndpoint:
    """Tests for the cart management endpoints."""

    def setup_method(self):
        self.mock_db = MagicMock()

    def mock_query_chain(self, first_return_value):
        """Set up mock where query().options().filter().first() returns value."""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = first_return_value
        return mock_query

    # === Cart Creation Tests ===

    def test_successful_cart_creation(self):
        """Valid cart creation should return the new cart."""
        current_user = make_current_user()

        # No existing cart found, then cart found after creation
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [None, make_cart()]

        self.mock_db.query.return_value = mock_query

        result = create_cart(db=self.mock_db, current_user=current_user)

        assert isinstance(result, CartResponse)
        assert result.user_id == "user-123"
        assert len(result.items) == 0
        assert result.cart_id is not None

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_cart_creation_returns_existing_cart(self):
        """Creating a cart when one exists should return the existing cart."""
        current_user = make_current_user()
        existing_cart = make_cart(cart_id="cart-existing", user_id="user-123")

        # Existing cart found
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_cart

        self.mock_db.query.return_value = mock_query

        result = create_cart(db=self.mock_db, current_user=current_user)

        assert result.cart_id == "cart-existing"
        assert result.user_id == "user-123"

        # Should not add/commit/refresh since cart already exists
        self.mock_db.add.assert_not_called()
        self.mock_db.commit.assert_not_called()
        self.mock_db.refresh.assert_not_called()

    def test_cart_creation_unauthenticated_raises_401(self):
        """Unauthenticated cart creation should raise 401."""
        with pytest.raises(HTTPException) as exc_info:
            create_cart(db=self.mock_db, current_user=None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cart_creation_database_error_raises_exception(self):
        """Database error during creation should raise an exception."""
        current_user = make_current_user()
        from sqlalchemy.exc import IntegrityError

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.mock_db.query.return_value = mock_query

        self.mock_db.commit.side_effect = IntegrityError(
            "duplicate key", params={}, orig=None
        )

        with pytest.raises(HTTPException) as exc_info:
            create_cart(db=self.mock_db, current_user=current_user)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        self.mock_db.rollback.assert_called_once()

    # === Cart Retrieval Tests ===

    def test_successful_cart_retrieval_by_owner(self):
        """Valid cart ID owned by user should return the cart."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-123")

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = cart

        self.mock_db.query.return_value = mock_query

        result = get_cart(cart_id=cart_id, db=self.mock_db, current_user=current_user)

        assert result.cart_id == "cart-123"
        assert result.user_id == "user-123"
        assert len(result.items) == 0

    def test_cart_retrieval_by_another_user_raises_404(self):
        """Cart owned by another user should raise 404 (information disclosure)."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-456")

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = cart

        self.mock_db.query.return_value = mock_query

        with pytest.raises(HTTPException) as exc_info:
            get_cart(cart_id=cart_id, db=self.mock_db, current_user=current_user)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_cart_retrieval_nonexistent_raises_404(self):
        """Nonexistent cart ID should raise 404."""
        cart_id = "nonexistent-cart"
        current_user = make_current_user()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        self.mock_db.query.return_value = mock_query

        with pytest.raises(HTTPException) as exc_info:
            get_cart(cart_id=cart_id, db=self.mock_db, current_user=current_user)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_cart_retrieval_database_error_raises_exception(self):
        """Database error during retrieval should raise an exception."""
        cart_id = "cart-123"
        current_user = make_current_user()

        self.mock_db.query.side_effect = Exception("DB connection error")

        with pytest.raises(Exception):
            get_cart(cart_id=cart_id, db=self.mock_db, current_user=current_user)

    # === Cart Response Serialization Tests ===

    def test_cart_response_includes_items(self):
        """Cart response should serialize items with product information."""
        current_user = make_current_user(user_id="user-123")
        product = make_product(product_id="product-456", name="Test Product", price=29.99)
        cart_item = make_cart_item(
            cart_item_id="item-123",
            cart_id="cart-123",
            product_id="product-456",
            quantity=2,
            price_at_time=29.99,
            product=product,
        )
        cart = make_cart(cart_id="cart-123", user_id="user-123", items=[cart_item])

        result = _cart_to_response(cart)

        assert isinstance(result, CartResponse)
        assert result.cart_id == "cart-123"
        assert result.user_id == "user-123"
        assert len(result.items) == 1
        assert isinstance(result.items[0], CartItemResponse)
        assert result.items[0].cart_item_id == "item-123"
        assert result.items[0].product_id == "product-456"
        assert result.items[0].quantity == 2
        assert result.items[0].price_at_time == 29.99

    def test_cart_response_empty_items(self):
        """Cart response with no items should return empty items list."""
        cart = make_cart(cart_id="cart-123", user_id="user-123", items=[])

        result = _cart_to_response(cart)

        assert result.items == []
        assert len(result.items) == 0

    def test_cart_response_expires_at_none(self):
        """Cart response with no expiration should have expires_at as None."""
        cart = make_cart(cart_id="cart-123", user_id="user-123", expires_at=None)

        result = _cart_to_response(cart)

        assert result.expires_at is None
