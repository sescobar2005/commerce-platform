"""Unit tests for cart item management endpoints.

Tests use mocked database sessions - no live database required.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.core.cart.router import (
    add_item_to_cart,
    remove_item_from_cart,
    update_cart_item,
)
from src.core.cart.schemas import CartItemAddRequest, CartItemUpdateRequest
from src.core.models.cart import Cart, CartItem
from src.core.models.product import Product


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


def make_product(
    product_id="product-456",
    name="Test Product",
    sku="SKU-001",
    price=29.99,
    stock=100,
    is_active=True,
):
    """Create a SimpleNamespace acting as a Product model instance."""
    return SimpleNamespace(
        product_id=product_id,
        name=name,
        sku=sku,
        price=price,
        stock=stock,
        is_active=is_active,
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


class TestCartItemAdd:
    """Tests for adding items to a cart (POST /{cart_id}/items)."""

    def setup_method(self):
        self.mock_db = MagicMock()

    def _setup_cart_query(self, cart):
        """Configure mock for cart query: query().options().filter().first()"""
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = cart
        return mock_query

    def _setup_product_query(self, product):
        """Configure mock for product query: query().filter().first()"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = product
        return mock_query

    def _setup_queries(self, cart, product):
        """Set up mock_db.query to return cart or product mock based on model class."""
        cart_mock = self._setup_cart_query(cart)
        product_mock = self._setup_product_query(product)

        def query_side_effect(model_class, *args, **kwargs):
            if model_class == Cart:
                return cart_mock
            if model_class == Product:
                return product_mock
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

    def _setup_cart_only_query(self, cart):
        """Set up mock_db.query to return only cart mock."""
        cart_mock = self._setup_cart_query(cart)

        def query_side_effect(model_class, *args, **kwargs):
            return cart_mock

        self.mock_db.query.side_effect = query_side_effect

    def test_successful_add_item(self):
        """Valid product addition should return updated cart."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-123")
        product = make_product(product_id="product-456", stock=100)
        request = CartItemAddRequest(product_id="product-456", quantity=2)

        self._setup_queries(cart, product)

        result = add_item_to_cart(
            cart_id=cart_id,
            request=request,
            db=self.mock_db,
            current_user=current_user,
        )

        assert result.cart_id == cart_id
        assert result.user_id == "user-123"
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_add_item_product_not_found(self):
        """Nonexistent product ID should raise 404."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-123")
        request = CartItemAddRequest(product_id="product-nonexistent", quantity=2)

        self._setup_queries(cart, None)

        with pytest.raises(HTTPException) as exc_info:
            add_item_to_cart(
                cart_id=cart_id,
                request=request,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_add_item_inactive_product_raises_404(self):
        """Inactive product should raise 404 (information disclosure)."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-123")
        product = make_product(is_active=False)
        request = CartItemAddRequest(product_id="product-456", quantity=2)

        self._setup_queries(cart, product)

        with pytest.raises(HTTPException) as exc_info:
            add_item_to_cart(
                cart_id=cart_id,
                request=request,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_add_item_insufficient_stock_raises_409(self):
        """Insufficient stock should raise 409."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-123")
        product = make_product(stock=1)  # Only 1 in stock, requesting 2
        request = CartItemAddRequest(product_id="product-456", quantity=2)

        self._setup_queries(cart, product)

        with pytest.raises(HTTPException) as exc_info:
            add_item_to_cart(
                cart_id=cart_id,
                request=request,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "stock" in exc_info.value.detail.lower()

    def test_add_item_invalid_quantity_raises_validation_error(self):
        """Invalid quantity (zero or negative) should raise ValidationError."""
        with pytest.raises(Exception):
            CartItemAddRequest(product_id="product-456", quantity=0)

    def test_add_item_increments_existing_quantity(self):
        """Adding existing product should increment quantity."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        existing_item = make_cart_item(
            cart_item_id="item-1",
            cart_id=cart_id,
            product_id="product-456",
            quantity=2,
            price_at_time=29.99,
        )
        cart = make_cart(cart_id=cart_id, user_id="user-123", items=[existing_item])
        product = make_product(product_id="product-456", stock=100)
        request = CartItemAddRequest(product_id="product-456", quantity=3)

        self._setup_queries(cart, product)

        add_item_to_cart(
            cart_id=cart_id,
            request=request,
            db=self.mock_db,
            current_user=current_user,
        )

        # Quantity should be incremented to 5
        assert existing_item.quantity == 5
        self.mock_db.commit.assert_called_once()

    def test_add_item_price_snapshot_from_database(self):
        """Price should come from database, not client."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-123")
        product = make_product(product_id="product-456", price=49.99, stock=100)
        request = CartItemAddRequest(product_id="product-456", quantity=1)

        self._setup_queries(cart, product)

        add_item_to_cart(
            cart_id=cart_id,
            request=request,
            db=self.mock_db,
            current_user=current_user,
        )

        # Verify the added item has the database price snapshot
        added_item = self.mock_db.add.call_args[0][0]
        assert added_item.price_at_time == 49.99
        assert str(added_item.product_id) == "product-456"
        assert added_item.quantity == 1

    def test_add_item_cart_not_found(self):
        """Nonexistent cart ID should raise 404."""
        cart_id = "nonexistent-cart"
        current_user = make_current_user()
        request = CartItemAddRequest(product_id="product-456", quantity=2)

        self._setup_cart_only_query(None)

        with pytest.raises(HTTPException) as exc_info:
            add_item_to_cart(
                cart_id=cart_id,
                request=request,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_add_item_not_cart_owner_raises_404(self):
        """Cart owned by another user should raise 404."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-456")
        request = CartItemAddRequest(product_id="product-456", quantity=2)

        self._setup_cart_only_query(cart)

        with pytest.raises(HTTPException) as exc_info:
            add_item_to_cart(
                cart_id=cart_id,
                request=request,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_add_item_database_error_raises_exception(self):
        """Database error during add should rollback."""
        cart_id = "cart-123"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-123")
        product = make_product(stock=100)
        request = CartItemAddRequest(product_id="product-456", quantity=2)

        self._setup_queries(cart, product)
        self.mock_db.commit.side_effect = IntegrityError(
            "duplicate key", params={}, orig=None
        )

        with pytest.raises(HTTPException) as exc_info:
            add_item_to_cart(
                cart_id=cart_id,
                request=request,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        self.mock_db.rollback.assert_called_once()


class TestCartItemUpdate:
    """Tests for updating cart item quantity (PUT /{cart_id}/items/{item_id})."""

    def setup_method(self):
        self.mock_db = MagicMock()

    def _setup_cart_query(self, cart):
        """Configure mock for cart query: query().options().filter().first()"""
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = cart
        return mock_query

    def _setup_product_query(self, product):
        """Configure mock for product query: query().filter().first()"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = product
        return mock_query

    def _setup_queries(self, cart, product):
        """Set up mock_db.query to return cart or product mock based on model class."""
        cart_mock = self._setup_cart_query(cart)
        product_mock = self._setup_product_query(product)

        def query_side_effect(model_class, *args, **kwargs):
            if model_class == Cart:
                return cart_mock
            if model_class == Product:
                return product_mock
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

    def test_successful_update_quantity(self):
        """Valid quantity update should return updated cart."""
        cart_id = "cart-123"
        item_id = "item-123"
        current_user = make_current_user(user_id="user-123")
        item = make_cart_item(cart_item_id=item_id, cart_id=cart_id, quantity=2)
        cart = make_cart(cart_id=cart_id, user_id="user-123", items=[item])
        product = make_product(product_id="product-456", stock=100)
        request = CartItemUpdateRequest(quantity=5)

        self._setup_queries(cart, product)

        result = update_cart_item(
            cart_id=cart_id,
            item_id=item_id,
            request=request,
            db=self.mock_db,
            current_user=current_user,
        )

        assert item.quantity == 5
        self.mock_db.commit.assert_called_once()

    def test_update_item_not_found(self):
        """Nonexistent item ID should raise 404."""
        cart_id = "cart-123"
        item_id = "item-nonexistent"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-123")
        request = CartItemUpdateRequest(quantity=5)

        self._setup_cart_query(cart)

        with pytest.raises(HTTPException) as exc_info:
            update_cart_item(
                cart_id=cart_id,
                item_id=item_id,
                request=request,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_update_item_cart_not_owner_raises_404(self):
        """Cart owned by another user should raise 404."""
        cart_id = "cart-123"
        item_id = "item-123"
        current_user = make_current_user(user_id="user-123")
        item = make_cart_item(cart_item_id=item_id, cart_id=cart_id)
        cart = make_cart(cart_id=cart_id, user_id="user-456", items=[item])
        request = CartItemUpdateRequest(quantity=5)

        self._setup_cart_query(cart)

        with pytest.raises(HTTPException) as exc_info:
            update_cart_item(
                cart_id=cart_id,
                item_id=item_id,
                request=request,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_update_item_invalid_quantity(self):
        """Invalid quantity (zero or negative) should raise ValidationError."""
        with pytest.raises(Exception):
            CartItemUpdateRequest(quantity=0)

    def test_update_item_insufficient_stock_raises_409(self):
        """Insufficient stock should raise 409."""
        cart_id = "cart-123"
        item_id = "item-123"
        current_user = make_current_user(user_id="user-123")
        item = make_cart_item(cart_item_id=item_id, cart_id=cart_id, quantity=2)
        cart = make_cart(cart_id=cart_id, user_id="user-123", items=[item])
        product = make_product(product_id="product-456", stock=1)
        request = CartItemUpdateRequest(quantity=5)

        self._setup_queries(cart, product)

        with pytest.raises(HTTPException) as exc_info:
            update_cart_item(
                cart_id=cart_id,
                item_id=item_id,
                request=request,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "stock" in exc_info.value.detail.lower()

    def test_update_item_price_snapshot_preserved(self):
        """Price snapshot should be preserved during update."""
        cart_id = "cart-123"
        item_id = "item-123"
        current_user = make_current_user(user_id="user-123")
        item = make_cart_item(
            cart_item_id=item_id,
            cart_id=cart_id,
            product_id="product-456",
            quantity=2,
            price_at_time=19.99,  # Original price snapshot
        )
        cart = make_cart(cart_id=cart_id, user_id="user-123", items=[item])
        product = make_product(product_id="product-456", price=49.99, stock=100)
        request = CartItemUpdateRequest(quantity=5)

        self._setup_queries(cart, product)

        update_cart_item(
            cart_id=cart_id,
            item_id=item_id,
            request=request,
            db=self.mock_db,
            current_user=current_user,
        )

        # Quantity updated but price snapshot preserved
        assert item.quantity == 5
        assert item.price_at_time == 19.99


class TestCartItemRemove:
    """Tests for removing cart items (DELETE /{cart_id}/items/{item_id})."""

    def setup_method(self):
        self.mock_db = MagicMock()

    def _setup_cart_query(self, cart):
        """Configure mock for cart query: query().filter().first()"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = cart
        return mock_query

    def test_successful_remove_item(self):
        """Valid item removal should succeed."""
        cart_id = "cart-123"
        item_id = "item-123"
        current_user = make_current_user(user_id="user-123")
        item = make_cart_item(cart_item_id=item_id, cart_id=cart_id)
        cart = make_cart(cart_id=cart_id, user_id="user-123", items=[item])

        def query_side_effect(model_class, *args, **kwargs):
            if model_class == Cart:
                cm = MagicMock()
                cm.filter.return_value = cm
                cm.first.return_value = cart
                return cm
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        result = remove_item_from_cart(
            cart_id=cart_id,
            item_id=item_id,
            db=self.mock_db,
            current_user=current_user,
        )

        assert result["message"] == "Item removed from cart"
        assert result["cart_id"] == cart_id
        assert result["item_id"] == item_id
        self.mock_db.delete.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_remove_item_not_found(self):
        """Nonexistent item ID should raise 404."""
        cart_id = "cart-123"
        item_id = "item-nonexistent"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-123", items=[])

        def query_side_effect(model_class, *args, **kwargs):
            if model_class == Cart:
                cm = MagicMock()
                cm.filter.return_value = cm
                cm.first.return_value = cart
                return cm
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        with pytest.raises(HTTPException) as exc_info:
            remove_item_from_cart(
                cart_id=cart_id,
                item_id=item_id,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_remove_item_cart_not_owner_raises_404(self):
        """Cart owned by another user should raise 404."""
        cart_id = "cart-123"
        item_id = "item-123"
        current_user = make_current_user(user_id="user-123")
        cart = make_cart(cart_id=cart_id, user_id="user-456")

        def query_side_effect(model_class, *args, **kwargs):
            if model_class == Cart:
                cm = MagicMock()
                cm.filter.return_value = cm
                cm.first.return_value = cart
                return cm
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        with pytest.raises(HTTPException) as exc_info:
            remove_item_from_cart(
                cart_id=cart_id,
                item_id=item_id,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_remove_item_cart_not_found(self):
        """Nonexistent cart ID should raise 404."""
        cart_id = "nonexistent-cart"
        item_id = "item-123"
        current_user = make_current_user()

        def query_side_effect(model_class, *args, **kwargs):
            if model_class == Cart:
                cm = MagicMock()
                cm.filter.return_value = cm
                cm.first.return_value = None
                return cm
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        with pytest.raises(HTTPException) as exc_info:
            remove_item_from_cart(
                cart_id=cart_id,
                item_id=item_id,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_remove_item_database_error_raises_exception(self):
        """Database error during removal should rollback."""
        cart_id = "cart-123"
        item_id = "item-123"
        current_user = make_current_user(user_id="user-123")
        item = make_cart_item(cart_item_id=item_id, cart_id=cart_id)
        cart = make_cart(cart_id=cart_id, user_id="user-123", items=[item])

        def query_side_effect(model_class, *args, **kwargs):
            if model_class == Cart:
                cm = MagicMock()
                cm.filter.return_value = cm
                cm.first.return_value = cart
                return cm
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect
        self.mock_db.commit.side_effect = IntegrityError(
            "constraint violation", params={}, orig=None
        )

        with pytest.raises(HTTPException) as exc_info:
            remove_item_from_cart(
                cart_id=cart_id,
                item_id=item_id,
                db=self.mock_db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        self.mock_db.rollback.assert_called_once()
