"""Unit tests for order models.

Tests use SQLAlchemy inspection to verify model structure
without requiring a live database.
"""

import pytest
from sqlalchemy import inspect
from sqlalchemy.schema import CheckConstraint, UniqueConstraint

from src.core.models.order import Commission, Order, OrderItem, OrderSubitem, Payment
from src.core.models.product import Product
from src.core.models.user import User


class TestOrderModel:
    """Tests for the Order model structure and constraints."""

    def test_order_table_name(self):
        """Order model should map to the 'orders' table."""
        assert Order.__tablename__ == "orders"

    def test_order_has_order_id_column(self):
        """Order should have an order_id primary key column."""
        mapper = inspect(Order)
        columns = {c.name: c for c in mapper.columns}
        assert "order_id" in columns
        assert columns["order_id"].primary_key

    def test_order_has_user_id_foreign_key(self):
        """Order should have a user_id foreign key to users with RESTRICT."""
        mapper = inspect(Order)
        columns = {c.name: c for c in mapper.columns}
        assert "user_id" in columns
        assert not columns["user_id"].nullable
        fks = list(columns["user_id"].foreign_keys)
        assert len(fks) == 1
        assert "users.user_id" in str(fks[0])
        assert fks[0].ondelete == "RESTRICT"

    def test_order_has_total_amount_column(self):
        """Order should have a non-nullable total_amount column."""
        mapper = inspect(Order)
        columns = {c.name: c for c in mapper.columns}
        assert "total_amount" in columns
        assert not columns["total_amount"].nullable

    def test_order_has_status_column(self):
        """Order should have a non-nullable status column defaulting to 'pending'."""
        mapper = inspect(Order)
        columns = {c.name: c for c in mapper.columns}
        assert "status" in columns
        assert not columns["status"].nullable

    def test_order_has_payment_status_column(self):
        """Order should have a non-nullable payment_status column defaulting to 'pending'."""
        mapper = inspect(Order)
        columns = {c.name: c for c in mapper.columns}
        assert "payment_status" in columns
        assert not columns["payment_status"].nullable

    def test_order_has_idempotency_key_column(self):
        """Order should have a nullable idempotency_key column."""
        mapper = inspect(Order)
        columns = {c.name: c for c in mapper.columns}
        assert "idempotency_key" in columns
        assert columns["idempotency_key"].nullable

    def test_order_has_timestamps(self):
        """Order should have created_at and updated_at columns."""
        mapper = inspect(Order)
        columns = {c.name: c for c in mapper.columns}
        assert "created_at" in columns
        assert not columns["created_at"].nullable
        assert "updated_at" in columns
        assert not columns["updated_at"].nullable

    def test_order_has_user_relationship(self):
        """Order should have a user relationship."""
        mapper = inspect(Order)
        relationships = {r.key: r for r in mapper.relationships}
        assert "user" in relationships
        assert relationships["user"].direction.name == "MANYTOONE"

    def test_order_has_items_relationship(self):
        """Order should have an items relationship to OrderItem."""
        mapper = inspect(Order)
        relationships = {r.key: r for r in mapper.relationships}
        assert "items" in relationships
        assert relationships["items"].direction.name == "ONETOMANY"

    def test_order_has_subitems_relationship(self):
        """Order should have a subitems relationship to OrderSubitem."""
        mapper = inspect(Order)
        relationships = {r.key: r for r in mapper.relationships}
        assert "subitems" in relationships
        assert relationships["subitems"].direction.name == "ONETOMANY"

    def test_order_has_payments_relationship(self):
        """Order should have a payments relationship to Payment."""
        mapper = inspect(Order)
        relationships = {r.key: r for r in mapper.relationships}
        assert "payments" in relationships
        assert relationships["payments"].direction.name == "ONETOMANY"

    def test_order_has_idempotency_unique_constraint(self):
        """Order should have a unique constraint on (user_id, idempotency_key)."""
        constraints = Order.__table_args__
        unique_constraints = [
            c for c in constraints if isinstance(c, UniqueConstraint)
        ]
        assert len(unique_constraints) == 1
        constraint_columns = list(unique_constraints[0].columns)
        assert "user_id" in [c.name for c in constraint_columns]
        assert "idempotency_key" in [c.name for c in constraint_columns]

    def test_order_can_be_instantiated(self):
        """Order model can be instantiated with valid attributes."""
        order = Order(
            order_id="order-123",
            user_id="user-456",
            total_amount=99.99,
            status="pending",
            payment_status="pending",
        )
        assert order.order_id == "order-123"
        assert order.user_id == "user-456"
        assert order.total_amount == 99.99
        assert order.status == "pending"
        assert order.payment_status == "pending"


