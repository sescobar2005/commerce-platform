"""Unit tests for Orders API router endpoints.

Tests the five Orders router endpoints:
- POST /orders/ (create order)
- GET /orders/{order_id} (get order)
- GET /orders/ (list orders)
- GET /orders/{order_id}/items (get order items)
- GET /orders/{order_id}/subitems (get order subitems)

Tests use mocks for OrderService methods and verify:
- Correct HTTP status codes
- Correct response schemas
- Authentication requirements
- Buyer ownership and unauthorized access
- Administrator access
- UUID validation
- Idempotency header handling
- Error mapping
- Pagination
- Response schema serialization
- Privacy of error responses
"""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette import status

from src.core.orders.router import (
    create_order,
    get_order,
    get_order_items,
    get_order_subitems,
    list_orders,
    _validate_uuid,
)
from src.core.orders.schemas import (
    OrderCreateRequest,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
    OrderSubitemResponse,
    OrderSummaryResponse,
)
from src.core.orders.services import OrderCreationResult
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
from src.core.security.schemas import CurrentUser


# -----------------------------------------------------------------------
# Test helpers
# ----------------------------------------------------------------------


_TEST_ORDER_ID = UUID("11111111-1111-1111-1111-111111111111")
_TEST_USER_ID = UUID("22222222-2222-2222-2222-222222222222")
_TEST_PRODUCT_ID = UUID("33333333-3333-3333-3333-333333333333")
_TEST_SELLER_ID = UUID("44444444-4444-4444-4444-444444444444")
_TEST_CART_ID = UUID("55555555-5555-5555-5555-555555555555")
_TEST_ORDER_ITEM_ID = UUID("66666666-6666-6666-6666-666666666666")
_TEST_ORDER_SUBITEM_ID = UUID("77777777-7777-7777-7777-777777777777")


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


def _make_order_orm(
    order_id=_TEST_ORDER_ID,
    user_id=_TEST_USER_ID,
    total_amount=Decimal("50.00"),
    status="pending",
    payment_status="pending",
    items=None,
    subitems=None,
):
    """Create a SimpleNamespace acting as an Order ORM instance."""
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


def _make_order_item_orm(
    order_item_id=_TEST_ORDER_ITEM_ID,
    order_id=_TEST_ORDER_ID,
    product_id=_TEST_PRODUCT_ID,
    seller_id=_TEST_SELLER_ID,
    product_name="Test Product",
    product_sku="SKU-001",
    quantity=2,
    price=Decimal("10.00"),
):
    """Create a SimpleNamespace acting as an OrderItem ORM instance."""
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


