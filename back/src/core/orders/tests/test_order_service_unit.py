"""Unit tests for OrderService.create_order_from_cart.

Tests use mocks for isolated unit testing of business logic,
and SQLite in-memory for integration-style tests of the
transactional flow.

SQLite does not provide PostgreSQL row-level locking semantics.
Integration tests verify database transaction behavior but
do not prove PostgreSQL concurrency guarantees.
"""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.database import Base
from src.core.cart.exceptions import (
    CartError,
    CartNotFoundError,
    CartOwnershipError,
)
from src.core.models.cart import Cart, CartItem
from src.core.models.category import Category
from src.core.models.order import Order, OrderItem, OrderSubitem
from src.core.models.product import Product
from src.core.models.seller import Seller
from src.core.models.store import Store
from src.core.models.user import User
from src.core.orders.exceptions import (
    IdempotencyConflictError,
    InsufficientStockError,
    OrderError,
    ProductInactiveError,
    ProductNotFoundError,
)
from src.core.orders.services import OrderCreationResult, OrderService
from src.core.security.schemas import CurrentUser


# -----------------------------------------------------------------------
# Test helpers
# -----------------------------------------------------------------------


def _make_current_user(user_id="user-1"):
    """Create a CurrentUser instance."""
    return CurrentUser(
        user_id=user_id,
        username="user1",
        email="user1@example.com",
        is_seller=False,
        is_verified=False,
        is_admin=False,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


def _make_cart_item(
    product_id="product-1",
    quantity=2,
    price_at_time=Decimal("10.00"),
):
    """Create a SimpleNamespace acting as a CartItem."""
    return SimpleNamespace(
        product_id=product_id,
        quantity=quantity,
        price_at_time=price_at_time,
    )


def _make_cart(cart_id="cart-1", user_id="user-1", items=None):
    """Create a SimpleNamespace acting as a Cart."""
    if items is None:
        items = []
    return SimpleNamespace(
        cart_id=cart_id,
        user_id=user_id,
        items=items,
    )


def _make_product(
    product_id="product-1",
    store_id="store-1",
    name="Test Product",
    sku="SKU-001",
    price=Decimal("10.00"),
    stock=100,
    reserved_quantity=0,
    is_active=True,
):
    """Create a SimpleNamespace acting as a Product."""
    return SimpleNamespace(
        product_id=product_id,
        store_id=store_id,
        name=name,
        sku=sku,
        price=price,
        stock=stock,
        reserved_quantity=reserved_quantity,
        is_active=is_active,
    )


def _make_service(mock_db=None):
    """Create an OrderService with a mock database session."""
    if mock_db is None:
        mock_db = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.rollback = MagicMock()
    return OrderService(mock_db), mock_db


# -----------------------------------------------------------------------
# Successful creation tests
# -----------------------------------------------------------------------


class TestSuccessfulCreation:
    """Tests for successful order creation."""

    def _setup_successful_service(
        self, cart, products, seller_map, mock_db
    ):
        """Configure mocks for a successful order creation."""
        service, _ = _make_service(mock_db)
        service.cart_repo.get_by_id_for_update = MagicMock(return_value=cart)
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(
            return_value=None
        )
        service.product_inventory_repo.lock_products = MagicMock(
            return_value=products
        )
        service.product_inventory_repo.check_available_stock = MagicMock(
            return_value=True
        )
        service.product_inventory_repo.reserve_quantity = MagicMock()
        service.store_repo.get_seller_ids = MagicMock(return_value=seller_map)
        return service

    def test_single_product_order_creation(self):
        """Single product cart creates one OrderItem and one OrderSubitem."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(
            product_id="product-1",
            quantity=2,
            price_at_time=Decimal("10.00"),
        )
        cart = _make_cart(
            cart_id="cart-1",
            user_id="user-1",
            items=[item],
        )
        product = _make_product(
            product_id="product-1",
            store_id="store-1",
            name="Test Product",
            sku="SKU-001",
            stock=100,
        )
        seller_map = {"store-1": "seller-1"}

        service = self._setup_successful_service(
            cart, [product], seller_map, mock_db
        )
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()

        current_user = _make_current_user("user-1")
        result = service.create_order_from_cart("cart-1", current_user)

        assert isinstance(result, OrderCreationResult)
        assert result.is_new is True

        added_order = result.order
        assert added_order.user_id == "user-1"
        assert added_order.source_cart_id == "cart-1"
        assert added_order.request_fingerprint is not None
        assert added_order.idempotency_key is None
        assert added_order.status == "pending"
        assert added_order.payment_status == "pending"
        assert added_order.total_amount == Decimal("20.00")

        service.order_item_repo.add.assert_called_once()
        added_item = service.order_item_repo.add.call_args[0][0]
        assert isinstance(added_item, OrderItem)
        assert added_item.order_id == added_order.order_id
        assert added_item.product_id == "product-1"
        assert added_item.seller_id == "seller-1"
        assert added_item.product_name == "Test Product"
        assert added_item.product_sku == "SKU-001"
        assert added_item.quantity == 2
        assert added_item.price == Decimal("10.00")

        service.order_subitem_repo.add.assert_called_once()
        added_subitem = service.order_subitem_repo.add.call_args[0][0]
        assert isinstance(added_subitem, OrderSubitem)
        assert added_subitem.order_id == added_order.order_id
        assert added_subitem.seller_id == "seller-1"
        assert added_subitem.subtotal == Decimal("20.00")
        assert added_subitem.status == "pending"

        mock_db.commit.assert_called_once()

        service.product_inventory_repo.reserve_quantity.assert_called_once_with(
            product, 2
        )

    def test_multiple_products_same_seller(self):
        """Multiple products from same seller create one OrderSubitem."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()

        items = [
            _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00")),
            _make_cart_item(product_id="product-2", quantity=3, price_at_time=Decimal("5.00")),
        ]
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=items)
        products = [
            _make_product(product_id="product-1", store_id="store-1", name="Product 1", sku="SKU-001", stock=100),
            _make_product(product_id="product-2", store_id="store-1", name="Product 2", sku="SKU-002", stock=100),
        ]
        seller_map = {"store-1": "seller-1"}

        service = self._setup_successful_service(
            cart, products, seller_map, mock_db
        )
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()

        current_user = _make_current_user("user-1")
        result = service.create_order_from_cart("cart-1", current_user)

        assert result.is_new is True

        assert service.order_item_repo.add.call_count == 2
        assert service.order_subitem_repo.add.call_count == 1
        added_subitem = service.order_subitem_repo.add.call_args[0][0]
        assert added_subitem.seller_id == "seller-1"
        assert added_subitem.subtotal == Decimal("25.00")

        added_order = service.order_repo.add.call_args[0][0]
        assert added_order.total_amount == Decimal("25.00")

        mock_db.commit.assert_called_once()

    def test_multiple_products_multiple_sellers(self):
        """Products from different sellers create multiple OrderSubitems."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()

        items = [
            _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00")),
            _make_cart_item(product_id="product-2", quantity=2, price_at_time=Decimal("20.00")),
        ]
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=items)
        products = [
            _make_product(product_id="product-1", store_id="store-1", name="Product 1", sku="SKU-001", stock=100),
            _make_product(product_id="product-2", store_id="store-2", name="Product 2", sku="SKU-002", stock=100),
        ]
        seller_map = {"store-1": "seller-1", "store-2": "seller-2"}

        service = self._setup_successful_service(
            cart, products, seller_map, mock_db
        )
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()

        current_user = _make_current_user("user-1")
        result = service.create_order_from_cart("cart-1", current_user)

        assert result.is_new is True

        assert service.order_subitem_repo.add.call_count == 2
        subitems = [
            call_args[0][0] for call_args in service.order_subitem_repo.add.call_args_list
        ]
        seller_ids = {s.seller_id for s in subitems}
        assert seller_ids == {"seller-1", "seller-2"}

        subtotal_map = {s.seller_id: s.subtotal for s in subitems}
        assert subtotal_map["seller-1"] == Decimal("10.00")
        assert subtotal_map["seller-2"] == Decimal("40.00")

        added_order = service.order_repo.add.call_args[0][0]
        assert added_order.total_amount == Decimal("50.00")

        mock_db.commit.assert_called_once()

    def test_with_idempotency_key(self):
        """Order creation with idempotency key stores it on the order."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)
        seller_map = {"store-1": "seller-1"}

        service = self._setup_successful_service(
            cart, [product], seller_map, mock_db
        )
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(return_value=None)
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()

        current_user = _make_current_user("user-1")
        result = service.create_order_from_cart(
            "cart-1", current_user, idempotency_key="key-123"
        )

        assert result.is_new is True

        added_order = result.order
        assert added_order.idempotency_key == "key-123"

        service.order_repo.get_by_user_and_idempotency_key.assert_called_once_with(
            "user-1", "key-123"
        )

        mock_db.commit.assert_called_once()

    def test_cart_remains_intact(self):
        """Cart items are not modified after order creation."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=2, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)
        seller_map = {"store-1": "seller-1"}

        service = self._setup_successful_service(
            cart, [product], seller_map, mock_db
        )
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()
        service.cart_repo.delete = MagicMock()

        current_user = _make_current_user("user-1")
        service.create_order_from_cart("cart-1", current_user)

        assert len(cart.items) == 1
        assert cart.items[0].quantity == 2
        assert cart.items[0].price_at_time == Decimal("10.00")

        service.cart_repo.delete.assert_not_called()


# -----------------------------------------------------------------------
# Validation tests
# -----------------------------------------------------------------------


class TestValidationErrors:
    """Tests for validation error handling."""

    def test_missing_cart_raises_not_found(self):
        """Missing cart raises CartNotFoundError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = _make_service(mock_db)
        service.cart_repo.get_by_id_for_update = MagicMock(return_value=None)

        current_user = _make_current_user("user-1")
        with pytest.raises(CartNotFoundError, match="Cart not found"):
            service.create_order_from_cart("cart-1", current_user)

        mock_db.commit.assert_not_called()
        mock_db.rollback.assert_not_called()

    def test_missing_cart_idempotency_retry_returns_existing(self):
        """Missing cart with idempotency key returns existing order if source_cart_id matches."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = _make_service(mock_db)
        service.cart_repo.get_by_id_for_update = MagicMock(return_value=None)

        existing_order = SimpleNamespace(
            order_id="order-1",
            user_id="user-1",
            source_cart_id="cart-1",
            request_fingerprint="fp-abc",
        )
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(
            return_value=existing_order
        )

        current_user = _make_current_user("user-1")
        result = service.create_order_from_cart(
            "cart-1", current_user, idempotency_key="key-123"
        )

        assert result.order is existing_order
        assert result.is_new is False
        mock_db.commit.assert_not_called()

    def test_missing_cart_idempotency_different_cart_raises(self):
        """Missing cart with idempotency key but different source_cart_id raises CartNotFoundError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = _make_service(mock_db)
        service.cart_repo.get_by_id_for_update = MagicMock(return_value=None)

        existing_order = SimpleNamespace(
            order_id="order-1",
            user_id="user-1",
            source_cart_id="cart-other",
            request_fingerprint="fp-abc",
        )
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(
            return_value=existing_order
        )

        current_user = _make_current_user("user-1")
        with pytest.raises(CartNotFoundError):
            service.create_order_from_cart(
                "cart-1", current_user, idempotency_key="key-123"
            )

        mock_db.rollback.assert_not_called()

    def test_cart_ownership_violation(self):
        """Cart belonging to another user raises CartOwnershipError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = _make_service(mock_db)

        cart = _make_cart(cart_id="cart-1", user_id="user-other", items=[])
        service.cart_repo.get_by_id_for_update = MagicMock(return_value=cart)

        current_user = _make_current_user("user-1")
        with pytest.raises(CartOwnershipError):
            service.create_order_from_cart("cart-1", current_user)

        mock_db.rollback.assert_not_called()

    def test_empty_cart_raises_error(self):
        """Empty cart raises CartError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = _make_service(mock_db)

        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[])
        service.cart_repo.get_by_id_for_update = MagicMock(return_value=cart)

        current_user = _make_current_user("user-1")
        with pytest.raises(CartError, match="Cart is empty"):
            service.create_order_from_cart("cart-1", current_user)

        mock_db.rollback.assert_not_called()

    def test_missing_product_raises_error(self):
        """Product not found raises ProductNotFoundError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = _make_service(mock_db)

        item = _make_cart_item(product_id="product-999", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        service.cart_repo.get_by_id_for_update = MagicMock(return_value=cart)
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(return_value=None)
        service.product_inventory_repo.lock_products = MagicMock(
            side_effect=ValueError("Products not found: ['product-999']")
        )

        current_user = _make_current_user("user-1")
        with pytest.raises(ProductNotFoundError):
            service.create_order_from_cart("cart-1", current_user)

        mock_db.rollback.assert_called_once()

    def test_inactive_product_raises_error(self):
        """Inactive product raises ProductInactiveError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = _make_service(mock_db)

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(
            product_id="product-1", store_id="store-1", name="Test", sku="SKU-001",
            stock=100, is_active=False,
        )
        service.cart_repo.get_by_id_for_update = MagicMock(return_value=cart)
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(return_value=None)
        service.product_inventory_repo.lock_products = MagicMock(return_value=[product])
        service.store_repo.get_seller_ids = MagicMock(return_value={"store-1": "seller-1"})

        current_user = _make_current_user("user-1")
        with pytest.raises(ProductInactiveError):
            service.create_order_from_cart("cart-1", current_user)

        mock_db.rollback.assert_called_once()

    def test_insufficient_stock_raises_error(self):
        """Insufficient stock raises InsufficientStockError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = _make_service(mock_db)

        item = _make_cart_item(product_id="product-1", quantity=100, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(
            product_id="product-1", store_id="store-1", name="Test", sku="SKU-001",
            stock=10, reserved_quantity=0, is_active=True,
        )
        service.cart_repo.get_by_id_for_update = MagicMock(return_value=cart)
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(return_value=None)
        service.product_inventory_repo.lock_products = MagicMock(return_value=[product])
        service.product_inventory_repo.check_available_stock = MagicMock(return_value=False)
        service.product_inventory_repo.reserve_quantity = MagicMock()
        service.store_repo.get_seller_ids = MagicMock(return_value={"store-1": "seller-1"})

        current_user = _make_current_user("user-1")
        with pytest.raises(InsufficientStockError):
            service.create_order_from_cart("cart-1", current_user)

        service.product_inventory_repo.reserve_quantity.assert_not_called()
        mock_db.rollback.assert_called_once()

    def test_missing_seller_mapping_raises_error(self):
        """Product with no seller mapping raises OrderError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = _make_service(mock_db)

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(
            product_id="product-1", store_id="store-1", name="Test", sku="SKU-001",
            stock=100, is_active=True,
        )
        service.cart_repo.get_by_id_for_update = MagicMock(return_value=cart)
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(return_value=None)
        service.product_inventory_repo.lock_products = MagicMock(return_value=[product])
        service.product_inventory_repo.check_available_stock = MagicMock(return_value=True)
        service.store_repo.get_seller_ids = MagicMock(return_value={})

        current_user = _make_current_user("user-1")
        with pytest.raises(OrderError, match="No seller mapping"):
            service.create_order_from_cart("cart-1", current_user)

        mock_db.rollback.assert_called_once()

    def test_invalid_quantity_raises_error(self):
        """Non-positive quantity raises OrderError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = _make_service(mock_db)

        item = _make_cart_item(product_id="product-1", quantity=0, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        service.cart_repo.get_by_id_for_update = MagicMock(return_value=cart)

        current_user = _make_current_user("user-1")
        with pytest.raises(OrderError, match="Invalid quantity"):
            service.create_order_from_cart("cart-1", current_user)

        mock_db.rollback.assert_not_called()

    def test_invalid_price_raises_error(self):
        """Non-Decimal price raises OrderError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = _make_service(mock_db)

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=10.00)
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        service.cart_repo.get_by_id_for_update = MagicMock(return_value=cart)

        current_user = _make_current_user("user-1")
        with pytest.raises(OrderError, match="Invalid price"):
            service.create_order_from_cart("cart-1", current_user)

        mock_db.rollback.assert_not_called()