class TestOrderItemModel:
    """Tests for the OrderItem model structure and constraints."""

    def test_order_item_table_name(self):
        """OrderItem model should map to the 'order_items' table."""
        assert OrderItem.__tablename__ == "order_items"

    def test_order_item_has_order_item_id_column(self):
        """OrderItem should have an order_item_id primary key column."""
        mapper = inspect(OrderItem)
        columns = {c.name: c for c in mapper.columns}
        assert "order_item_id" in columns
        assert columns["order_item_id"].primary_key

    def test_order_item_has_order_id_foreign_key(self):
        """OrderItem should have an order_id foreign key to orders with CASCADE."""
        mapper = inspect(OrderItem)
        columns = {c.name: c for c in mapper.columns}
        assert "order_id" in columns
        assert not columns["order_id"].nullable
        fks = list(columns["order_id"].foreign_keys)
        assert len(fks) == 1
        assert "orders.order_id" in str(fks[0])
        assert fks[0].ondelete == "CASCADE"

    def test_order_item_has_product_id_foreign_key(self):
        """OrderItem should have a product_id foreign key to products with RESTRICT."""
        mapper = inspect(OrderItem)
        columns = {c.name: c for c in mapper.columns}
        assert "product_id" in columns
        assert not columns["product_id"].nullable
        fks = list(columns["product_id"].foreign_keys)
        assert len(fks) == 1
        assert "products.product_id" in str(fks[0])
        assert fks[0].ondelete == "RESTRICT"

    def test_order_item_has_seller_id_foreign_key(self):
        """OrderItem should have a seller_id foreign key to sellers with RESTRICT."""
        mapper = inspect(OrderItem)
        columns = {c.name: c for c in mapper.columns}
        assert "seller_id" in columns
        assert not columns["seller_id"].nullable
        fks = list(columns["seller_id"].foreign_keys)
        assert len(fks) == 1
        assert "sellers.seller_id" in str(fks[0])
        assert fks[0].ondelete == "RESTRICT"

    def test_order_item_has_product_name_snapshot(self):
        """OrderItem should have a non-nullable product_name snapshot column."""
        mapper = inspect(OrderItem)
        columns = {c.name: c for c in mapper.columns}
        assert "product_name" in columns
        assert not columns["product_name"].nullable

    def test_order_item_has_product_sku_snapshot(self):
        """OrderItem should have a nullable product_sku snapshot column."""
        mapper = inspect(OrderItem)
        columns = {c.name: c for c in mapper.columns}
        assert "product_sku" in columns
        assert columns["product_sku"].nullable

    def test_order_item_has_quantity_column(self):
        """OrderItem should have a non-nullable quantity column."""
        mapper = inspect(OrderItem)
        columns = {c.name: c for c in mapper.columns}
        assert "quantity" in columns
        assert not columns["quantity"].nullable

    def test_order_item_has_price_column(self):
        """OrderItem should have a non-nullable price column."""
        mapper = inspect(OrderItem)
        columns = {c.name: c for c in mapper.columns}
        assert "price" in columns
        assert not columns["price"].nullable

    def test_order_item_has_created_at_column(self):
        """OrderItem should have a non-nullable created_at column."""
        mapper = inspect(OrderItem)
        columns = {c.name: c for c in mapper.columns}
        assert "created_at" in columns
        assert not columns["created_at"].nullable

    def test_order_item_has_quantity_check_constraint(self):
        """OrderItem should have a check constraint enforcing quantity > 0."""
        constraints = OrderItem.__table_args__
        check_constraints = [
            c for c in constraints if isinstance(c, CheckConstraint)
        ]
        assert len(check_constraints) == 1
        assert "quantity > 0" in str(check_constraints[0].sqltext)

    def test_order_item_has_order_relationship(self):
        """OrderItem should have an order relationship."""
        mapper = inspect(OrderItem)
        relationships = {r.key: r for r in mapper.relationships}
        assert "order" in relationships
        assert relationships["order"].direction.name == "MANYTOONE"

    def test_order_item_has_product_relationship(self):
        """OrderItem should have a product relationship."""
        mapper = inspect(OrderItem)
        relationships = {r.key: r for r in mapper.relationships}
        assert "product" in relationships
        assert relationships["product"].direction.name == "MANYTOONE"

    def test_order_item_has_seller_relationship(self):
        """OrderItem should have a seller relationship."""
        mapper = inspect(OrderItem)
        relationships = {r.key: r for r in mapper.relationships}
        assert "seller" in relationships
        assert relationships["seller"].direction.name == "MANYTOONE"

    def test_order_item_can_be_instantiated(self):
        """OrderItem model can be instantiated with valid attributes."""
        item = OrderItem(
            order_item_id="item-123",
            order_id="order-456",
            product_id="product-789",
            seller_id="seller-abc",
            product_name="Test Product",
            product_sku="SKU-001",
            quantity=2,
            price=29.99,
        )
        assert item.order_item_id == "item-123"
        assert item.order_id == "order-456"
        assert item.product_id == "product-789"
        assert item.seller_id == "seller-abc"
        assert item.product_name == "Test Product"
        assert item.product_sku == "SKU-001"
        assert item.quantity == 2
        assert item.price == 29.99


