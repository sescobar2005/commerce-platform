"""Unit tests for Orders API Pydantic schemas.

Tests validate schema construction, field validation, Decimal
serialization, ORM compatibility, and privacy boundaries.
"""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.core.orders.schemas import (
    OrderCreateRequest,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
    OrderSubitemResponse,
    OrderSummaryResponse,
)


# -----------------------------------------------------------------------
# OrderCreateRequest tests
# -----------------------------------------------------------------------


class TestOrderCreateRequest:
    """Tests for the order creation request schema."""

    def test_valid_order_creation_request(self):
        """A valid cart_id produces a valid OrderCreateRequest."""
        cart_id = uuid4()
        request = OrderCreateRequest(cart_id=cart_id)
        assert request.cart_id == cart_id
        assert isinstance(request.cart_id, UUID)

    def test_order_creation_request_from_string_uuid(self):
        """OrderCreateRequest accepts a UUID string."""
        cart_id_str = str(uuid4())
        request = OrderCreateRequest(cart_id=cart_id_str)
        assert request.cart_id == UUID(cart_id_str)

    def test_invalid_cart_uuid_raises(self):
        """An invalid UUID string raises ValidationError."""
        with pytest.raises(ValidationError):
            OrderCreateRequest(cart_id="not-a-uuid")

    def test_missing_cart_id_raises(self):
        """A missing cart_id raises ValidationError."""
        with pytest.raises(ValidationError):
            OrderCreateRequest()

    def test_no_server_controlled_fields_in_request(self):
        """OrderCreateRequest must not accept server-controlled fields."""
        # cart_id is the only allowed field; idempotency_key comes from header
        request = OrderCreateRequest(cart_id=uuid4())
        request_dict = request.model_dump()
        assert set(request_dict.keys()) == {"cart_id"}
        assert "total_amount" not in request_dict
        assert "seller_id" not in request_dict
        assert "status" not in request_dict
        assert "payment_status" not in request_dict
        assert "idempotency_key" not in request_dict
        assert "request_fingerprint" not in request_dict


# -----------------------------------------------------------------------
# OrderItemResponse tests
# -----------------------------------------------------------------------


