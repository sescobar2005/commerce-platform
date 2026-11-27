"""HTTP-level integration tests for Orders API router.

These tests use FastAPI's TestClient against the actual application,
with dependency overrides for the database session and authenticated user.
Tests run against an in-memory SQLite database.

SQLite does not provide PostgreSQL row-level locking semantics.
These tests verify HTTP contract behavior (status codes, response schemas,
error mapping) but do not prove PostgreSQL concurrency guarantees.
"""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.database import Base, get_db
from src.core.auth.dependencies import get_current_user
from src.core.models.cart import Cart, CartItem
from src.core.models.category import Category
from src.core.models.order import Order, OrderItem, OrderSubitem
from src.core.models.product import Product
from src.core.models.seller import Seller
from src.core.models.store import Store
from src.core.models.user import User
from src.core.security.schemas import CurrentUser
from src.main import create_app


# -----------------------------------------------------------------------
# Test constants
# -----------------------------------------------------------------------

_TEST_ORDER_ID = UUID("11111111-1111-1111-1111-111111111111")
_TEST_USER_ID = UUID("22222222-2222-2222-2222-222222222222")
_TEST_PRODUCT_ID = UUID("33333333-3333-3333-3333-333333333333")
_TEST_SELLER_ID = UUID("44444444-4444-4444-4444-444444444444")
_TEST_CART_ID = UUID("55555555-5555-5555-5555-555555555555")
_TEST_ORDER_ITEM_ID = UUID("66666666-6666-6666-6666-666666666666")
_TEST_ORDER_SUBITEM_ID = UUID("77777777-7777-7777-7777-777777777777")


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