class TestOrderSubitemModel:
    """Tests for the OrderSubitem model structure and constraints."""

    def test_order_subitem_table_name(self):
        """OrderSubitem model should map to the 'order_subitems' table."""
        assert OrderSubitem.__tablename__ == "order_subitems"

    def test_order_subitem_has_order_subitem_id_column(self):
        """OrderSubitem should have an order_subitem_id primary key column."""
        mapper = inspect(OrderSubitem)
        columns = {c.name: c for c in mapper.columns}
        assert "order_subitem_id" in columns
        assert columns["order_subitem_id"].primary_key

    def test_order_subitem_has_order_id_foreign_key(self):
        """OrderSubitem should have an order_id foreign key to orders with CASCADE."""
        mapper = inspect(OrderSubitem)
        columns = {c.name: c for c in mapper.columns}
        assert "order_id" in columns
        assert not columns["order_id"].nullable
        fks = list(columns["order_id"].foreign_keys)
        assert len(fks) == 1
        assert "orders.order_id" in str(fks[0])
        assert fks[0].ondelete == "CASCADE"

    def test_order_subitem_has_seller_id_foreign_key(self):
        """OrderSubitem should have a seller_id foreign key to sellers with RESTRICT."""
        mapper = inspect(OrderSubitem)
        columns = {c.name: c for c in mapper.columns}
        assert "seller_id" in columns
        assert not columns["seller_id"].nullable
        fks = list(columns["seller_id"].foreign_keys)
        assert len(fks) == 1
        assert "sellers.seller_id" in str(fks[0])
        assert fks[0].ondelete == "RESTRICT"

    def test_order_subitem_has_subtotal_column(self):
        """OrderSubitem should have a non-nullable subtotal column."""
        mapper = inspect(OrderSubitem)
        columns = {c.name: c for c in mapper.columns}
        assert "subtotal" in columns
        assert not columns["subtotal"].nullable

    def test_order_subitem_has_status_column(self):
        """OrderSubitem should have a non-nullable status column defaulting to 'pending'."""
        mapper = inspect(OrderSubitem)
        columns = {c.name: c for c in mapper.columns}
        assert "status" in columns
        assert not columns["status"].nullable

    def test_order_subitem_has_created_at_column(self):
        """OrderSubitem should have a non-nullable created_at column."""
        mapper = inspect(OrderSubitem)
        columns = {c.name: c for c in mapper.columns}
        assert "created_at" in columns
        assert not columns["created_at"].nullable

    def test_order_subitem_has_order_relationship(self):
        """OrderSubitem should have an order relationship."""
        mapper = inspect(OrderSubitem)
        relationships = {r.key: r for r in mapper.relationships}
        assert "order" in relationships
        assert relationships["order"].direction.name == "MANYTOONE"

    def test_order_subitem_has_seller_relationship(self):
        """OrderSubitem should have a seller relationship."""
        mapper = inspect(OrderSubitem)
        relationships = {r.key: r for r in mapper.relationships}
        assert "seller" in relationships
        assert relationships["seller"].direction.name == "MANYTOONE"

    def test_order_subitem_has_unique_order_seller_constraint(self):
        """OrderSubitem should have a unique constraint on (order_id, seller_id)."""
        constraints = OrderSubitem.__table_args__
        unique_constraints = [
            c for c in constraints if isinstance(c, UniqueConstraint)
        ]
        assert len(unique_constraints) == 1
        constraint_columns = list(unique_constraints[0].columns)
        assert "order_id" in [c.name for c in constraint_columns]
        assert "seller_id" in [c.name for c in constraint_columns]

    def test_order_subitem_can_be_instantiated(self):
        """OrderSubitem model can be instantiated with valid attributes."""
        subitem = OrderSubitem(
            order_subitem_id="subitem-123",
            order_id="order-456",
            seller_id="seller-abc",
            subtotal=59.98,
            status="pending",
        )
        assert subitem.order_subitem_id == "subitem-123"
        assert subitem.order_id == "order-456"
        assert subitem.seller_id == "seller-abc"
        assert subitem.subtotal == 59.98
        assert subitem.status == "pending"