def _make_order_subitem_orm(
    order_subitem_id=_TEST_ORDER_SUBITEM_ID,
    order_id=_TEST_ORDER_ID,
    seller_id=_TEST_SELLER_ID,
    subtotal=Decimal("20.00"),
    status="pending",
):
    """Create a SimpleNamespace acting as an OrderSubitem ORM instance."""
    return SimpleNamespace(
        order_subitem_id=order_subitem_id,
        order_id=order_id,
        seller_id=seller_id,
        subtotal=subtotal,
        status=status,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


# -----------------------------------------------------------------------
# UUID validation tests
# ----------------------------------------------------------------------


class TestUuidValidation:
    """Tests for UUID validation helper."""

    def test_valid_uuid_passes(self):
        """A valid UUID string passes validation."""
        _validate_uuid(str(_TEST_ORDER_ID))

    def test_invalid_uuid_raises_404(self):
        """An invalid UUID string raises HTTP 404."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_uuid("not-a-uuid")
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Order not found"

    def test_empty_uuid_raises_404(self):
        """An empty string raises HTTP 404."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_uuid("")
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


# -----------------------------------------------------------------------
# Create order tests
# ----------------------------------------------------------------------


class TestCreateOrder:
    """Tests for POST /orders/ endpoint."""

    def test_create_order_success_returns_201(self):
        """Successful order creation returns HTTP 201."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        order_orm = _make_order_orm(
            order_id=_TEST_ORDER_ID,
            user_id=_TEST_USER_ID,
            total_amount=Decimal("20.00"),
        )
        creation_result = OrderCreationResult(order=order_orm, is_new=True)

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_order_from_cart.return_value = creation_result
            mock_service_class.return_value = mock_service

            response = create_order(
                cart_id=str(_TEST_CART_ID),
                idempotency_key=None,
                db=mock_db,
                current_user=mock_current_user,
            )

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_201_CREATED
        import json
        body = json.loads(response.body)
        assert body["order_id"] == str(_TEST_ORDER_ID)
        assert body["user_id"] == str(_TEST_USER_ID)
        assert body["total_amount"] == "20.00"
        assert body["status"] == "pending"
        assert body["payment_status"] == "pending"

        mock_service.create_order_from_cart.assert_called_once_with(
            str(_TEST_CART_ID), mock_current_user, None
        )

    def test_create_order_with_idempotency_key(self):
        """Order creation with idempotency key passes it to service."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")
        order_orm = _make_order_orm(order_id=_TEST_ORDER_ID, user_id=_TEST_USER_ID)
        creation_result = OrderCreationResult(order=order_orm, is_new=False)

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_order_from_cart.return_value = creation_result
            mock_service_class.return_value = mock_service

            result = create_order(
                cart_id=str(_TEST_CART_ID),
                idempotency_key="key-123",
                db=mock_db,
                current_user=mock_current_user,
            )

        assert isinstance(result, JSONResponse)
        assert result.status_code == status.HTTP_200_OK
        import json
        body = json.loads(result.body)
        assert body["order_id"] == str(_TEST_ORDER_ID)

        mock_service.create_order_from_cart.assert_called_once_with(
            str(_TEST_CART_ID), mock_current_user, "key-123"
        )

    def test_create_order_cart_not_found(self):
        """Missing cart returns HTTP 404."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_order_from_cart.side_effect = (
                OrderNotFoundError(str(_TEST_CART_ID))
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                create_order(
                    cart_id=str(_TEST_CART_ID),
                    idempotency_key=None,
                    db=mock_db,
                    current_user=mock_current_user,
                )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Order not found"

    def test_create_order_idempotency_conflict(self):
        """Idempotency conflict returns HTTP 409."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_order_from_cart.side_effect = (
                IdempotencyConflictError("Idempotency conflict")
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                create_order(
                    cart_id=str(_TEST_CART_ID),
                    idempotency_key=None,
                    db=mock_db,
                    current_user=mock_current_user,
                )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert exc_info.value.detail == "Idempotency conflict"

    def test_create_order_insufficient_stock(self):
        """Insufficient stock returns HTTP 409."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_order_from_cart.side_effect = (
                InsufficientStockError(str(_TEST_PRODUCT_ID), 10, 5)
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                create_order(
                    cart_id=str(_TEST_CART_ID),
                    idempotency_key=None,
                    db=mock_db,
                    current_user=mock_current_user,
                )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert exc_info.value.detail == "Insufficient stock"


# -----------------------------------------------------------------------
# Get order tests
# ----------------------------------------------------------------------


class TestGetOrder:
    """Tests for GET /orders/{order_id} endpoint."""

    def test_get_order_success(self):
        """Successful order retrieval returns an OrderResponse."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        order_orm = _make_order_orm(order_id=_TEST_ORDER_ID, user_id=_TEST_USER_ID)

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_order_by_id.return_value = order_orm
            mock_service_class.return_value = mock_service

            response = get_order(
                order_id=str(_TEST_ORDER_ID),
                db=mock_db,
                current_user=mock_current_user,
            )

        assert isinstance(response, OrderResponse)
        assert response.order_id == _TEST_ORDER_ID
        assert response.user_id == _TEST_USER_ID
        mock_service.get_order_by_id.assert_called_once_with(
            str(_TEST_ORDER_ID), mock_current_user
        )

    def test_get_order_invalid_uuid(self):
        """Invalid UUID returns HTTP 404."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        with pytest.raises(HTTPException) as exc_info:
            get_order(
                order_id="not-a-uuid",
                db=mock_db,
                current_user=mock_current_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_get_order_not_found(self):
        """Missing order returns HTTP 404."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_order_by_id.side_effect = OrderNotFoundError(
                str(uuid4())
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                get_order(
                    order_id=str(uuid4()),
                    db=mock_db,
                    current_user=mock_current_user,
                )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_get_order_ownership_denied(self):
        """Order ownership violation returns HTTP 404."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        order_orm = _make_order_orm(order_id=_TEST_ORDER_ID, user_id=_TEST_USER_ID)

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_order_by_id.side_effect = OrderOwnershipError(
                str(_TEST_ORDER_ID), str(_TEST_USER_ID)
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                get_order(
                    order_id=str(_TEST_ORDER_ID),
                    db=mock_db,
                    current_user=mock_current_user,
                )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


# -----------------------------------------------------------------------
# List orders tests
# ----------------------------------------------------------------------


class TestListOrders:
    """Tests for GET /orders/ endpoint."""

    def test_list_orders_success(self):
        """Successful order listing returns an OrderListResponse."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        order_summary_orm = _make_order_orm(
            order_id=_TEST_ORDER_ID,
            user_id=_TEST_USER_ID,
            total_amount=Decimal("50.00"),
        )

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_orders_by_user.return_value = (
                [order_summary_orm],
                1,
            )
            mock_service_class.return_value = mock_service

            response = list_orders(
                skip=0,
                limit=20,
                db=mock_db,
                current_user=mock_current_user,
            )

        assert isinstance(response, OrderListResponse)
        assert response.total == 1
        assert response.skip == 0
        assert response.limit == 20
        assert len(response.orders) == 1
        assert response.orders[0].order_id == _TEST_ORDER_ID
        assert response.orders[0].total_amount == Decimal("50.00")

        mock_service.list_orders_by_user.assert_called_once_with(
            mock_current_user, skip=0, limit=20
        )

    def test_list_orders_pagination_params(self):
        """Pagination parameters are passed to the service."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_orders_by_user.return_value = ([], 0)
            mock_service_class.return_value = mock_service

            list_orders(
                skip=10,
                limit=5,
                db=mock_db,
                current_user=mock_current_user,
            )

        mock_service.list_orders_by_user.assert_called_once_with(
            mock_current_user, skip=10, limit=5
        )

    def test_list_orders_invalid_skip(self):
        """Negative skip returns HTTP 400."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_orders_by_user.side_effect = OrderError(
                "skip must be non-negative"
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                list_orders(
                    skip=-1,
                    limit=20,
                    db=mock_db,
                    current_user=mock_current_user,
                )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Order operation failed"

    def test_list_orders_invalid_limit(self):
        """Zero limit returns HTTP 400."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_orders_by_user.side_effect = OrderError(
                "limit must be positive"
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                list_orders(
                    skip=0,
                    limit=0,
                    db=mock_db,
                    current_user=mock_current_user,
                )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Order operation failed"


# -----------------------------------------------------------------------
# Get order items tests
# ----------------------------------------------------------------------


class TestGetOrderItems:
    """Tests for GET /orders/{order_id}/items endpoint."""

    def test_get_order_items_success(self):
        """Successful item retrieval returns a list of OrderItemResponse."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        item_orm = _make_order_item_orm(
            order_item_id=_TEST_ORDER_ITEM_ID,
            order_id=_TEST_ORDER_ID,
            product_id=_TEST_PRODUCT_ID,
            seller_id=_TEST_SELLER_ID,
        )

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_order_items.return_value = [item_orm]
            mock_service_class.return_value = mock_service

            response = get_order_items(
                order_id=str(_TEST_ORDER_ID),
                db=mock_db,
                current_user=mock_current_user,
            )

        assert isinstance(response, list)
        assert len(response) == 1
        assert isinstance(response[0], OrderItemResponse)
        assert response[0].order_item_id == _TEST_ORDER_ITEM_ID
        assert response[0].product_id == _TEST_PRODUCT_ID
        assert response[0].seller_id == _TEST_SELLER_ID
        assert response[0].product_name == "Test Product"
        assert response[0].quantity == 2
        assert response[0].price == Decimal("10.00")