@pytest.fixture
def db_session():
    """Create a file-based SQLite session with all tables created."""
    import tempfile
    import os
    tmpfile = tempfile.mktemp(suffix=".db")
    engine = create_engine(f"sqlite:///{tmpfile}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
    engine.dispose()
    os.unlink(tmpfile)


@pytest.fixture
def current_user():
    """Create a CurrentUser for authenticated requests."""
    return CurrentUser(
        user_id=str(_TEST_USER_ID),
        username="user1",
        email="user1@example.com",
        is_seller=False,
        is_verified=False,
        is_admin=False,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def client(db_session, current_user):
    """Create a TestClient with overridden dependencies."""
    app = create_app()

    def override_get_db():
        session = Session(db_session.bind)
        try:
            yield session
        finally:
            session.close()

    def override_get_current_user():
        return current_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# -----------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------


def _create_prerequisite_data(session: Session):
    """Create users, stores, sellers, categories, products, cart, cart items."""
    user = User(
        user_id=str(_TEST_USER_ID),
        username="user1",
        email="user1@example.com",
        password_hash="hash",
        is_seller=False,
        is_verified=True,
    )
    seller = Seller(
        seller_id=str(_TEST_SELLER_ID),
        store_name="Test Store",
    )
    store = Store(
        store_id=str(UUID("88888888-8888-8888-8888-888888888888")),
        seller_id=str(_TEST_SELLER_ID),
        name="Test Store",
        slug="test-store",
    )
    category = Category(
        category_id=str(UUID("99999999-9999-9999-9999-999999999999")),
        name="Electronics",
        slug="electronics",
    )
    product = Product(
        product_id=str(_TEST_PRODUCT_ID),
        store_id=str(UUID("88888888-8888-8888-8888-888888888888")),
        category_id=str(UUID("99999999-9999-9999-9999-999999999999")),
        name="Test Product",
        sku="SKU-001",
        price=Decimal("10.00"),
        stock=100,
        reserved_quantity=0,
        is_active=True,
    )
    cart = Cart(
        cart_id=str(_TEST_CART_ID),
        user_id=str(_TEST_USER_ID),
    )
    cart_item = CartItem(
        cart_item_id=str(_TEST_ORDER_ITEM_ID),
        cart_id=str(_TEST_CART_ID),
        product_id=str(_TEST_PRODUCT_ID),
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


# -----------------------------------------------------------------------
# Integration tests - Create Order (POST /api/v1/orders/)
# -----------------------------------------------------------------------


class TestCreateOrderIntegration:
    """Integration tests for POST /api/v1/orders/ endpoint."""

    def test_first_creation_returns_201(self, client, db_session):
        """First successful order creation returns HTTP 201."""
        _create_prerequisite_data(db_session)

        response = client.post(
            "/api/v1/orders/",
            json={"cart_id": str(_TEST_CART_ID)},
            headers={"Idempotency-Key": "key-123"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(_TEST_USER_ID)
        assert data["total_amount"] == "20.00"
        assert data["status"] == "pending"
        assert data["payment_status"] == "pending"
        assert "request_fingerprint" not in data
        assert "source_cart_id" not in data
        assert len(data["items"]) == 1
        assert data["items"][0]["price"] == "10.00"
        assert len(data["subitems"]) == 1
        assert data["subitems"][0]["subtotal"] == "20.00"

    def test_idempotent_retry_returns_200(self, client, db_session):
        """Repeating same request with same key returns HTTP 200."""
        _create_prerequisite_data(db_session)

        # First creation
        response1 = client.post(
            "/api/v1/orders/",
            json={"cart_id": str(_TEST_CART_ID)},
            headers={"Idempotency-Key": "key-123"},
        )
        assert response1.status_code == 201
        order_id_1 = response1.json()["order_id"]

        # Second call with same key and cart
        response2 = client.post(
            "/api/v1/orders/",
            json={"cart_id": str(_TEST_CART_ID)},
            headers={"Idempotency-Key": "key-123"},
        )
        assert response2.status_code == 200
        assert response2.json()["order_id"] == order_id_1

        # Verify only one order exists in database
        orders = db_session.query(Order).all()
        assert len(orders) == 1

    def test_incompatible_key_returns_409(self, client, db_session):
        """Reusing same key with different cart returns HTTP 409."""
        _create_prerequisite_data(db_session)

        # First creation with cart-1
        response1 = client.post(
            "/api/v1/orders/",
            json={"cart_id": str(_TEST_CART_ID)},
            headers={"Idempotency-Key": "key-123"},
        )
        assert response1.status_code == 201

        # Create a different cart
        cart2 = Cart(
            cart_id=str(uuid4()),
            user_id=str(_TEST_USER_ID),
        )
        cart2_item = CartItem(
            cart_item_id=str(uuid4()),
            cart_id=str(cart2.cart_id),
            product_id=str(_TEST_PRODUCT_ID),
            quantity=1,
            price_at_time=Decimal("10.00"),
        )
        db_session.add(cart2)
        db_session.add(cart2_item)
        db_session.commit()

        # Try same key with different cart
        response2 = client.post(
            "/api/v1/orders/",
            json={"cart_id": str(cart2.cart_id)},
            headers={"Idempotency-Key": "key-123"},
        )
        assert response2.status_code == 409
        assert response2.json()["detail"] == "Idempotency conflict"

    def test_response_decimal_serialization(self, client, db_session):
        """Monetary values are serialized as decimal strings."""
        _create_prerequisite_data(db_session)

        response = client.post(
            "/api/v1/orders/",
            json={"cart_id": str(_TEST_CART_ID)},
            headers={"Idempotency-Key": "key-serial"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["total_amount"] == "20.00"
        assert data["items"][0]["price"] == "10.00"
        assert data["subitems"][0]["subtotal"] == "20.00"

    def test_missing_idempotency_key_returns_201(self, client, db_session):
        """Missing Idempotency-Key header returns HTTP 201."""
        _create_prerequisite_data(db_session)

        response = client.post(
            "/api/v1/orders/",
            json={"cart_id": str(_TEST_CART_ID)},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["order_id"] is not None

    def test_empty_idempotency_key_returns_400(self, client, db_session):
        """Empty Idempotency-Key header returns HTTP 400."""
        _create_prerequisite_data(db_session)

        response = client.post(
            "/api/v1/orders/",
            json={"cart_id": str(_TEST_CART_ID)},
            headers={"Idempotency-Key": ""},
        )

        assert response.status_code == 400

    def test_oversized_idempotency_key_returns_400(self, client, db_session):
        """Oversized Idempotency-Key header returns HTTP 400."""
        _create_prerequisite_data(db_session)

        oversized_key = "x" * 101
        response = client.post(
            "/api/v1/orders/",
            json={"cart_id": str(_TEST_CART_ID)},
            headers={"Idempotency-Key": oversized_key},
        )

        assert response.status_code == 400

    def test_missing_cart_returns_404(self, client, db_session):
        """Nonexistent cart_id returns HTTP 404."""
        _create_prerequisite_data(db_session)

        response = client.post(
            "/api/v1/orders/",
            json={"cart_id": str(uuid4())},
            headers={"Idempotency-Key": "key-missing-cart"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Order not found"


# -----------------------------------------------------------------------
# Integration tests - Get Order (GET /api/v1/orders/{order_id})
# -----------------------------------------------------------------------


class TestGetOrderIntegration:
    """Integration tests for GET /api/v1/orders/{order_id} endpoint."""

    def test_get_order_returns_200(self, client, db_session):
        """Retrieving an order returns HTTP 200 with order data."""
        _create_prerequisite_data(db_session)

        # Create order first
        create_response = client.post(
            "/api/v1/orders/",
            json={"cart_id": str(_TEST_CART_ID)},
            headers={"Idempotency-Key": "key-get-order"},
        )
        assert create_response.status_code == 201
        order_id = create_response.json()["order_id"]

        # Retrieve the order
        response = client.get(f"/api/v1/orders/{order_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == order_id
        assert data["user_id"] == str(_TEST_USER_ID)
        assert data["total_amount"] == "20.00"
        assert data["status"] == "pending"
        assert data["payment_status"] == "pending"
        assert len(data["items"]) == 1
        assert len(data["subitems"]) == 1
        assert "request_fingerprint" not in data

    def test_get_order_invalid_uuid_returns_404(self, client, db_session):
        """Invalid UUID returns HTTP 404."""
        _create_prerequisite_data(db_session)

        response = client.get("/api/v1/orders/not-a-uuid")
        assert response.status_code == 404

    def test_get_order_nonexistent_returns_404(self, client, db_session):
        """Nonexistent order returns HTTP 404."""
        _create_prerequisite_data(db_session)

        response = client.get(f"/api/v1/orders/{uuid4()}")
        assert response.status_code == 404


# -----------------------------------------------------------------------
# Integration tests - List Orders (GET /api/v1/orders/)
# -----------------------------------------------------------------------


class TestListOrdersIntegration:
    """Integration tests for GET /api/v1/orders/ endpoint."""

    def test_list_orders_returns_200(self, client, db_session):
        """Listing orders returns HTTP 200 with order summaries."""
        _create_prerequisite_data(db_session)

        # Create an order first
        client.post(
            "/api/v1/orders/",
            json={"cart_id": str(_TEST_CART_ID)},
            headers={"Idempotency-Key": "key-list"},
        )

        response = client.get("/api/v1/orders/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert data["skip"] == 0
        assert data["limit"] == 20
        assert len(data["orders"]) >= 1
        assert "total_amount" in data["orders"][0]
        assert "items" not in data["orders"][0]  # No nesting in summary


# -----------------------------------------------------------------------
# Integration tests - Get Order Items (GET /api/v1/orders/{order_id}/items)
# -----------------------------------------------------------------------


class TestGetOrderItemsIntegration:
    """Integration tests for GET /api/v1/orders/{order_id}/items endpoint."""

    def test_get_order_items_returns_200(self, client, db_session):
        """Retrieving order items returns HTTP 200 with item data."""
        _create_prerequisite_data(db_session)

        # Create order first
        create_response = client.post(
            "/api/v1/orders/",
            json={"cart_id": str(_TEST_CART_ID)},
            headers={"Idempotency-Key": "key-items"},
        )
        assert create_response.status_code == 201
        order_id = create_response.json()["order_id"]

        # Retrieve order items
        response = client.get(f"/api/v1/orders/{order_id}/items")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["product_id"] == str(_TEST_PRODUCT_ID)
        assert data[0]["seller_id"] == str(_TEST_SELLER_ID)
        assert data[0]["product_name"] == "Test Product"
        assert data[0]["product_sku"] == "SKU-001"
        assert data[0]["quantity"] == 2
        assert data[0]["price"] == "10.00"


# -----------------------------------------------------------------------
# Integration tests - Get Order Subitems (GET /api/v1/orders/{order_id}/subitems)
# -----------------------------------------------------------------------


class TestGetOrderSubitemsIntegration:
    """Integration tests for GET /api/v1/orders/{order_id}/subitems endpoint."""

    def test_get_order_subitems_returns_200(self, client, db_session):
        """Retrieving order subitems returns HTTP 200 with subitem data."""
        _create_prerequisite_data(db_session)

        # Create order first
        create_response = client.post(
            "/api/v1/orders/",
            json={"cart_id": str(_TEST_CART_ID)},
            headers={"Idempotency-Key": "key-subitems"},
        )
        assert create_response.status_code == 201
        order_id = create_response.json()["order_id"]

        # Retrieve order subitems
        response = client.get(f"/api/v1/orders/{order_id}/subitems")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["seller_id"] == str(_TEST_SELLER_ID)
        assert data[0]["subtotal"] == "20.00"
        assert data[0]["status"] == "pending"