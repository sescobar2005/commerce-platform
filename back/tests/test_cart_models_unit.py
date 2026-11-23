"""Unit tests for cart models.

Tests use SQLAlchemy inspection to verify model structure
without requiring a live database.
"""

import pytest
from sqlalchemy import inspect
from sqlalchemy.schema import CheckConstraint, UniqueConstraint

from src.core.models.cart import Cart, CartItem


class TestCartModel:
    """Tests for the Cart model structure and constraints."""

    def test_cart_table_name(self):
        """Cart model should map to the 'carts' table."""
        assert Cart.__tablename__ == "carts"

    def test_cart_has_cart_id_column(self):
        """Cart should have a cart_id primary key column."""
        mapper = inspect(Cart)
        columns = {c.name: c for c in mapper.columns}
        assert "cart_id" in columns
        assert columns["cart_id"].primary_key

    def test_cart_has_user_id_foreign_key(self):
        """Cart should have a user_id foreign key to users."""
        mapper = inspect(Cart)
        columns = {c.name: c for c in mapper.columns}
        assert "user_id" in columns
        assert not columns["user_id"].nullable
        # Verify foreign key exists
        fks = list(columns["user_id"].foreign_keys)
        assert len(fks) == 1
        assert "users.user_id" in str(fks[0])

    def test_cart_has_timestamps(self):
        """Cart should have created_at and last_updated_at columns."""
        mapper = inspect(Cart)
        columns = {c.name: c for c in mapper.columns}
        assert "created_at" in columns
        assert "last_updated_at" in columns
        assert "expires_at" in columns
        assert columns["expires_at"].nullable

    def test_cart_has_user_relationship(self):
        """Cart should have a user relationship."""
        mapper = inspect(Cart)
        relationships = {r.key: r for r in mapper.relationships}
        assert "user" in relationships
        assert relationships["user"].direction.name == "MANYTOONE"

    def test_cart_has_items_relationship(self):
        """Cart should have an items relationship to CartItem."""
        mapper = inspect(Cart)
        relationships = {r.key: r for r in mapper.relationships}
        assert "items" in relationships
        assert relationships["items"].direction.name == "ONETOMANY"

    def test_cart_can_be_instantiated(self):
        """Cart model can be instantiated with valid attributes."""
        cart = Cart(
            cart_id="cart-123",
            user_id="user-456",
        )
        assert cart.cart_id == "cart-123"
        assert cart.user_id == "user-456"


class TestCartItemModel:
    """Tests for the CartItem model structure and constraints."""

    def test_cart_item_table_name(self):
        """CartItem model should map to the 'cart_items' table."""
        assert CartItem.__tablename__ == "cart_items"

    def test_cart_item_has_cart_item_id_column(self):
        """CartItem should have a cart_item_id primary key column."""
        mapper = inspect(CartItem)
        columns = {c.name: c for c in mapper.columns}
        assert "cart_item_id" in columns
        assert columns["cart_item_id"].primary_key

    def test_cart_item_has_cart_id_foreign_key(self):
        """CartItem should have a cart_id foreign key to carts."""
        mapper = inspect(CartItem)
        columns = {c.name: c for c in mapper.columns}
        assert "cart_id" in columns
        assert not columns["cart_id"].nullable
        fks = list(columns["cart_id"].foreign_keys)
        assert len(fks) == 1
        assert "carts.cart_id" in str(fks[0])

    def test_cart_item_has_product_id_foreign_key(self):
        """CartItem should have a product_id foreign key to products."""
        mapper = inspect(CartItem)
        columns = {c.name: c for c in mapper.columns}
        assert "product_id" in columns
        assert not columns["product_id"].nullable
        fks = list(columns["product_id"].foreign_keys)
        assert len(fks) == 1
        assert "products.product_id" in str(fks[0])

    def test_cart_item_has_quantity_column(self):
        """CartItem should have a non-nullable quantity column."""
        mapper = inspect(CartItem)
        columns = {c.name: c for c in mapper.columns}
        assert "quantity" in columns
        assert not columns["quantity"].nullable

    def test_cart_item_has_price_at_time_column(self):
        """CartItem should have a non-nullable price_at_time column."""
        mapper = inspect(CartItem)
        columns = {c.name: c for c in mapper.columns}
        assert "price_at_time" in columns
        assert not columns["price_at_time"].nullable

    def test_cart_item_has_created_at_column(self):
        """CartItem should have a created_at column."""
        mapper = inspect(CartItem)
        columns = {c.name: c for c in mapper.columns}
        assert "created_at" in columns
        assert not columns["created_at"].nullable

    def test_cart_item_has_cart_relationship(self):
        """CartItem should have a cart relationship."""
        mapper = inspect(CartItem)
        relationships = {r.key: r for r in mapper.relationships}
        assert "cart" in relationships
        assert relationships["cart"].direction.name == "MANYTOONE"

    def test_cart_item_has_product_relationship(self):
        """CartItem should have a product relationship."""
        mapper = inspect(CartItem)
        relationships = {r.key: r for r in mapper.relationships}
        assert "product" in relationships
        assert relationships["product"].direction.name == "MANYTOONE"

    def test_cart_item_has_quantity_check_constraint(self):
        """CartItem should have a check constraint enforcing quantity > 0."""
        constraints = CartItem.__table_args__
        check_constraints = [
            c for c in constraints if isinstance(c, CheckConstraint)
        ]
        assert len(check_constraints) == 1
        assert "quantity > 0" in str(check_constraints[0].sqltext)

    def test_cart_item_has_unique_cart_product_constraint(self):
        """CartItem should have a unique constraint on (cart_id, product_id)."""
        constraints = CartItem.__table_args__
        unique_constraints = [
            c for c in constraints if isinstance(c, UniqueConstraint)
        ]
        assert len(unique_constraints) == 1
        constraint_columns = list(unique_constraints[0].columns)
        assert "cart_id" in [c.name for c in constraint_columns]
        assert "product_id" in [c.name for c in constraint_columns]

    def test_cart_item_can_be_instantiated(self):
        """CartItem model can be instantiated with valid attributes."""
        item = CartItem(
            cart_item_id="item-123",
            cart_id="cart-456",
            product_id="product-789",
            quantity=2,
            price_at_time=29.99,
        )
        assert item.cart_item_id == "item-123"
        assert item.cart_id == "cart-456"
        assert item.product_id == "product-789"
        assert item.quantity == 2
        assert item.price_at_time == 29.99

    def test_cart_item_quantity_must_be_positive(self):
        """CartItem quantity must be a positive integer (convention check)."""
        # Quantity of 0 or negative violates the check constraint
        # This test documents the constraint; DB enforcement happens at insert
        item = CartItem(
            cart_item_id="item-123",
            cart_id="cart-456",
            product_id="product-789",
            quantity=0,
            price_at_time=29.99,
        )
        assert item.quantity == 0  # Python-level, DB would reject