# -----------------------------------------------------------------------
# Get order subitems tests
# ----------------------------------------------------------------------


class TestGetOrderSubitems:
    """Tests for GET /orders/{order_id}/subitems endpoint."""

    def test_get_order_subitems_success(self):
        """Successful subitem retrieval returns a list of OrderSubitemResponse."""
        mock_db = MagicMock()
        mock_current_user = _make_current_user(user_id="user-1")

        subitem_orm = _make_order_subitem_orm(
            order_subitem_id=_TEST_ORDER_SUBITEM_ID,
            order_id=_TEST_ORDER_ID,
            seller_id=_TEST_SELLER_ID,
        )

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_order_subitems.return_value = [subitem_orm]
            mock_service_class.return_value = mock_service

            response = get_order_subitems(
                order_id=str(_TEST_ORDER_ID),
                db=mock_db,
                current_user=mock_current_user,
            )

        assert isinstance(response, list)
        assert len(response) == 1
        assert isinstance(response[0], OrderSubitemResponse)
        assert response[0].order_subitem_id == _TEST_ORDER_SUBITEM_ID
        assert response[0].seller_id == _TEST_SELLER_ID
        assert response[0].subtotal == Decimal("20.00")
        assert response[0].status == "pending"


# -----------------------------------------------------------------------
# Administrator access tests
# ----------------------------------------------------------------------


