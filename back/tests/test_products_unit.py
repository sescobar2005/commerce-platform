"""Unit tests for product creation endpoint.

Tests use mocked database sessions - no live database required.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from src.core.models.category import Category
from src.core.models.product import Product
from src.core.models.seller import Seller
from src.core.models.store import Store
from src.core.products.router import create_product, get_product, update_product
from src.core.products.schemas import (
    ProductCreateRequest,
    ProductUpdateRequest,
)
from src.core.security.schemas import UserResponse


class TestCreateProductEndpoint:
    """Tests for the product creation endpoint."""

    def setup_method(self):
        self.mock_db = MagicMock()

    def make_request(self):
        return ProductCreateRequest(
            store_id="store-123",
            category_id="cat-456",
            name="Test Product",
            description="A test product",
            price=29.99,
            cost=15.00,
            sku="SKU-001",
            stock=100,
        )

    def make_current_user(self):
        return UserResponse(
            user_id="user-123",
            username="johndoe",
            email="john@example.com",
            is_seller=True,
            is_verified=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

    def make_seller(self):
        seller = MagicMock(spec=Seller)
        seller.seller_id = "user-123"
        seller.store_name = "Test Store"
        return seller

    def make_store(self, seller_id="user-123"):
        store = MagicMock(spec=Store)
        store.store_id = "store-123"
        store.seller_id = seller_id
        store.name = "Test Store"
        return store

    def make_category(self):
        category = MagicMock(spec=Category)
        category.category_id = "cat-456"
        category.name = "Electronics"
        return category

    def test_successful_product_creation(self):
        """Valid product creation should return the created product."""
        request = self.make_request()
        current_user = self.make_current_user()

        seller = self.make_seller()
        store = self.make_store()
        category = self.make_category()

        # Three first() calls: seller lookup, store lookup, category lookup
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            seller,
            store,
            category,
        ]

        # refresh populates server-generated timestamps
        def set_timestamps(product):
            product.created_at = datetime(2024, 1, 1, 12, 0, 0)
            product.updated_at = datetime(2024, 1, 1, 12, 0, 0)

        self.mock_db.refresh.side_effect = set_timestamps

        result = create_product(request, self.mock_db, current_user)

        assert result.store_id == "store-123"
        assert result.category_id == "cat-456"
        assert result.name == "Test Product"
        assert result.description == "A test product"
        assert result.price == 29.99
        assert result.cost == 15.00
        assert result.sku == "SKU-001"
        assert result.stock == 100
        assert result.is_active is True

        # Verify all lookups were performed
        assert self.mock_db.query.call_count == 3
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_no_seller_profile_raises_403(self):
        """User without a seller profile should raise 403."""
        request = self.make_request()
        current_user = self.make_current_user()

        # First call returns None (no seller profile found)
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            create_product(request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "seller profile" in exc_info.value.detail.lower()

    def test_store_not_found_raises_404(self):
        """Nonexistent store should raise 404."""
        request = self.make_request()
        current_user = self.make_current_user()

        seller = self.make_seller()

        # First call returns seller, second returns None (store not found)
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            seller,
            None,
        ]

        with pytest.raises(HTTPException) as exc_info:
            create_product(request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "store" in exc_info.value.detail.lower()

    def test_store_owned_by_another_seller_raises_403(self):
        """Store owned by another seller should raise 403."""
        request = self.make_request()
        current_user = self.make_current_user()

        seller = self.make_seller()
        store = self.make_store(seller_id="user-456")  # Different owner

        # First call returns seller, second returns store owned by another user
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            seller,
            store,
        ]

        with pytest.raises(HTTPException) as exc_info:
            create_product(request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "belong" in exc_info.value.detail.lower()

    def test_category_not_found_raises_404(self):
        """Nonexistent category should raise 404."""
        request = self.make_request()
        current_user = self.make_current_user()

        seller = self.make_seller()
        store = self.make_store()

        # Seller found, store found, category not found
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            seller,
            store,
            None,
        ]

        with pytest.raises(HTTPException) as exc_info:
            create_product(request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "category" in exc_info.value.detail.lower()

    def test_invalid_product_input_raises_validation_error(self):
        """Invalid product input (negative price) should raise ValidationError."""
        with pytest.raises(ValidationError):
            ProductCreateRequest(
                store_id="store-123",
                category_id="cat-456",
                name="Test Product",
                price=-10.00,  # Invalid: price must be > 0
                sku="SKU-001",
            )

    def test_duplicate_sku_raises_409(self):
        """Duplicate SKU should raise 409 via IntegrityError."""
        request = self.make_request()
        current_user = self.make_current_user()

        seller = self.make_seller()
        store = self.make_store()
        category = self.make_category()

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            seller,
            store,
            category,
        ]

        # Simulate IntegrityError on commit
        self.mock_db.commit.side_effect = IntegrityError(
            "duplicate key", params={}, orig=None
        )

        with pytest.raises(HTTPException) as exc_info:
            create_product(request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert self.mock_db.rollback.called

    def test_database_failure_raises_exception(self):
        """Database error during creation should raise an exception."""
        request = self.make_request()
        current_user = self.make_current_user()

        seller = self.make_seller()
        store = self.make_store()
        category = self.make_category()

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            seller,
            store,
            category,
        ]

        # Simulate DB error on commit
        self.mock_db.commit.side_effect = Exception("DB connection error")

        with pytest.raises(Exception):
            create_product(request, self.mock_db, current_user)

    def make_product(self):
        product = MagicMock(spec=Product)
        product.product_id = "product-123"
        product.store_id = "store-123"
        product.category_id = "cat-456"
        product.name = "Test Product"
        product.description = "A test product"
        product.price = 29.99
        product.cost = 15.00
        product.sku = "SKU-001"
        product.stock = 100
        product.is_active = True
        product.images_urls = None
        product.created_at = datetime(2024, 1, 1, 12, 0, 0)
        product.updated_at = datetime(2024, 1, 1, 12, 0, 0)
        return product

    def test_successful_product_retrieval(self):
        """Valid product ID should return the product."""
        product_id = "product-123"
        product = self.make_product()

        self.mock_db.query.return_value.filter.return_value.first.return_value = product

        result = get_product(product_id, self.mock_db)

        assert result.product_id == "product-123"
        assert result.store_id == "store-123"
        assert result.category_id == "cat-456"
        assert result.name == "Test Product"
        assert result.description == "A test product"
        assert result.price == 29.99
        assert result.cost == 15.00
        assert result.sku == "SKU-001"
        assert result.stock == 100
        assert result.is_active is True

    def test_product_not_found_raises_404(self):
        """Nonexistent product ID should raise 404."""
        product_id = "nonexistent-product"

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_product(product_id, self.mock_db)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "product" in exc_info.value.detail.lower()

    def test_database_query_failure_raises_exception(self):
        """Database query error should raise an exception."""
        product_id = "product-123"

        self.mock_db.query.side_effect = Exception("DB connection error")

        with pytest.raises(Exception):
            get_product(product_id, self.mock_db)

    def make_update_request(self):
        return ProductUpdateRequest(
            name="Updated Product",
            price=39.99,
            stock=50,
        )

    def test_successful_product_update(self):
        """Valid update should return the updated product."""
        product_id = "product-123"
        request = self.make_update_request()
        current_user = self.make_current_user()

        product = self.make_product()
        seller = self.make_seller()
        store = self.make_store()

        # Three first() calls: seller lookup, product lookup, store ownership check
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            seller,
            product,
            store,
        ]

        result = update_product(product_id, request, self.mock_db, current_user)

        assert result.product_id == "product-123"
        assert result.name == "Updated Product"
        assert result.description == "A test product"  # preserved
        assert result.price == 39.99
        assert result.cost == 15.00  # preserved
        assert result.sku == "SKU-001"  # preserved
        assert result.stock == 50
        assert result.is_active is True  # preserved

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_product_update_not_found_raises_404(self):
        """Nonexistent product ID should raise 404."""
        product_id = "nonexistent-product"
        request = self.make_update_request()
        current_user = self.make_current_user()

        seller = self.make_seller()

        # First call returns seller, second returns None (product not found)
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            seller,
            None,
        ]

        with pytest.raises(HTTPException) as exc_info:
            update_product(product_id, request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "product" in exc_info.value.detail.lower()

    def test_product_update_no_seller_profile_raises_403(self):
        """User without seller profile should raise 403."""
        product_id = "product-123"
        request = self.make_update_request()
        current_user = self.make_current_user()

        # First call returns None (no seller profile found)
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            update_product(product_id, request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "seller profile" in exc_info.value.detail.lower()

    def test_product_update_not_owner_raises_403(self):
        """Store owned by another seller should raise 403."""
        product_id = "product-123"
        request = self.make_update_request()
        current_user = self.make_current_user()

        seller = self.make_seller()
        product = self.make_product()
        store_owned_by_other = self.make_store(seller_id="user-456")

        # First call returns seller, second returns product, third returns store owned by another user
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            seller,
            product,
            store_owned_by_other,
        ]

        with pytest.raises(HTTPException) as exc_info:
            update_product(product_id, request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "belong" in exc_info.value.detail.lower()

    def test_product_update_preserves_omitted_fields(self):
        """Fields omitted from update request should remain unchanged."""
        product_id = "product-123"
        request = ProductUpdateRequest(price=49.99)  # Only price
        current_user = self.make_current_user()

        product = self.make_product()
        seller = self.make_seller()
        store = self.make_store()

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            seller,
            product,
            store,
        ]

        result = update_product(product_id, request, self.mock_db, current_user)

        assert result.price == 49.99  # updated
        assert result.name == "Test Product"  # preserved
        assert result.description == "A test product"  # preserved
        assert result.sku == "SKU-001"  # preserved
        assert result.stock == 100  # preserved
        assert result.is_active is True  # preserved

    def test_product_update_duplicate_sku_raises_409(self):
        """Duplicate SKU should raise 409 via IntegrityError."""
        product_id = "product-123"
        request = ProductUpdateRequest(sku="DUPLICATE-SKU")
        current_user = self.make_current_user()

        product = self.make_product()
        seller = self.make_seller()
        store = self.make_store()

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            seller,
            product,
            store,
        ]

        # Simulate IntegrityError on commit
        self.mock_db.commit.side_effect = IntegrityError(
            "duplicate key", params={}, orig=None
        )

        with pytest.raises(HTTPException) as exc_info:
            update_product(product_id, request, self.mock_db, current_user)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert self.mock_db.rollback.called

    def test_product_update_invalid_price_raises_validation_error(self):
        """Invalid price (negative) should raise ValidationError."""
        product_id = "product-123"
        current_user = self.make_current_user()

        with pytest.raises(Exception):
            ProductUpdateRequest(price=-10.00)  # Invalid: price must be > 0

    def test_product_update_database_failure_raises_exception(self):
        """Database error during update should raise an exception."""
        product_id = "product-123"
        request = ProductUpdateRequest(name="Updated Product")
        current_user = self.make_current_user()

        product = self.make_product()
        seller = self.make_seller()
        store = self.make_store()

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            seller,
            product,
            store,
        ]

        # Simulate DB error on commit
        self.mock_db.commit.side_effect = Exception("DB connection error")

        with pytest.raises(Exception):
            update_product(product_id, request, self.mock_db, current_user)