class TestOrderItemResponse:
    """Tests for the order item response schema."""

    def test_valid_order_item_response(self):
        """A valid order item produces a valid OrderItemResponse."""
        item = OrderItemResponse(
            order_item_id=uuid4(),
            product_id=uuid4(),
            seller_id=uuid4(),
            product_name="Test Product",
            product_sku="SKU-001",
            quantity=2,
            price=Decimal("10.00"),
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        assert item.product_name == "Test Product"
        assert item.product_sku == "SKU-001"
        assert item.quantity == 2
        assert item.price == Decimal("10.00")

    def test_nullable_product_sku(self):
        """product_sku can be None."""
        item = OrderItemResponse(
            order_item_id=uuid4(),
            product_id=uuid4(),
            seller_id=uuid4(),
            product_name="Test Product",
            product_sku=None,
            quantity=1,
            price=Decimal("5.00"),
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        assert item.product_sku is None

    def test_invalid_quantity_raises(self):
        """Non-positive quantity raises ValidationError."""
        with pytest.raises(ValidationError):
            OrderItemResponse(
                order_item_id=uuid4(),
                product_id=uuid4(),
                seller_id=uuid4(),
                product_name="Test Product",
                quantity=0,
                price=Decimal("10.00"),
                created_at=datetime(2024, 1, 1, 12, 0, 0),
            )

    def test_negative_quantity_raises(self):
        """Negative quantity raises ValidationError."""
        with pytest.raises(ValidationError):
            OrderItemResponse(
                order_item_id=uuid4(),
                product_id=uuid4(),
                seller_id=uuid4(),
                product_name="Test Product",
                quantity=-1,
                price=Decimal("10.00"),
                created_at=datetime(2024, 1, 1, 12, 0, 0),
            )


# -----------------------------------------------------------------------
# OrderSubitemResponse tests
# -----------------------------------------------------------------------


class TestOrderSubitemResponse:
    """Tests for the order subitem response schema."""

    def test_valid_subitem_response(self):
        """A valid subitem produces a valid OrderSubitemResponse."""
        subitem = OrderSubitemResponse(
            order_subitem_id=uuid4(),
            seller_id=uuid4(),
            subtotal=Decimal("25.00"),
            status="pending",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        assert subitem.subtotal == Decimal("25.00")
        assert subitem.status == "pending"

    def test_negative_subtotal_raises(self):
        """Negative subtotal raises ValidationError."""
        with pytest.raises(ValidationError):
            OrderSubitemResponse(
                order_subitem_id=uuid4(),
                seller_id=uuid4(),
                subtotal=Decimal("-5.00"),
                status="pending",
                created_at=datetime(2024, 1, 1, 12, 0, 0),
            )


# -----------------------------------------------------------------------
# OrderSummaryResponse tests
# -----------------------------------------------------------------------


class TestOrderSummaryResponse:
    """Tests for the order summary response schema."""

    def test_valid_order_summary(self):
        """A valid order produces a valid OrderSummaryResponse."""
        summary = OrderSummaryResponse(
            order_id=uuid4(),
            total_amount=Decimal("50.00"),
            status="pending",
            payment_status="pending",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        assert summary.total_amount == Decimal("50.00")
        assert summary.status == "pending"
        assert summary.payment_status == "pending"

    def test_negative_total_amount_raises(self):
        """Negative total_amount raises ValidationError."""
        with pytest.raises(ValidationError):
            OrderSummaryResponse(
                order_id=uuid4(),
                total_amount=Decimal("-10.00"),
                status="pending",
                payment_status="pending",
                created_at=datetime(2024, 1, 1, 12, 0, 0),
            )


# -----------------------------------------------------------------------
# OrderResponse tests
# -----------------------------------------------------------------------


class TestOrderResponse:
    """Tests for the full order detail response schema."""

    def test_valid_full_order_response(self):
        """A complete order produces a valid OrderResponse."""
        order = OrderResponse(
            order_id=uuid4(),
            user_id=uuid4(),
            total_amount=Decimal("50.00"),
            status="pending",
            payment_status="pending",
            items=[
                OrderItemResponse(
                    order_item_id=uuid4(),
                    product_id=uuid4(),
                    seller_id=uuid4(),
                    product_name="Test Product",
                    product_sku="SKU-001",
                    quantity=2,
                    price=Decimal("10.00"),
                    created_at=datetime(2024, 1, 1, 12, 0, 0),
                )
            ],
            subitems=[
                OrderSubitemResponse(
                    order_subitem_id=uuid4(),
                    seller_id=uuid4(),
                    subtotal=Decimal("20.00"),
                    status="pending",
                    created_at=datetime(2024, 1, 1, 12, 0, 0),
                )
            ],
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        assert order.total_amount == Decimal("50.00")
        assert len(order.items) == 1
        assert len(order.subitems) == 1
        assert order.items[0].product_name == "Test Product"
        assert order.subitems[0].subtotal == Decimal("20.00")

    def test_fingerprint_excluded(self):
        """OrderResponse does not include request_fingerprint."""
        order = OrderResponse(
            order_id=uuid4(),
            user_id=uuid4(),
            total_amount=Decimal("50.00"),
            status="pending",
            payment_status="pending",
            items=[],
            subitems=[],
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        order_dict = order.model_dump()
        assert "request_fingerprint" not in order_dict
        assert "source_cart_id" not in order_dict


# -----------------------------------------------------------------------
# OrderListResponse tests
# -----------------------------------------------------------------------


class TestOrderListResponse:
    """Tests for the paginated order list response schema."""

    def test_valid_order_list_response(self):
        """A valid list produces a valid OrderListResponse."""
        summary = OrderSummaryResponse(
            order_id=uuid4(),
            total_amount=Decimal("50.00"),
            status="pending",
            payment_status="pending",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        response = OrderListResponse(
            orders=[summary],
            total=1,
            skip=0,
            limit=20,
        )
        assert len(response.orders) == 1
        assert response.total == 1
        assert response.skip == 0
        assert response.limit == 20

    def test_invalid_skip_raises(self):
        """Negative skip raises ValidationError."""
        with pytest.raises(ValidationError):
            OrderListResponse(
                orders=[],
                total=0,
                skip=-1,
                limit=20,
            )

    def test_invalid_limit_raises(self):
        """Zero limit raises ValidationError."""
        with pytest.raises(ValidationError):
            OrderListResponse(
                orders=[],
                total=0,
                skip=0,
                limit=0,
            )


# -----------------------------------------------------------------------
# Decimal precision and JSON serialization tests
# -----------------------------------------------------------------------


class TestDecimalSerialization:
    """Tests for Decimal serialization in JSON output."""

    def test_price_serializes_as_decimal_string(self):
        """OrderItemResponse price serializes as a decimal string."""
        item = OrderItemResponse(
            order_item_id=uuid4(),
            product_id=uuid4(),
            seller_id=uuid4(),
            product_name="Test Product",
            product_sku="SKU-001",
            quantity=1,
            price=Decimal("10.00"),
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        json_str = item.model_dump_json()
        assert '"price":"10.00"' in json_str

    def test_subtotal_serializes_as_decimal_string(self):
        """OrderSubitemResponse subtotal serializes as a decimal string."""
        subitem = OrderSubitemResponse(
            order_subitem_id=uuid4(),
            seller_id=uuid4(),
            subtotal=Decimal("25.50"),
            status="pending",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        json_str = subitem.model_dump_json()
        assert '"subtotal":"25.50"' in json_str

    def test_total_amount_serializes_as_decimal_string(self):
        """OrderResponse total_amount serializes as a decimal string."""
        order = OrderResponse(
            order_id=uuid4(),
            user_id=uuid4(),
            total_amount=Decimal("100.99"),
            status="pending",
            payment_status="pending",
            items=[],
            subitems=[],
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        json_str = order.model_dump_json()
        assert '"total_amount":"100.99"' in json_str

    def test_decimal_precision_preserved(self):
        """Decimal precision is preserved through serialization."""
        item = OrderItemResponse(
            order_item_id=uuid4(),
            product_id=uuid4(),
            seller_id=uuid4(),
            product_name="Test Product",
            product_sku="SKU-001",
            quantity=3,
            price=Decimal("9.99"),
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        dumped = item.model_dump()
        assert dumped["price"] == "9.99"
        assert isinstance(dumped["price"], str)


# -----------------------------------------------------------------------
# ORM compatibility tests
# -----------------------------------------------------------------------


class TestOrmCompatibility:
    """Tests for Pydantic ORM (from_attributes) compatibility."""

    def test_order_item_response_from_orm_attributes(self):
        """OrderItemResponse can be constructed from ORM-like attributes."""
        orm_obj = SimpleNamespace(
            order_item_id=uuid4(),
            product_id=uuid4(),
            seller_id=uuid4(),
            product_name="ORM Product",
            product_sku="ORM-SKU",
            quantity=5,
            price=Decimal("15.00"),
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        item = OrderItemResponse.model_validate(orm_obj)
        assert item.product_name == "ORM Product"
        assert item.price == Decimal("15.00")
        assert item.quantity == 5

    def test_order_response_from_orm_attributes(self):
        """OrderResponse can be constructed from ORM-like attributes."""
        orm_obj = SimpleNamespace(
            order_id=uuid4(),
            user_id=uuid4(),
            total_amount=Decimal("75.00"),
            status="pending",
            payment_status="pending",
            items=[],
            subitems=[],
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
            request_fingerprint="should-not-be-exposed",
            source_cart_id="should-not-be-exposed",
        )
        order = OrderResponse.model_validate(orm_obj)
        assert order.order_id == orm_obj.order_id
        assert order.total_amount == Decimal("75.00")

        dumped = order.model_dump()
        assert "request_fingerprint" not in dumped
        assert "source_cart_id" not in dumped

    def test_order_summary_response_from_orm_attributes(self):
        """OrderSummaryResponse can be constructed from ORM-like attributes."""
        orm_obj = SimpleNamespace(
            order_id=uuid4(),
            total_amount=Decimal("42.00"),
            status="pending",
            payment_status="pending",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        summary = OrderSummaryResponse.model_validate(orm_obj)
        assert summary.total_amount == Decimal("42.00")
