"""Unit tests for OrderService retrieval methods.

Tests read-only order retrieval: get_order_by_id, list_orders_by_user,
get_order_items, and get_order_subitems. Uses mocks for isolated unit
testing of authorization and business logic.
"""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.core.cart.exceptions import CartOwnershipError
from src.core.orders.exceptions import (
    OrderError,
    OrderNotFoundError,
    OrderOwnershipError,
)
from src.core.orders.services import OrderService
from src.core.security.schemas import CurrentUser


# -----------------------------------------------------------------------
# Test helpers
# -----------------------------------------------------------------------


def _make_current_user(user_id="user-1", is_admin=False, is_seller=False):
    """Create a CurrentUser instance."""
    return CurrentUser(
        user_id=user_id,
        username="user1",
        email="user1@example.com",
        is_seller=is_seller,
        is_verified=False,
        is_admin=is_admin,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


def _make_order(
    order_id="order-1",
    user_id="user-1",
    total_amount=Decimal("50.00"),
    status="pending",
    payment_status="pending",
    items=None,
    subitems=None,
):
    """Create a SimpleNamespace acting as an Order model instance."""
    if items is None:
        items = []
    if subitems is None:
        subitems = []
    return SimpleNamespace(
        order_id=order_id,
        user_id=user_id,
        total_amount=total_amount,
        status=status,
        payment_status=payment_status,
        items=items,
        subitems=subitems,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
    )


def _make_order_item(
    order_item_id="item-1",
    order_id="order-1",
    product_id="product-1",
    seller_id="seller-1",
    product_name="Test Product",
    product_sku="SKU-001",
    quantity=2,
    price=Decimal("10.00"),
):
    """Create a SimpleNamespace acting as an OrderItem model instance."""
    return SimpleNamespace(
        order_item_id=order_item_id,
        order_id=order_id,
        product_id=product_id,
        seller_id=seller_id,
        product_name=product_name,
        product_sku=product_sku,
        quantity=quantity,
        price=price,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


def _make_order_subitem(
    order_subitem_id="subitem-1",
    order_id="order-1",
    seller_id="seller-1",
    subtotal=Decimal("20.00"),
    status="pending",
):
    """Create a SimpleNamespace acting as an OrderSubitem model instance."""
    return SimpleNamespace(
        order_subitem_id=order_subitem_id,
        order_id=order_id,
        seller_id=seller_id,
        subtotal=subtotal,
        status=status,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


def _make_service(mock_db=None):
    """Create an OrderService with a mock database session."""
    if mock_db is None:
        mock_db = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.rollback = MagicMock()
    return OrderService(mock_db), mock_db


# -----------------------------------------------------------------------
# get_order_by_id tests
# -----------------------------------------------------------------------


class TestGetOrderById:
    """Tests for OrderService.get_order_by_id."""

    def test_buyer_retrieves_own_order(self):
        """A buyer can retrieve their own order."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        order = _make_order(order_id="order-1", user_id="user-1")
        service.order_repo.get_by_id = MagicMock(return_value=order)

        current_user = _make_current_user(user_id="user-1")
        result = service.get_order_by_id("order-1", current_user)

        assert result is order
        service.order_repo.get_by_id.assert_called_once_with("order-1")

    def test_administrator_retrieves_any_order(self):
        """An administrator can retrieve any order."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        order = _make_order(order_id="order-1", user_id="user-other")
        service.order_repo.get_by_id = MagicMock(return_value=order)

        current_user = _make_current_user(user_id="admin-1", is_admin=True)
        result = service.get_order_by_id("order-1", current_user)

        assert result is order

    def test_buyer_cannot_retrieve_another_users_order(self):
        """A buyer cannot retrieve another user's order."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        order = _make_order(order_id="order-1", user_id="user-other")
        service.order_repo.get_by_id = MagicMock(return_value=order)

        current_user = _make_current_user(user_id="user-1")
        with pytest.raises(OrderOwnershipError):
            service.get_order_by_id("order-1", current_user)

    def test_missing_order_raises_not_found(self):
        """A missing order raises OrderNotFoundError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        service.order_repo.get_by_id = MagicMock(return_value=None)

        current_user = _make_current_user(user_id="user-1")
        with pytest.raises(OrderNotFoundError, match="Order not found"):
            service.get_order_by_id("nonexistent", current_user)

    def test_seller_cannot_retrieve_another_users_order(self):
        """A seller cannot retrieve another user's order even with products in it."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        order = _make_order(order_id="order-1", user_id="buyer-1")
        service.order_repo.get_by_id = MagicMock(return_value=order)

        current_user = _make_current_user(user_id="seller-1", is_seller=True)
        with pytest.raises(OrderOwnershipError):
            service.get_order_by_id("order-1", current_user)

    def test_no_commit_or_rollback_on_success(self):
        """Successful retrieval does not commit or roll back."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        order = _make_order(order_id="order-1", user_id="user-1")
        service.order_repo.get_by_id = MagicMock(return_value=order)

        current_user = _make_current_user(user_id="user-1")
        service.get_order_by_id("order-1", current_user)

        mock_db.commit.assert_not_called()
        mock_db.rollback.assert_not_called()


# -----------------------------------------------------------------------
# list_orders_by_user tests
# -----------------------------------------------------------------------


class TestListOrdersByUser:
    """Tests for OrderService.list_orders_by_user."""

    def test_buyer_lists_only_own_orders(self):
        """A buyer lists only their own orders."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        orders = [
            _make_order(order_id="order-1", user_id="user-1"),
            _make_order(order_id="order-2", user_id="user-1"),
        ]
        service.order_repo.get_by_user_id = MagicMock(return_value=orders)
        service.order_repo.count_by_user_id = MagicMock(return_value=2)

        current_user = _make_current_user(user_id="user-1")
        result_orders, total = service.list_orders_by_user(current_user)

        assert result_orders == orders
        assert total == 2
        service.order_repo.get_by_user_id.assert_called_once_with(
            "user-1", 0, 20
        )
        service.order_repo.count_by_user_id.assert_called_once_with("user-1")

    def test_administrator_lists_own_orders(self):
        """An administrator lists their own orders via get_by_user_id."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        orders = [_make_order(order_id="order-1", user_id="admin-1")]
        service.order_repo.get_by_user_id = MagicMock(return_value=orders)
        service.order_repo.count_by_user_id = MagicMock(return_value=1)

        current_user = _make_current_user(user_id="admin-1", is_admin=True)
        result_orders, total = service.list_orders_by_user(current_user)

        assert result_orders == orders
        assert total == 1
        service.order_repo.get_by_user_id.assert_called_once_with(
            "admin-1", 0, 20
        )

    def test_seller_cannot_use_buyer_order_listing(self):
        """A seller lists only their own orders (as a buyer), not all orders."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        orders = [_make_order(order_id="order-1", user_id="seller-1")]
        service.order_repo.get_by_user_id = MagicMock(return_value=orders)
        service.order_repo.count_by_user_id = MagicMock(return_value=1)

        current_user = _make_current_user(user_id="seller-1", is_seller=True)
        result_orders, total = service.list_orders_by_user(current_user)

        assert result_orders == orders
        assert total == 1
        # Verifies the seller only sees orders where user_id == seller-1
        service.order_repo.get_by_user_id.assert_called_once_with(
            "seller-1", 0, 20
        )

    def test_empty_order_list(self):
        """An empty order list returns an empty list and zero total."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        service.order_repo.get_by_user_id = MagicMock(return_value=[])
        service.order_repo.count_by_user_id = MagicMock(return_value=0)

        current_user = _make_current_user(user_id="user-1")
        result_orders, total = service.list_orders_by_user(current_user)

        assert result_orders == []
        assert total == 0

    def test_pagination_parameters_passed_to_repository(self):
        """Pagination parameters are passed to the repository."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        service.order_repo.get_by_user_id = MagicMock(return_value=[])
        service.order_repo.count_by_user_id = MagicMock(return_value=0)

        current_user = _make_current_user(user_id="user-1")
        service.list_orders_by_user(current_user, skip=10, limit=5)

        service.order_repo.get_by_user_id.assert_called_once_with(
            "user-1", 10, 5
        )

    def test_invalid_skip_raises(self):
        """Negative skip raises OrderError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        current_user = _make_current_user(user_id="user-1")
        with pytest.raises(OrderError, match="skip must be non-negative"):
            service.list_orders_by_user(current_user, skip=-1)

    def test_invalid_limit_raises(self):
        """Zero limit raises OrderError."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        current_user = _make_current_user(user_id="user-1")
        with pytest.raises(OrderError, match="limit must be positive"):
            service.list_orders_by_user(current_user, limit=0)

    def test_no_commit_or_rollback(self):
        """Listing orders does not commit or roll back."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        service.order_repo.get_by_user_id = MagicMock(return_value=[])
        service.order_repo.count_by_user_id = MagicMock(return_value=0)

        current_user = _make_current_user(user_id="user-1")
        service.list_orders_by_user(current_user)

        mock_db.commit.assert_not_called()
        mock_db.rollback.assert_not_called()


# -----------------------------------------------------------------------
# get_order_items tests
# -----------------------------------------------------------------------


class TestGetOrderItems:
    """Tests for OrderService.get_order_items."""

    def test_buyer_retrieves_own_order_items(self):
        """A buyer retrieves all items from their own order."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        order = _make_order(order_id="order-1", user_id="user-1")
        items = [
            _make_order_item(order_item_id="item-1", order_id="order-1"),
            _make_order_item(order_item_id="item-2", order_id="order-1"),
        ]
        service.order_repo.get_by_id = MagicMock(return_value=order)
        service.order_item_repo.get_by_order_id = MagicMock(return_value=items)

        current_user = _make_current_user(user_id="user-1")
        result = service.get_order_items("order-1", current_user)

        assert result == items
        assert len(result) == 2

    def test_buyer_cannot_retrieve_another_users_order_items(self):
        """A buyer cannot retrieve items from another user's order."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        order = _make_order(order_id="order-1", user_id="user-other")
        service.order_repo.get_by_id = MagicMock(return_value=order)

        current_user = _make_current_user(user_id="user-1")
        with pytest.raises(OrderOwnershipError):
            service.get_order_items("order-1", current_user)

    def test_missing_order_items_raises_not_found(self):
        """Missing order raises OrderNotFoundError for items."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        service.order_repo.get_by_id = MagicMock(return_value=None)

        current_user = _make_current_user(user_id="user-1")
        with pytest.raises(OrderNotFoundError):
            service.get_order_items("nonexistent", current_user)

    def test_no_commit_or_rollback(self):
        """Retrieving items does not commit or roll back."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        order = _make_order(order_id="order-1", user_id="user-1")
        service.order_repo.get_by_id = MagicMock(return_value=order)
        service.order_item_repo.get_by_order_id = MagicMock(return_value=[])

        current_user = _make_current_user(user_id="user-1")
        service.get_order_items("order-1", current_user)

        mock_db.commit.assert_not_called()
        mock_db.rollback.assert_not_called()


# -----------------------------------------------------------------------
# get_order_subitems tests
# -----------------------------------------------------------------------


class TestGetOrderSubitems:
    """Tests for OrderService.get_order_subitems."""

    def test_buyer_retrieves_own_order_subitems(self):
        """A buyer retrieves all subitems from their own order."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        order = _make_order(order_id="order-1", user_id="user-1")
        subitems = [
            _make_order_subitem(
                order_subitem_id="subitem-1", order_id="order-1"
            ),
            _make_order_subitem(
                order_subitem_id="subitem-2", order_id="order-1"
            ),
        ]
        service.order_repo.get_by_id = MagicMock(return_value=order)
        service.order_subitem_repo.get_by_order_id = MagicMock(
            return_value=subitems
        )

        current_user = _make_current_user(user_id="user-1")
        result = service.get_order_subitems("order-1", current_user)

        assert result == subitems
        assert len(result) == 2

    def test_buyer_cannot_retrieve_another_users_order_subitems(self):
        """A buyer cannot retrieve subitems from another user's order."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        order = _make_order(order_id="order-1", user_id="user-other")
        service.order_repo.get_by_id = MagicMock(return_value=order)

        current_user = _make_current_user(user_id="user-1")
        with pytest.raises(OrderOwnershipError):
            service.get_order_subitems("order-1", current_user)

    def test_missing_order_subitems_raises_not_found(self):
        """Missing order raises OrderNotFoundError for subitems."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        service.order_repo.get_by_id = MagicMock(return_value=None)

        current_user = _make_current_user(user_id="user-1")
        with pytest.raises(OrderNotFoundError):
            service.get_order_subitems("nonexistent", current_user)

    def test_no_commit_or_rollback(self):
        """Retrieving subitems does not commit or roll back."""
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        service, _ = OrderService(mock_db), mock_db

        order = _make_order(order_id="order-1", user_id="user-1")
        service.order_repo.get_by_id = MagicMock(return_value=order)
        service.order_subitem_repo.get_by_order_id = MagicMock(
            return_value=[]
        )

        current_user = _make_current_user(user_id="user-1")
        service.get_order_subitems("order-1", current_user)

        mock_db.commit.assert_not_called()
        mock_db.rollback.assert_not_called()