class TestPaymentModel:
    """Tests for the Payment model structure and constraints."""

    def test_payment_table_name(self):
        """Payment model should map to the 'payments' table."""
        assert Payment.__tablename__ == "payments"

    def test_payment_has_payment_id_column(self):
        """Payment should have a payment_id primary key column."""
        mapper = inspect(Payment)
        columns = {c.name: c for c in mapper.columns}
        assert "payment_id" in columns
        assert columns["payment_id"].primary_key

    def test_payment_has_order_id_foreign_key(self):
        """Payment should have an order_id foreign key to orders with CASCADE."""
        mapper = inspect(Payment)
        columns = {c.name: c for c in mapper.columns}
        assert "order_id" in columns
        assert not columns["order_id"].nullable
        fks = list(columns["order_id"].foreign_keys)
        assert len(fks) == 1
        assert "orders.order_id" in str(fks[0])
        assert fks[0].ondelete == "CASCADE"

    def test_payment_has_amount_column(self):
        """Payment should have a non-nullable amount column."""
        mapper = inspect(Payment)
        columns = {c.name: c for c in mapper.columns}
        assert "amount" in columns
        assert not columns["amount"].nullable

    def test_payment_has_method_column(self):
        """Payment should have a non-nullable method column."""
        mapper = inspect(Payment)
        columns = {c.name: c for c in mapper.columns}
        assert "method" in columns
        assert not columns["method"].nullable

    def test_payment_has_status_column(self):
        """Payment should have a non-nullable status column defaulting to 'pending'."""
        mapper = inspect(Payment)
        columns = {c.name: c for c in mapper.columns}
        assert "status" in columns
        assert not columns["status"].nullable

    def test_payment_has_transaction_id_column(self):
        """Payment should have a nullable transaction_id column."""
        mapper = inspect(Payment)
        columns = {c.name: c for c in mapper.columns}
        assert "transaction_id" in columns
        assert columns["transaction_id"].nullable

    def test_payment_has_processed_at_column(self):
        """Payment should have a nullable processed_at column."""
        mapper = inspect(Payment)
        columns = {c.name: c for c in mapper.columns}
        assert "processed_at" in columns
        assert columns["processed_at"].nullable

    def test_payment_has_idempotency_key_column(self):
        """Payment should have a nullable idempotency_key column."""
        mapper = inspect(Payment)
        columns = {c.name: c for c in mapper.columns}
        assert "idempotency_key" in columns
        assert columns["idempotency_key"].nullable

    def test_payment_has_created_at_column(self):
        """Payment should have a non-nullable created_at column."""
        mapper = inspect(Payment)
        columns = {c.name: c for c in mapper.columns}
        assert "created_at" in columns
        assert not columns["created_at"].nullable

    def test_payment_has_idempotency_unique_constraint(self):
        """Payment should have a unique constraint on (order_id, idempotency_key)."""
        constraints = Payment.__table_args__
        unique_constraints = [
            c for c in constraints if isinstance(c, UniqueConstraint)
        ]
        assert len(unique_constraints) == 1
        constraint_columns = list(unique_constraints[0].columns)
        assert "order_id" in [c.name for c in constraint_columns]
        assert "idempotency_key" in [c.name for c in constraint_columns]

    def test_payment_has_order_relationship(self):
        """Payment should have an order relationship."""
        mapper = inspect(Payment)
        relationships = {r.key: r for r in mapper.relationships}
        assert "order" in relationships
        assert relationships["order"].direction.name == "MANYTOONE"

    def test_payment_can_be_instantiated(self):
        """Payment model can be instantiated with valid attributes."""
        payment = Payment(
            payment_id="payment-123",
            order_id="order-456",
            amount=99.99,
            method="simulated",
            status="pending",
        )
        assert payment.payment_id == "payment-123"
        assert payment.order_id == "order-456"
        assert payment.amount == 99.99
        assert payment.method == "simulated"
        assert payment.status == "pending"


