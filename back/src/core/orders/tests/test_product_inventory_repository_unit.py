"""Unit tests for ProductInventoryRepository.

Tests use SQLAlchemy with an in-memory SQLite database to verify
actual repository behavior without requiring a PostgreSQL database.

Note: SQLite does not provide PostgreSQL-equivalent ``SELECT FOR UPDATE``
semantics. These tests verify that the correct SQLAlchemy query methods
are called and that business logic (stock calculations, reservation,
consumption) is correct. Actual row-locking/concurrency verification
must be done with PostgreSQL integration tests against
``plataforma_comercio_test``.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.database import Base
from src.core.models.product import Product
from src.core.orders.repositories import ProductInventoryRepository


def _create_session() -> Session:
    """Create an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


class TestProductInventoryRepository:
    """Tests for ProductInventoryRepository."""

    def test_repository_construction(self):
        """Repository should store the database session."""
        session = _create_session()
        repo = ProductInventoryRepository(session)
        assert repo.db is session
        session.close()

    def test_lock_products_retrieves_multiple_products(self):
        """lock_products should retrieve multiple locked products."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=0,
        )
        p2 = Product(
            product_id="prod-2",
            store_id="store-1",
            category_id="cat-1",
            name="Product 2",
            price=20.00,
            sku="SKU-002",
            stock=50,
            reserved_quantity=0,
        )
        session.add(p1)
        session.add(p2)
        session.flush()

        result = repo.lock_products(["prod-1", "prod-2"])
        assert len(result) == 2
        result_ids = {p.product_id for p in result}
        assert result_ids == {"prod-1", "prod-2"}
        assert result[0].stock == 100
        assert result[1].stock == 50

        session.close()

    def test_lock_products_deterministic_ordering(self):
        """lock_products should return products in ascending product_id order."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        # Insert products out of order
        p_z = Product(
            product_id="prod-z",
            store_id="store-1",
            category_id="cat-1",
            name="Product Z",
            price=10.00,
            sku="SKU-Z",
            stock=10,
            reserved_quantity=0,
        )
        p_a = Product(
            product_id="prod-a",
            store_id="store-1",
            category_id="cat-1",
            name="Product A",
            price=10.00,
            sku="SKU-A",
            stock=10,
            reserved_quantity=0,
        )
        session.add(p_z)
        session.add(p_a)
        session.flush()

        result = repo.lock_products(["prod-z", "prod-a"])
        assert len(result) == 2
        assert result[0].product_id == "prod-a"
        assert result[1].product_id == "prod-z"

        session.close()

    def test_lock_products_deduplicates_ids(self):
        """lock_products should deduplicate requested product IDs."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=0,
        )
        session.add(p1)
        session.flush()

        result = repo.lock_products(["prod-1", "prod-1", "prod-1"])
        assert len(result) == 1
        assert result[0].product_id == "prod-1"

        session.close()

    def test_lock_products_raises_for_missing_product(self):
        """lock_products should raise ValueError for missing product IDs."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        with pytest.raises(ValueError, match="Products not found"):
            repo.lock_products(["prod-nonexistent"])

        session.close()

    def test_lock_products_partial_missing_raises(self):
        """lock_products should raise if some products are missing."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=0,
        )
        session.add(p1)
        session.flush()

        with pytest.raises(ValueError, match="Products not found"):
            repo.lock_products(["prod-1", "prod-missing"])

        session.close()

    def test_check_available_stock_true(self):
        """check_available_stock should return True when stock >= quantity."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=20,
        )
        session.add(p1)
        session.flush()

        result = repo.check_available_stock(p1, 80)
        assert result is True

        session.close()

    def test_check_available_stock_false(self):
        """check_available_stock should return False when insufficient stock."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=95,
        )
        session.add(p1)
        session.flush()

        result = repo.check_available_stock(p1, 10)
        assert result is False

        session.close()

    def test_check_available_stock_exact_match(self):
        """check_available_stock should return True when stock == quantity."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=50,
            reserved_quantity=0,
        )
        session.add(p1)
        session.flush()

        result = repo.check_available_stock(p1, 50)
        assert result is True

        session.close()

    def test_check_available_stock_invalid_quantity(self):
        """check_available_stock should raise ValueError for invalid quantity."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=0,
        )
        session.add(p1)
        session.flush()

        with pytest.raises(ValueError, match="Quantity must be positive"):
            repo.check_available_stock(p1, 0)

        with pytest.raises(ValueError, match="Quantity must be positive"):
            repo.check_available_stock(p1, -5)

        session.close()

    def test_reserve_quantity_success(self):
        """reserve_quantity should increase reserved_quantity."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=10,
        )
        session.add(p1)
        session.flush()

        repo.reserve_quantity(p1, 30)
        assert p1.reserved_quantity == 40

        session.close()

    def test_reserve_quantity_invalid_quantity(self):
        """reserve_quantity should raise ValueError for invalid quantity."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=0,
        )
        session.add(p1)
        session.flush()

        with pytest.raises(ValueError, match="Quantity must be positive"):
            repo.reserve_quantity(p1, 0)

        with pytest.raises(ValueError, match="Quantity must be positive"):
            repo.reserve_quantity(p1, -5)

        session.close()

    def test_release_reservation_success(self):
        """release_reservation should decrease reserved_quantity."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=50,
        )
        session.add(p1)
        session.flush()

        repo.release_reservation(p1, 30)
        assert p1.reserved_quantity == 20

        session.close()

    def test_release_reservation_negative_rejection(self):
        """release_reservation should raise ValueError if reserved_quantity would go negative."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=10,
        )
        session.add(p1)
        session.flush()

        with pytest.raises(ValueError, match="Cannot release 20 from reserved_quantity 10"):
            repo.release_reservation(p1, 20)

        session.close()

    def test_release_reservation_invalid_quantity(self):
        """release_reservation should raise ValueError for invalid quantity."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=50,
        )
        session.add(p1)
        session.flush()

        with pytest.raises(ValueError, match="Quantity must be positive"):
            repo.release_reservation(p1, 0)

        with pytest.raises(ValueError, match="Quantity must be positive"):
            repo.release_reservation(p1, -5)

        session.close()

    def test_confirm_consumption_success(self):
        """confirm_consumption should decrease both stock and reserved_quantity."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=50,
        )
        session.add(p1)
        session.flush()

        repo.confirm_consumption(p1, 30)
        assert p1.stock == 70
        assert p1.reserved_quantity == 20

        session.close()

    def test_confirm_consumption_exceeds_reserved_quantity(self):
        """confirm_consumption should raise ValueError if quantity > reserved_quantity."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=10,
        )
        session.add(p1)
        session.flush()

        with pytest.raises(ValueError, match="Cannot consume 30 from reserved_quantity 10"):
            repo.confirm_consumption(p1, 30)

        session.close()

    def test_confirm_consumption_exceeds_stock(self):
        """confirm_consumption should raise ValueError if quantity > reserved_quantity."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=10,
            reserved_quantity=10,
        )
        session.add(p1)
        session.flush()

        # When quantity exceeds stock, reserved_quantity (<= stock) is also
        # exceeded, so the reserved_quantity check fires first.
        with pytest.raises(ValueError, match="Cannot consume 20 from reserved_quantity 10"):
            repo.confirm_consumption(p1, 20)

        session.close()

    def test_confirm_consumption_invalid_quantity(self):
        """confirm_consumption should raise ValueError for invalid quantity."""
        session = _create_session()
        repo = ProductInventoryRepository(session)

        p1 = Product(
            product_id="prod-1",
            store_id="store-1",
            category_id="cat-1",
            name="Product 1",
            price=10.00,
            sku="SKU-001",
            stock=100,
            reserved_quantity=50,
        )
        session.add(p1)
        session.flush()

        with pytest.raises(ValueError, match="Quantity must be positive"):
            repo.confirm_consumption(p1, 0)

        with pytest.raises(ValueError, match="Quantity must be positive"):
            repo.confirm_consumption(p1, -5)

        session.close()

    def test_repository_has_no_commit_method(self):
        """Repository should not expose commit method."""
        session = _create_session()
        repo = ProductInventoryRepository(session)
        assert not hasattr(repo, "commit")
        session.close()

    def test_repository_has_no_rollback_method(self):
        """Repository should not expose rollback method."""
        session = _create_session()
        repo = ProductInventoryRepository(session)
        assert not hasattr(repo, "rollback")
        session.close()

    def test_repository_has_no_refresh_method(self):
        """Repository should not expose refresh method."""
        session = _create_session()
        repo = ProductInventoryRepository(session)
        assert not hasattr(repo, "refresh")
        session.close()