class TestAdminAccess:
    """Tests for administrator access to orders."""

    def test_admin_gets_any_order(self):
        """An administrator can retrieve any order."""
        mock_db = MagicMock()
        mock_admin = _make_current_user(user_id="admin-1", is_admin=True)

        order_orm = _make_order_orm(
            order_id=_TEST_ORDER_ID, user_id=_TEST_USER_ID
        )

        with patch(
            "src.core.orders.router.OrderService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_order_by_id.return_value = order_orm
            mock_service_class.return_value = mock_service

            response = get_order(
                order_id=str(_TEST_ORDER_ID),
                db=mock_db,
                current_user=mock_admin,
            )

        assert response.order_id == _TEST_ORDER_ID


# -----------------------------------------------------------------------
# Decimal serialization tests
# ----------------------------------------------------------------------


class TestDecimalSerialization:
    """Tests for Decimal serialization in responses."""

    def test_order_response_decimal_serialization(self):
        """OrderResponse serializes monetary values as decimal strings."""
        order_orm = _make_order_orm(
            order_id=_TEST_ORDER_ID,
            user_id=_TEST_USER_ID,
            total_amount=Decimal("100.99"),
            items=[
                _make_order_item_orm(
                    order_item_id=_TEST_ORDER_ITEM_ID,
                    product_id=_TEST_PRODUCT_ID,
                    seller_id=_TEST_SELLER_ID,
                    price=Decimal("10.00"),
                )
            ],
            subitems=[
                _make_order_subitem_orm(
                    order_subitem_id=_TEST_ORDER_SUBITEM_ID,
                    seller_id=_TEST_SELLER_ID,
                    subtotal=Decimal("20.00"),
                )
            ],
        )

        response = OrderResponse.model_validate(order_orm)
        json_str = response.model_dump_json()

        assert '"total_amount":"100.99"' in json_str
        assert '"price":"10.00"' in json_str
        assert '"subtotal":"20.00"' in json_str