class TestCommissionModel:
    """Tests for the Commission model structure and constraints."""

    def test_commission_table_name(self):
        """Commission model should map to the 'commissions' table."""
        assert Commission.__tablename__ == "commissions"

    def test_commission_has_commission_id_column(self):
        """Commission should have a commission_id primary key column."""
        mapper = inspect(Commission)
        columns = {c.name: c for c in mapper.columns}
        assert "commission_id" in columns
        assert columns["commission_id"].primary_key

    def test_commission_has_seller_id_foreign_key(self):
        """Commission should have a seller_id foreign key to sellers with RESTRICT."""
        mapper = inspect(Commission)
        columns = {c.name: c for c in mapper.columns}
        assert "seller_id" in columns
        assert not columns["seller_id"].nullable
        fks = list(columns["seller_id"].foreign_keys)
        assert len(fks) == 1
        assert "sellers.seller_id" in str(fks[0])
        assert fks[0].ondelete == "RESTRICT"

    def test_commission_has_order_subitem_id_foreign_key(self):
        """Commission should have an order_subitem_id foreign key to order_subitems with RESTRICT."""
        mapper = inspect(Commission)
        columns = {c.name: c for c in mapper.columns}
        assert "order_subitem_id" in columns
        assert not columns["order_subitem_id"].nullable
        fks = list(columns["order_subitem_id"].foreign_keys)
        assert len(fks) == 1
        assert "order_subitems.order_subitem_id" in str(fks[0])
        assert fks[0].ondelete == "RESTRICT"

    def test_commission_has_amount_column(self):
        """Commission should have a non-nullable amount column."""
        mapper = inspect(Commission)
        columns = {c.name: c for c in mapper.columns}
        assert "amount" in columns
        assert not columns["amount"].nullable

    def test_commission_has_status_column(self):
        """Commission should have a non-nullable status column defaulting to 'pending'."""
        mapper = inspect(Commission)
        columns = {c.name: c for c in mapper.columns}
        assert "status" in columns
        assert not columns["status"].nullable

    def test_commission_has_paid_at_column(self):
        """Commission should have a nullable paid_at column."""
        mapper = inspect(Commission)
        columns = {c.name: c for c in mapper.columns}
        assert "paid_at" in columns
        assert columns["paid_at"].nullable

    def test_commission_has_created_at_column(self):
        """Commission should have a non-nullable created_at column."""
        mapper = inspect(Commission)
        columns = {c.name: c for c in mapper.columns}
        assert "created_at" in columns
        assert not columns["created_at"].nullable

    def test_commission_has_unique_order_subitem_constraint(self):
        """Commission should have a unique constraint on order_subitem_id."""
        constraints = Commission.__table_args__
        unique_constraints = [
            c for c in constraints if isinstance(c, UniqueConstraint)
        ]
        assert len(unique_constraints) == 1
        constraint_columns = list(unique_constraints[0].columns)
        assert "order_subitem_id" in [c.name for c in constraint_columns]

    def test_commission_has_seller_relationship(self):
        """Commission should have a seller relationship."""
        mapper = inspect(Commission)
        relationships = {r.key: r for r in mapper.relationships}
        assert "seller" in relationships
        assert relationships["seller"].direction.name == "MANYTOONE"

    def test_commission_has_order_subitem_relationship(self):
        """Commission should have an order_subitem relationship."""
        mapper = inspect(Commission)
        relationships = {r.key: r for r in mapper.relationships}
        assert "order_subitem" in relationships
        assert relationships["order_subitem"].direction.name == "MANYTOONE"

    def test_commission_can_be_instantiated(self):
        """Commission model can be instantiated with valid attributes."""
        commission = Commission(
            commission_id="comm-123",
            seller_id="seller-abc",
            order_subitem_id="subitem-456",
            amount=5.99,
            status="pending",
        )
        assert commission.commission_id == "comm-123"
        assert commission.seller_id == "seller-abc"
        assert commission.order_subitem_id == "subitem-456"
        assert commission.amount == 5.99
        assert commission.status == "pending"


