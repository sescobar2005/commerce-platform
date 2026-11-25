"""Unit tests for database models.

These tests do NOT require a live PostgreSQL database.
They use in-memory SQLite URLs for model instantiation and
relationship tests.
"""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from src.core.database import Base, engine, SessionLocal
from src.core.models.category import Category
from src.core.models.product import Product
from src.core.models.seller import Seller
from src.core.models.store import Store
from src.core.models.user import User


class TestUserModel:
    """Tests for User model without live database."""

    def test_user_creation(self):
        """User should be instantiable with required fields.

        Python-side column defaults are applied at flush/insert time,
        not at instance construction time in SQLAlchemy 2.0.
        """
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="argon2id$hashed",
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "argon2id$hashed"
        assert user.is_seller is None
        assert user.is_verified is None
        assert user.is_admin is None
        assert user.is_moderator is None

    def test_user_admin_and_moderator_defaults(self):
        """User should default is_admin and is_moderator to None at construction.

        Python-side defaults are applied at flush/insert time,
        not at instance construction time in SQLAlchemy 2.0.
        """
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hash",
        )
        assert user.is_admin is None
        assert user.is_moderator is None

    def test_user_can_be_admin_and_moderator(self):
        """User should allow setting is_admin and is_moderator to True."""
        user = User(
            username="adminuser",
            email="admin@example.com",
            password_hash="argon2id$hashed",
            is_admin=True,
            is_moderator=True,
        )
        assert user.is_admin is True
        assert user.is_moderator is True

    def test_user_defaults(self):
        """User should have correct default values at construction.

        Python-side column defaults are applied at flush/insert time,
        not at instance construction time in SQLAlchemy 2.0.
        """
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hash",
        )
        assert user.is_seller is None
        assert user.is_verified is None
        assert user.is_admin is None
        assert user.is_moderator is None
        assert user.preferences_json is None
        assert user.last_login_at is None

    def test_user_repr(self):
        """User __repr__ should include key fields."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hash",
        )
        repr_str = repr(user)
        assert "testuser" in repr_str
        assert "test@example.com" in repr_str


class TestSellerModel:
    """Tests for Seller model without live database."""

    def test_seller_creation(self):
        """Seller should be instantiable with required fields.

        Python-side column defaults are applied at flush/insert time,
        not at instance construction time in SQLAlchemy 2.0.
        """
        seller = Seller(
            seller_id="test-seller-id",
            store_name="Test Store",
        )
        assert seller.store_name == "Test Store"
        assert seller.is_verified is None
        assert seller.business_name is None
        assert seller.tax_id is None

    def test_seller_defaults(self):
        """Seller should have correct default values at construction.

        Python-side column defaults are applied at flush/insert time,
        not at instance construction time in SQLAlchemy 2.0.
        """
        seller = Seller(
            seller_id="test-seller-id",
            store_name="Test Store",
        )
        assert seller.is_verified is None
        assert seller.payment_info_json is None
        assert seller.bank_account is None

    def test_seller_repr(self):
        """Seller __repr__ should include key fields."""
        seller = Seller(
            seller_id="test-seller-id",
            store_name="Test Store",
        )
        repr_str = repr(seller)
        assert "Test Store" in repr_str


class TestStoreModel:
    """Tests for Store model without live database."""

    def test_store_creation(self):
        """Store should be instantiable with required fields.

        Python-side column defaults are applied at flush/insert time,
        not at instance construction time in SQLAlchemy 2.0.
        """
        store = Store(
            store_id="test-store-id",
            seller_id="test-seller-id",
            name="Test Store",
            slug="test-store",
        )
        assert store.name == "Test Store"
        assert store.slug == "test-store"
        assert store.is_active is None

    def test_store_defaults(self):
        """Store should have correct default values at construction.

        Python-side column defaults are applied at flush/insert time,
        not at instance construction time in SQLAlchemy 2.0.
        """
        store = Store(
            store_id="test-store-id",
            seller_id="test-seller-id",
            name="Test Store",
            slug="test-store",
        )
        assert store.is_active is None
        assert store.description is None
        assert store.logo_url is None

    def test_store_repr(self):
        """Store __repr__ should include key fields."""
        store = Store(
            store_id="test-store-id",
            seller_id="test-seller-id",
            name="Test Store",
            slug="test-store",
        )
        repr_str = repr(store)
        assert "Test Store" in repr_str
        assert "test-store" in repr_str


class TestCategoryModel:
    """Tests for Category model without live database."""

    def test_category_creation(self):
        """Category should be instantiable with required fields.

        Python-side column defaults are applied at flush/insert time,
        not at instance construction time in SQLAlchemy 2.0.
        """
        category = Category(
            category_id="test-category-id",
            name="Electronics",
            slug="electronics",
        )
        assert category.name == "Electronics"
        assert category.slug == "electronics"
        assert category.level is None
        assert category.is_active is None
        assert category.parent_id is None

    def test_category_defaults(self):
        """Category should have correct default values at construction.

        Python-side column defaults are applied at flush/insert time,
        not at instance construction time in SQLAlchemy 2.0.
        """
        category = Category(
            category_id="test-category-id",
            name="Electronics",
            slug="electronics",
        )
        assert category.level is None
        assert category.is_active is None
        assert category.description is None
        assert category.path is None

    def test_category_repr(self):
        """Category __repr__ should include key fields."""
        category = Category(
            category_id="test-category-id",
            name="Electronics",
            slug="electronics",
        )
        repr_str = repr(category)
        assert "Electronics" in repr_str
        assert "electronics" in repr_str


class TestProductModel:
    """Tests for Product model without live database."""

    def test_product_creation(self):
        """Product should be instantiable with required fields.

        Python-side column defaults are applied at flush/insert time,
        not at instance construction time in SQLAlchemy 2.0.
        """
        product = Product(
            product_id="test-product-id",
            store_id="test-store-id",
            category_id="test-category-id",
            name="Test Product",
            price=99.99,
            sku="SKU-001",
        )
        assert product.name == "Test Product"
        assert product.price == 99.99
        assert product.sku == "SKU-001"
        assert product.stock is None
        assert product.is_active is None

    def test_product_defaults(self):
        """Product should have correct default values at construction.

        Python-side column defaults are applied at flush/insert time,
        not at instance construction time in SQLAlchemy 2.0.
        """
        product = Product(
            product_id="test-product-id",
            store_id="test-store-id",
            category_id="test-category-id",
            name="Test Product",
            price=99.99,
            sku="SKU-001",
        )
        assert product.stock is None
        assert product.is_active is None
        assert product.cost is None
        assert product.images_urls is None
        assert product.description is None

    def test_product_repr(self):
        """Product __repr__ should include key fields."""
        product = Product(
            product_id="test-product-id",
            store_id="test-store-id",
            category_id="test-category-id",
            name="Test Product",
            price=99.99,
            sku="SKU-001",
        )
        repr_str = repr(product)
        assert "Test Product" in repr_str
        assert "SKU-001" in repr_str


class TestModelMetadata:
    """Tests for SQLAlchemy metadata integration."""

    def test_all_models_registered_in_metadata(self):
        """All model tables should be registered in Base.metadata."""
        from src.core.database import Base

        table_names = set(Base.metadata.tables.keys())
        expected_tables = {
            "users",
            "sellers",
            "stores",
            "categories",
            "products",
        }
        assert expected_tables.issubset(table_names)

    def test_models_can_create_all_in_memory(self):
        """All models should be creatable in an in-memory SQLite database."""
        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(test_engine)
        # Verify all tables exist
        from sqlalchemy import inspect

        inspector = inspect(test_engine)
        table_names = set(inspector.get_table_names())
        expected_tables = {
            "users",
            "sellers",
            "stores",
            "categories",
            "products",
        }
        assert expected_tables.issubset(table_names)
        test_engine.dispose()