# -----------------------------------------------------------------------
# Idempotency tests
# -----------------------------------------------------------------------


class TestIdempotency:
    """Tests for idempotency behavior."""

    def _setup_idempotent_service(self, cart, products, seller_map, existing_order=None, mock_db=None):
        if mock_db is None:
            mock_db = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.rollback = MagicMock()
        service, _ = _make_service(mock_db)
        service.cart_repo.get_by_id_for_update = MagicMock(return_value=cart)
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(return_value=existing_order)
        service.product_inventory_repo.lock_products = MagicMock(return_value=products)
        service.product_inventory_repo.check_available_stock = MagicMock(return_value=True)
        service.product_inventory_repo.reserve_quantity = MagicMock()
        service.store_repo.get_seller_ids = MagicMock(return_value=seller_map)
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()
        return service, mock_db

    def test_same_key_same_cart_returns_existing(self):
        """Same idempotency key, same cart and fingerprint returns existing order."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)
        existing_order = SimpleNamespace(
            order_id="order-existing",
            user_id="user-1",
            source_cart_id="cart-1",
            request_fingerprint="fp-abc-123",
        )

        service, mock_db = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=existing_order, mock_db=mock_db
        )
        service.product_inventory_repo.lock_products = MagicMock(
            side_effect=lambda ids: [
                _make_product(product_id=pid, store_id="store-1", name="Test", sku="SKU-001", stock=100)
                for pid in ids
            ]
        )
        with patch(
            "src.core.orders.services.generate_cart_fingerprint",
            return_value="fp-abc-123",
        ):
            current_user = _make_current_user("user-1")
            result = service.create_order_from_cart(
                "cart-1", current_user, idempotency_key="key-123"
            )

        assert result.order is existing_order
        assert result.is_new is False
        service.order_repo.add.assert_not_called()
        mock_db.commit.assert_not_called()
        """Same key but different quantity raises IdempotencyConflictError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=5, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)
        existing_order = SimpleNamespace(
            order_id="order-existing",
            user_id="user-1",
            source_cart_id="cart-1",
            request_fingerprint="fp-original",
        )

        service, mock_db = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=existing_order, mock_db=mock_db
        )
        with patch(
            "src.core.orders.services.generate_cart_fingerprint",
            return_value="fp-different",
        ):
            current_user = _make_current_user("user-1")
            with pytest.raises(IdempotencyConflictError):
                service.create_order_from_cart(
                    "cart-1", current_user, idempotency_key="key-123"
                )

        mock_db.rollback.assert_called_once()

    def test_same_key_changed_price_raises_conflict(self):
        """Same key but different price snapshot raises IdempotencyConflictError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("15.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)
        existing_order = SimpleNamespace(
            order_id="order-existing",
            user_id="user-1",
            source_cart_id="cart-1",
            request_fingerprint="fp-original",
        )

        service, mock_db = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=existing_order, mock_db=mock_db
        )
        with patch(
            "src.core.orders.services.generate_cart_fingerprint",
            return_value="fp-different",
        ):
            current_user = _make_current_user("user-1")
            with pytest.raises(IdempotencyConflictError):
                service.create_order_from_cart(
                    "cart-1", current_user, idempotency_key="key-123"
                )

        mock_db.rollback.assert_called_once()

    def test_same_key_different_cart_raises_conflict(self):
        """Same key but different cart_id raises IdempotencyConflictError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-2", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)
        existing_order = SimpleNamespace(
            order_id="order-existing",
            user_id="user-1",
            source_cart_id="cart-1",
            request_fingerprint="fp-original",
        )

        service, mock_db = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=existing_order, mock_db=mock_db
        )
        with patch(
            "src.core.orders.services.generate_cart_fingerprint",
            return_value="fp-original",
        ):
            current_user = _make_current_user("user-1")
            with pytest.raises(IdempotencyConflictError):
                service.create_order_from_cart(
                    "cart-2", current_user, idempotency_key="key-123"
                )

        mock_db.rollback.assert_called_once()

    def test_same_key_different_users_no_conflict(self):
        """Same idempotency key used by different users does not conflict."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-2", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)
        existing_order = SimpleNamespace(
            order_id="order-existing",
            user_id="user-1",
            source_cart_id="cart-1",
            request_fingerprint="fp-abc",
        )

        service, mock_db = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=existing_order, mock_db=mock_db
        )
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(return_value=None)
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()

        current_user = _make_current_user("user-2")
        result = service.create_order_from_cart(
            "cart-1", current_user, idempotency_key="key-123"
        )

        assert result.is_new is True
        added_order = result.order
        assert added_order.user_id == "user-2"
        mock_db.commit.assert_called_once()

    def test_integrity_error_returns_existing_order(self):
        """Concurrent IntegrityError with compatible existing order returns it."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock(side_effect=IntegrityError("duplicate key", None, None))
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)
        existing_order = SimpleNamespace(
            order_id="order-existing",
            user_id="user-1",
            source_cart_id="cart-1",
            request_fingerprint="fp-abc",
        )

        service, _ = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=None, mock_db=mock_db
        )
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(
            side_effect=[None, existing_order]
        )
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()
        exc = IntegrityError("duplicate key", None, None)
        exc.diag = SimpleNamespace(constraint_name="uq_order_user_idempotency_key")
        mock_db.commit = MagicMock(side_effect=exc)
        with patch(
            "src.core.orders.services.generate_cart_fingerprint",
            return_value="fp-abc",
        ):
            current_user = _make_current_user("user-1")
            result = service.create_order_from_cart(
                "cart-1", current_user, idempotency_key="key-123"
            )

        assert result.order is existing_order
        assert result.is_new is False
        mock_db.rollback.assert_called()

    def test_integrity_error_incompatible_raises_conflict(self):
        """Concurrent IntegrityError with incompatible existing order raises IdempotencyConflictError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock(side_effect=IntegrityError("duplicate key", None, None))
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)
        existing_order = SimpleNamespace(
            order_id="order-existing",
            user_id="user-1",
            source_cart_id="cart-1",
            request_fingerprint="fp-different",
        )

        service, _ = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=None, mock_db=mock_db
        )
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(return_value=existing_order)
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()
        with patch(
            "src.core.orders.services.generate_cart_fingerprint",
            return_value="fp-original",
        ):
            current_user = _make_current_user("user-1")
            with pytest.raises(IdempotencyConflictError):
                service.create_order_from_cart(
                    "cart-1", current_user, idempotency_key="key-123"
                )

        mock_db.rollback.assert_called()

    def test_integrity_error_no_existing_order_re_raises(self):
        """IntegrityError with no existing order re-raises the original error."""
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)

        service, _ = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=None, mock_db=mock_db
        )
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(return_value=None)
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()
        # Set commit side_effect AFTER _setup_idempotent_service (which resets it)
        mock_db.commit = MagicMock(side_effect=IntegrityError("fk violation", None, None))
        with patch(
            "src.core.orders.services.generate_cart_fingerprint",
            return_value="fp-original",
        ):
            current_user = _make_current_user("user-1")
            with pytest.raises(IntegrityError):
                service.create_order_from_cart(
                    "cart-1", current_user, idempotency_key="key-123"
                )

        mock_db.rollback.assert_called()

    def test_integrity_error_idempotency_constraint_compatible(self):
        """Confirmed idempotency unique-constraint violation with compatible existing order returns it."""
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)
        existing_order = SimpleNamespace(
            order_id="order-existing",
            user_id="user-1",
            source_cart_id="cart-1",
            request_fingerprint="fp-abc",
        )

        service, _ = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=None, mock_db=mock_db
        )
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(
            side_effect=[None, existing_order]
        )
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()
        exc = IntegrityError("duplicate key", None, None)
        exc.diag = SimpleNamespace(constraint_name="uq_order_user_idempotency_key")
        mock_db.commit = MagicMock(side_effect=exc)
        with patch(
            "src.core.orders.services.generate_cart_fingerprint",
            return_value="fp-abc",
        ):
            current_user = _make_current_user("user-1")
            result = service.create_order_from_cart(
                "cart-1", current_user, idempotency_key="key-123"
            )

        assert result.order is existing_order
        assert result.is_new is False

    def test_integrity_error_idempotency_constraint_incompatible(self):
        """Confirmed idempotency unique-constraint violation with incompatible existing order raises IdempotencyConflictError."""
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)
        existing_order = SimpleNamespace(
            order_id="order-existing",
            user_id="user-1",
            source_cart_id="cart-1",
            request_fingerprint="fp-different",
        )

        service, _ = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=None, mock_db=mock_db
        )
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(return_value=existing_order)
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()
        exc = IntegrityError("duplicate key", None, None)
        exc.diag = SimpleNamespace(constraint_name="uq_order_user_idempotency_key")
        mock_db.commit = MagicMock(side_effect=exc)
        with patch(
            "src.core.orders.services.generate_cart_fingerprint",
            return_value="fp-original",
        ):
            current_user = _make_current_user("user-1")
            with pytest.raises(IdempotencyConflictError):
                service.create_order_from_cart(
                    "cart-1", current_user, idempotency_key="key-123"
                )

    def test_integrity_error_foreign_key_violation_re_raises(self):
        """Foreign-key IntegrityError re-raises the original error."""
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)
        existing_order = SimpleNamespace(
            order_id="order-existing",
            user_id="user-1",
            source_cart_id="cart-1",
            request_fingerprint="fp-abc",
        )

        service, _ = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=None, mock_db=mock_db
        )
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(
            side_effect=[None, existing_order]
        )
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()
        exc = IntegrityError("fk violation", None, None)
        exc.diag = SimpleNamespace(constraint_name="fk_order_user_id")
        mock_db.commit = MagicMock(side_effect=exc)
        with patch(
            "src.core.orders.services.generate_cart_fingerprint",
            return_value="fp-abc",
        ):
            current_user = _make_current_user("user-1")
            with pytest.raises(IntegrityError):
                service.create_order_from_cart(
                    "cart-1", current_user, idempotency_key="key-123"
                )

    def test_integrity_error_check_constraint_violation_re_raises(self):
        """CHECK constraint IntegrityError re-raises the original error."""
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)

        service, _ = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=None, mock_db=mock_db
        )
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(return_value=None)
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()
        exc = IntegrityError("check violation", None, None)
        exc.diag = SimpleNamespace(constraint_name="chk_product_stock_positive")
        mock_db.commit = MagicMock(side_effect=exc)
        with patch(
            "src.core.orders.services.generate_cart_fingerprint",
            return_value="fp-abc",
        ):
            current_user = _make_current_user("user-1")
            with pytest.raises(IntegrityError):
                service.create_order_from_cart(
                    "cart-1", current_user, idempotency_key="key-123"
                )

    def test_integrity_error_unrelated_unique_constraint_re_raises(self):
        """Unrelated unique-constraint IntegrityError re-raises the original error."""
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)

        service, _ = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=None, mock_db=mock_db
        )
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(return_value=None)
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()
        exc = IntegrityError("unique violation", None, None)
        exc.diag = SimpleNamespace(constraint_name="uq_product_sku")
        mock_db.commit = MagicMock(side_effect=exc)
        with patch(
            "src.core.orders.services.generate_cart_fingerprint",
            return_value="fp-abc",
        ):
            current_user = _make_current_user("user-1")
            with pytest.raises(IntegrityError):
                service.create_order_from_cart(
                    "cart-1", current_user, idempotency_key="key-123"
                )

    def test_integrity_error_unknown_constraint_metadata_re_raises(self):
        """IntegrityError with unknown/unavailable constraint metadata re-raises the original error."""
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()

        item = _make_cart_item(product_id="product-1", quantity=1, price_at_time=Decimal("10.00"))
        cart = _make_cart(cart_id="cart-1", user_id="user-1", items=[item])
        product = _make_product(product_id="product-1", store_id="store-1", name="Test", sku="SKU-001", stock=100)

        service, _ = self._setup_idempotent_service(
            cart, [product], {"store-1": "seller-1"},
            existing_order=None, mock_db=mock_db
        )
        service.order_repo.get_by_user_and_idempotency_key = MagicMock(return_value=None)
        service.order_repo.add = MagicMock()
        service.order_item_repo.add = MagicMock()
        service.order_subitem_repo.add = MagicMock()
        exc = IntegrityError("integrity violation", None, None)
        mock_db.commit = MagicMock(side_effect=exc)
        with patch(
            "src.core.orders.services.generate_cart_fingerprint",
            return_value="fp-abc",
        ):
            current_user = _make_current_user("user-1")
            with pytest.raises(IntegrityError):
                service.create_order_from_cart(
                    "cart-1", current_user, idempotency_key="key-123"
                )


# -----------------------------------------------------------------------
# Integration tests with SQLite
# -----------------------------------------------------------------------


class TestSQLiteIntegration:
    """Integration tests using SQLite in-memory database.

    These tests verify actual database transaction behavior.
    SQLite does not provide PostgreSQL row-level locking semantics.
    """

    def _create_session(self) -> Session:
        """Create an in-memory SQLite session with all tables created."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return Session(engine)

    def _create_prerequisite_data(self, session: Session):
        """Create users, stores, sellers, categories, products, cart, cart items."""
        user = User(
            user_id="user-1",
            username="user1",
            email="user1@example.com",
            password_hash="hash",
            is_seller=False,
            is_verified=True,
        )
        seller = Seller(
            seller_id="seller-1",
            store_name="Test Store",
        )
        store = Store(
            store_id="store-1",
            seller_id="seller-1",
            name="Test Store",
            slug="test-store",
        )
        category = Category(
            category_id="category-1",
            name="Electronics",
            slug="electronics",
        )
        product = Product(
            product_id="product-1",
            store_id="store-1",
            category_id="category-1",
            name="Test Product",
            sku="SKU-001",
            price=Decimal("10.00"),
            stock=100,
            reserved_quantity=0,
            is_active=True,
        )
        cart = Cart(
            cart_id="cart-1",
            user_id="user-1",
        )
        cart_item = CartItem(
            cart_item_id="item-1",
            cart_id="cart-1",
            product_id="product-1",
            quantity=2,
            price_at_time=Decimal("10.00"),
        )

        session.add(user)
        session.add(seller)
        session.add(store)
        session.add(category)
        session.add(product)
        session.add(cart)
        session.add(cart_item)
        session.commit()

    def test_integration_successful_order_creation(self):
        """Full order creation flow with SQLite database."""
        session = self._create_session()
        try:
            self._create_prerequisite_data(session)

            cart = session.query(Cart).filter(Cart.cart_id == "cart-1").first()
            product = session.query(Product).filter(Product.product_id == "product-1").first()

            service = OrderService(session)
            current_user = _make_current_user("user-1")

            result = service.create_order_from_cart("cart-1", current_user)

            assert result.is_new is True
            order = result.order
            assert order is not None
            assert order.order_id is not None
            assert order.user_id == "user-1"
            assert order.source_cart_id == "cart-1"
            assert order.request_fingerprint is not None
            assert order.total_amount == Decimal("20.00")
            assert order.status == "pending"
            assert order.payment_status == "pending"

            items = session.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
            assert len(items) == 1
            assert items[0].product_id == "product-1"
            assert items[0].seller_id == "seller-1"
            assert items[0].product_name == "Test Product"
            assert items[0].product_sku == "SKU-001"
            assert items[0].quantity == 2
            assert items[0].price == Decimal("10.00")

            subitems = session.query(OrderSubitem).filter(OrderSubitem.order_id == order.order_id).all()
            assert len(subitems) == 1
            assert subitems[0].seller_id == "seller-1"
            assert subitems[0].subtotal == Decimal("20.00")
            assert subitems[0].status == "pending"

            refreshed_product = session.query(Product).filter(Product.product_id == "product-1").first()
            assert refreshed_product.reserved_quantity == 2

            refreshed_cart = session.query(Cart).filter(Cart.cart_id == "cart-1").first()
            assert refreshed_cart is not None
            assert len(refreshed_cart.items) == 1
        finally:
            session.close()

    def test_integration_rollback_on_failure(self):
        """Failed order creation rolls back all changes including inventory."""
        session = self._create_session()
        try:
            self._create_prerequisite_data(session)

            cart = session.query(Cart).filter(Cart.cart_id == "cart-1").first()

            service = OrderService(session)
            current_user = _make_current_user("user-1")

            cart.items[0].quantity = 999

            with pytest.raises(InsufficientStockError):
                service.create_order_from_cart("cart-1", current_user)

            orders = session.query(Order).all()
            assert len(orders) == 0

            refreshed_product = session.query(Product).filter(Product.product_id == "product-1").first()
            assert refreshed_product.reserved_quantity == 0

            refreshed_cart = session.query(Cart).filter(Cart.cart_id == "cart-1").first()
            assert refreshed_cart is not None
            assert len(refreshed_cart.items) == 1
        finally:
            session.close()

    def test_integration_idempotency_returns_existing(self):
        """Same idempotency key returns existing order on retry."""
        session = self._create_session()
        try:
            self._create_prerequisite_data(session)

            service = OrderService(session)
            current_user = _make_current_user("user-1")

            result1 = service.create_order_from_cart(
                "cart-1", current_user, idempotency_key="key-123"
            )
            assert result1.is_new is True

            service2 = OrderService(session)
            result2 = service2.create_order_from_cart(
                "cart-1", current_user, idempotency_key="key-123"
            )

            assert result2.is_new is False
            assert result2.order.order_id == result1.order.order_id

            orders = session.query(Order).all()
            assert len(orders) == 1
        finally:
            session.close()