class TestProductReservedQuantity:
    """Tests for Product.reserved_quantity and stock CHECK constraints."""

    def test_product_has_reserved_quantity_column(self):
        """Product should have a non-nullable reserved_quantity column defaulting to 0."""
        mapper = inspect(Product)
        columns = {c.name: c for c in mapper.columns}
        assert "reserved_quantity" in columns
        assert not columns["reserved_quantity"].nullable

    def test_product_has_stock_check_constraint(self):
        """Product should have a check constraint enforcing stock >= 0."""
        constraints = Product.__table_args__
        check_constraints = [
            c for c in constraints if isinstance(c, CheckConstraint)
        ]
        check_texts = [str(c.sqltext) for c in check_constraints]
        assert any("stock >= 0" in ct for ct in check_texts)

    def test_product_has_reserved_quantity_check_constraint(self):
        """Product should have a check constraint enforcing reserved_quantity >= 0."""
        constraints = Product.__table_args__
        check_constraints = [
            c for c in constraints if isinstance(c, CheckConstraint)
        ]
        check_texts = [str(c.sqltext) for c in check_constraints]
        assert any("reserved_quantity >= 0" in ct for ct in check_texts)

    def test_product_has_reserved_quantity_lte_stock_check_constraint(self):
        """Product should have a check constraint enforcing reserved_quantity <= stock."""
        constraints = Product.__table_args__
        check_constraints = [
            c for c in constraints if isinstance(c, CheckConstraint)
        ]
        check_texts = [str(c.sqltext) for c in check_constraints]
        assert any("reserved_quantity <= stock" in ct for ct in check_texts)

    def test_product_can_be_instantiated_with_reserved_quantity(self):
        """Product model can be instantiated with reserved_quantity."""
        product = Product(
            product_id="product-123",
            store_id="store-456",
            category_id="category-789",
            name="Test Product",
            price=29.99,
            sku="SKU-001",
            stock=10,
            reserved_quantity=2,
        )
        assert product.stock == 10
        assert product.reserved_quantity == 2
