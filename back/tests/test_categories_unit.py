"""Unit tests for category management endpoints.

Tests use mocked database sessions - no live database required.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from src.core.categories.router import (
    create_category,
    delete_category,
    get_category,
    list_categories,
    list_category_products,
    update_category,
)
from src.core.categories.schemas import (
    CategoryCreateRequest,
    CategoryListResponse,
    CategoryUpdateRequest,
)


def make_category(
    category_id="cat-123",
    name="Electronics",
    slug="electronics",
    description="Electronic devices",
    parent_id=None,
    level=0,
    path="electronics",
    is_active=True,
):
    """Create a simple namespace object acting as a Category model instance."""
    return SimpleNamespace(
        category_id=category_id,
        name=name,
        description=description,
        slug=slug,
        parent_id=parent_id,
        level=level,
        path=path,
        is_active=is_active,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


class TestCategoryEndpoint:
    """Tests for the category management endpoints."""

    def setup_method(self):
        self.mock_db = MagicMock()

    def make_create_request(self):
        return CategoryCreateRequest(
            name="Electronics",
            slug="electronics",
            description="Electronic devices",
        )

    def make_update_request(self):
        return CategoryUpdateRequest(
            name="Updated Electronics",
            description="Updated description",
        )

    def mock_single_filter_chain(self, first_return_value):
        """Set up mock where query().filter().first() returns first_return_value."""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = first_return_value
        return mock_query

    def mock_listing_chain(self, categories_list, total=None):
        """Set up mock for listing queries."""
        if total is None:
            total = len(categories_list)

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = total
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = categories_list
        return mock_query

    # === Category Creation Tests ===

    def test_successful_category_creation(self):
        """Valid category creation should return the created category."""
        request = self.make_create_request()

        # No duplicate name, no duplicate slug, no parent
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,
            None,
        ]

        result = create_category(request, self.mock_db)

        assert result.name == "Electronics"
        assert result.slug == "electronics"
        assert result.description == "Electronic devices"
        assert result.level == 0
        assert result.path == "electronics"
        assert result.is_active is True

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_successful_category_creation_with_parent(self):
        """Category creation with valid parent should set level and path."""
        request = CategoryCreateRequest(
            name="Phones",
            slug="phones",
            description="Mobile phones",
            parent_id="cat-parent",
        )

        parent = make_category(
            category_id="cat-parent",
            name="Electronics",
            slug="electronics",
            level=0,
            path="electronics",
        )

        # No duplicate name, no duplicate slug, parent exists
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,
            None,
            parent,
        ]

        result = create_category(request, self.mock_db)

        assert result.level == 1
        assert result.path == "electronics/phones"
        assert result.parent_id == "cat-parent"

    def test_duplicate_category_name_raises_409(self):
        """Duplicate category name should raise 409."""
        request = self.make_create_request()

        # Name already exists
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            make_category()
        )

        with pytest.raises(HTTPException) as exc_info:
            create_category(request, self.mock_db)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "name" in exc_info.value.detail.lower()

    def test_duplicate_category_slug_raises_409(self):
        """Duplicate category slug should raise 409."""
        request = self.make_create_request()

        # Name not found, slug found
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,
            make_category(),
        ]

        with pytest.raises(HTTPException) as exc_info:
            create_category(request, self.mock_db)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "slug" in exc_info.value.detail.lower()

    def test_nonexistent_parent_category_raises_404(self):
        """Non-existent parent category should raise 404."""
        request = CategoryCreateRequest(
            name="Phones",
            slug="phones",
            parent_id="cat-nonexistent",
        )

        # No duplicate name, no duplicate slug, parent not found
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,
            None,
            None,
        ]

        with pytest.raises(HTTPException) as exc_info:
            create_category(request, self.mock_db)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_category_data_raises_validation_error(self):
        """Invalid category data should raise ValidationError."""
        with pytest.raises(ValidationError):
            CategoryCreateRequest(
                name="",
                slug="",  # Invalid: empty slug
            )

    def test_category_creation_database_failure_raises_exception(self):
        """Database error during creation should raise an exception."""
        request = self.make_create_request()

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,
            None,
        ]

        self.mock_db.commit.side_effect = Exception("DB connection error")

        with pytest.raises(Exception):
            create_category(request, self.mock_db)

    # === Category Retrieval Tests ===

    def test_successful_category_retrieval(self):
        """Valid category ID should return the category."""
        category_id = "cat-123"
        category = make_category()

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            category
        )

        result = get_category(category_id, self.mock_db)

        assert result.category_id == "cat-123"
        assert result.name == "Electronics"
        assert result.slug == "electronics"
        assert result.is_active is True

    def test_category_not_found_raises_404(self):
        """Nonexistent category ID should raise 404."""
        category_id = "nonexistent-category"

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_category(category_id, self.mock_db)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "category" in exc_info.value.detail.lower()

    def test_category_database_query_failure_raises_exception(self):
        """Database query error should raise an exception."""
        category_id = "cat-123"

        self.mock_db.query.side_effect = Exception("DB connection error")

        with pytest.raises(Exception):
            get_category(category_id, self.mock_db)

    # === Category Update Tests ===

    def test_successful_category_update(self):
        """Valid category update should return the updated category."""
        category_id = "cat-123"
        request = self.make_update_request()
        category = make_category()

        # Category found, no duplicate name, no duplicate slug
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            category,
            None,
            None,
        ]

        result = update_category(category_id, request, self.mock_db)

        assert result.category_id == "cat-123"
        assert result.name == "Updated Electronics"
        assert result.description == "Updated description"

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_category_update_not_found_raises_404(self):
        """Nonexistent category ID should raise 404."""
        category_id = "nonexistent-category"
        request = self.make_update_request()

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            update_category(category_id, request, self.mock_db)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_category_update_duplicate_name_raises_409(self):
        """Duplicate name on update should raise 409."""
        category_id = "cat-123"
        request = CategoryUpdateRequest(name="Existing Name")
        category = make_category(name="Original Name")

        # Category found, duplicate name found (different category)
        existing = make_category(category_id="cat-other", name="Existing Name")
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            category,
            existing,
        ]

        with pytest.raises(HTTPException) as exc_info:
            update_category(category_id, request, self.mock_db)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT

    def test_category_update_duplicate_slug_raises_409(self):
        """Duplicate slug on update should raise 409."""
        category_id = "cat-123"
        request = CategoryUpdateRequest(slug="existing-slug")
        category = make_category(slug="original-slug")

        # Category found, slug duplicate found (name check skipped since name is None)
        existing = make_category(
            category_id="cat-other", slug="existing-slug"
        )
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            category,
            existing,
        ]

        with pytest.raises(HTTPException) as exc_info:
            update_category(category_id, request, self.mock_db)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT

    def test_category_update_preserves_omitted_fields(self):
        """Fields omitted from update request should remain unchanged."""
        category_id = "cat-123"
        request = CategoryUpdateRequest(name="Renamed Only")
        category = make_category()

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            category,
            None,
            None,
        ]

        result = update_category(category_id, request, self.mock_db)

        assert result.name == "Renamed Only"
        assert result.slug == "electronics"  # preserved
        assert result.description == "Electronic devices"  # preserved

    def test_category_update_database_failure_raises_exception(self):
        """Database error during update should raise an exception."""
        category_id = "cat-123"
        request = self.make_update_request()
        category = make_category()

        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            category,
            None,
            None,
        ]

        self.mock_db.commit.side_effect = Exception("DB connection error")

        with pytest.raises(Exception):
            update_category(category_id, request, self.mock_db)

    # === Category Deletion Tests ===

    def test_successful_category_deactivation(self):
        """Valid category ID should soft-delete (is_active = False)."""
        category_id = "cat-123"
        category = make_category()
        category.is_active = True

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            category
        )

        result = delete_category(category_id, self.mock_db)

        assert result["message"] == "Category deactivated successfully"
        assert result["category_id"] == "cat-123"
        assert result["is_active"] is False
        assert category.is_active is False

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_category_deactivation_not_found_raises_404(self):
        """Nonexistent category ID should raise 404."""
        category_id = "nonexistent-category"

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            delete_category(category_id, self.mock_db)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_category_already_inactive_still_deactivates(self):
        """Category already inactive can still be deactivated."""
        category_id = "cat-123"
        category = make_category()
        category.is_active = False  # Already inactive

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            category
        )

        result = delete_category(category_id, self.mock_db)

        assert result["is_active"] is False
        self.mock_db.commit.assert_called_once()

    def test_category_deletion_database_failure_raises_exception(self):
        """Database error during deactivation should raise an exception."""
        category_id = "cat-123"
        category = make_category()

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            category
        )

        self.mock_db.commit.side_effect = Exception("DB connection error")

        with pytest.raises(Exception):
            delete_category(category_id, self.mock_db)

    # === Category Listing Tests ===

    def test_default_listing(self):
        """Default listing should return active categories paginated."""
        categories = [make_category(f"cat-{i}") for i in range(3)]
        self.mock_listing_chain(categories, total=3)

        result = list_categories(db=self.mock_db)

        assert isinstance(result, CategoryListResponse)
        assert result.total == 3
        assert result.page == 1
        assert result.page_size == 20
        assert result.total_pages == 1
        assert len(result.items) == 3
        assert result.items[0].category_id == "cat-0"
        assert result.items[0].is_active is True

    def test_listing_excludes_inactive_by_default(self):
        """Default listing should filter to is_active=True."""
        categories = [make_category("cat-1", is_active=True)]
        self.mock_listing_chain(categories, total=1)

        result = list_categories(db=self.mock_db)

        assert len(result.items) == 1
        assert result.items[0].is_active is True

    def test_listing_search_by_name(self):
        """Search should filter categories by name case-insensitively."""
        categories = [make_category("cat-1", name="Electronics")]
        self.mock_listing_chain(categories, total=1)

        result = list_categories(search="electronics", db=self.mock_db)

        assert len(result.items) == 1
        assert result.items[0].name == "Electronics"

    def test_listing_empty_results(self):
        """Empty results should return empty items list."""
        self.mock_listing_chain([], total=0)

        result = list_categories(db=self.mock_db)

        assert result.total == 0
        assert result.total_pages == 0
        assert result.items == []

    def test_listing_pagination(self):
        """Pagination should return correct page and page_size."""
        categories = [make_category(f"cat-{i}") for i in range(5)]
        self.mock_listing_chain(categories, total=25)

        result = list_categories(page=2, page_size=5, db=self.mock_db)

        assert result.page == 2
        assert result.page_size == 5
        assert result.total == 25
        assert result.total_pages == 5
        assert len(result.items) == 5

    def test_listing_invalid_page_raises_400(self):
        """page < 1 should raise 400."""
        with pytest.raises(HTTPException) as exc_info:
            list_categories(page=0, db=self.mock_db)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    def test_listing_invalid_page_size_raises_400(self):
        """page_size > 100 should raise 400."""
        with pytest.raises(HTTPException) as exc_info:
            list_categories(page_size=101, db=self.mock_db)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    def test_listing_database_error_raises_exception(self):
        """Database error during listing should raise an exception."""
        self.mock_db.query.side_effect = Exception("DB connection error")

        with pytest.raises(Exception):
            list_categories(db=self.mock_db)

    # === Category Product Listing Tests ===

    def test_category_product_listing(self):
        """Products belonging to a category should be listed."""
        category_id = "cat-123"
        category = make_category(category_id=category_id)

        products = [
            SimpleNamespace(
                product_id="prod-1",
                store_id="store-1",
                category_id=category_id,
                name="Phone",
                description="Smartphone",
                price=29.99,
                cost=15.00,
                sku="SKU-001",
                stock=100,
                is_active=True,
                images_urls=None,
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                updated_at=datetime(2024, 1, 1, 12, 0, 0),
            )
        ]

        # Category query mock
        category_mock = MagicMock()
        category_mock.filter.return_value = category_mock
        category_mock.first.return_value = category

        # Product query mock
        products_mock = MagicMock()
        products_mock.filter.return_value = products_mock
        products_mock.count.return_value = 1
        products_mock.order_by.return_value = products_mock
        products_mock.offset.return_value = products_mock
        products_mock.limit.return_value = products_mock
        products_mock.all.return_value = products

        # First db.query() call returns category mock, second returns products mock
        self.mock_db.query.side_effect = [category_mock, products_mock]

        result = list_category_products(category_id, db=self.mock_db)

        assert result["category_id"] == "cat-123"
        assert result["category_name"] == "Electronics"
        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "Phone"

    def test_category_product_listing_not_found(self):
        """Nonexistent category ID should raise 404 for product listing."""
        category_id = "nonexistent-category"

        category_mock = MagicMock()
        category_mock.filter.return_value = category_mock
        category_mock.first.return_value = None

        self.mock_db.query.side_effect = [category_mock]

        with pytest.raises(HTTPException) as exc_info:
            list_category_products(category_id, db=self.mock_db)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_category_product_listing_empty(self):
        """Category with no products should return empty items."""
        category_id = "cat-123"
        category = make_category(category_id=category_id)

        category_mock = MagicMock()
        category_mock.filter.return_value = category_mock
        category_mock.first.return_value = category

        products_mock = MagicMock()
        products_mock.filter.return_value = products_mock
        products_mock.count.return_value = 0
        products_mock.order_by.return_value = products_mock
        products_mock.offset.return_value = products_mock
        products_mock.limit.return_value = products_mock
        products_mock.all.return_value = []

        self.mock_db.query.side_effect = [category_mock, products_mock]

        result = list_category_products(category_id, db=self.mock_db)

        assert result["total"] == 0
        assert result["total_pages"] == 0
        assert result["items"] == []

    def test_category_product_listing_invalid_pagination(self):
        """Invalid pagination should raise 400."""
        category_id = "cat-123"
        category = make_category(category_id=category_id)

        category_mock = MagicMock()
        category_mock.filter.return_value = category_mock
        category_mock.first.return_value = category

        self.mock_db.query.side_effect = [category_mock]

        with pytest.raises(HTTPException) as exc_info:
            list_category_products(category_id, page_size=101, db=self.mock_db)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
