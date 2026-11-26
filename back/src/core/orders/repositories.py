"""Repository layer for order domain models.

Provides data access operations for Order and OrderItem entities.
Encapsulates all SQLAlchemy queries so that business logic in services
does not depend directly on database query patterns.

Repositories do NOT manage transactions (commit/rollback/refresh).
The service layer owns transaction boundaries.
"""

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from src.core.models.order import (
    Commission,
    Order,
    OrderItem,
    OrderSubitem,
    Payment,
)
from src.core.models.product import Product
from src.core.models.store import Store


class OrderRepository:
    """Repository for Order persistence operations.

    All database interactions related to Order entities are encapsulated here.
    Business logic (ownership checks, stock validation, etc.) lives in
    OrderService, not here.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, order_id: str) -> Optional[Order]:
        """Retrieve an order by its ID, eagerly loading items and products.

        Uses joinedload to avoid N+1 queries when accessing order items
        and their associated products.

        Args:
            order_id: The unique order identifier.

        Returns:
            The Order if found, None otherwise.
        """
        return (
            self.db.query(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.subitems),
            )
            .filter(Order.order_id == order_id)
            .first()
        )

    def get_by_user_id(
        self, user_id: str, skip: int = 0, limit: int = 20
    ) -> List[Order]:
        """Retrieve orders belonging to a user, with pagination.

        Only returns orders owned by the specified user, ensuring
        access isolation between users.

        Args:
            user_id: The authenticated user's identifier.
            skip: Number of records to skip (for pagination).
            limit: Maximum number of records to return.

        Returns:
            A list of Order objects belonging to the user, ordered
            by created_at descending (newest first).
        """
        return (
            self.db.query(Order)
            .filter(Order.user_id == user_id)
            .order_by(Order.created_at.desc(), Order.order_id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_user_id(self, user_id: str) -> int:
        """Count total orders belonging to a user.

        Used for pagination metadata in order listings.

        Args:
            user_id: The authenticated user's identifier.

        Returns:
            Total number of orders owned by the user.
        """
        return (
            self.db.query(Order)
            .filter(Order.user_id == user_id)
            .count()
        )

    def get_by_user_and_idempotency_key(
        self, user_id: str, idempotency_key: str
    ) -> Optional[Order]:
        """Retrieve an order by user-scoped idempotency key.

        Prevents duplicate order creation when a client retries a request
        with the same idempotency key. The lookup is scoped by both
        user_id and idempotency_key to ensure clients cannot use another
        user's idempotency key to retrieve their orders.

        Args:
            user_id: The authenticated user's identifier.
            idempotency_key: Client-provided idempotency key.

        Returns:
            The Order if found, None otherwise.
        """
        return (
            self.db.query(Order)
            .filter(
                Order.user_id == user_id,
                Order.idempotency_key == idempotency_key,
            )
            .first()
        )

    def add(self, order: Order) -> None:
        """Add a new order to the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.add(order)

    def delete(self, order: Order) -> None:
        """Delete an order from the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.delete(order)


class OrderItemRepository:
    """Repository for OrderItem persistence operations.

    All database interactions related to OrderItem entities are encapsulated here.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, order_item_id: str) -> Optional[OrderItem]:
        """Retrieve an order item by its ID.

        Args:
            order_item_id: The unique order item identifier.

        Returns:
            The OrderItem if found, None otherwise.
        """
        return (
            self.db.query(OrderItem)
            .filter(OrderItem.order_item_id == order_item_id)
            .first()
        )

    def get_by_order_id(self, order_id: str) -> List[OrderItem]:
        """Retrieve all order items belonging to an order.

        Args:
            order_id: The parent order identifier.

        Returns:
            A list of OrderItem objects belonging to the order,
            ordered by created_at ascending.
        """
        return (
            self.db.query(OrderItem)
            .filter(OrderItem.order_id == order_id)
            .order_by(OrderItem.created_at.asc())
            .all()
        )

    def add(self, item: OrderItem) -> None:
        """Add a new order item to the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.add(item)

    def delete(self, item: OrderItem) -> None:
        """Delete an order item from the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.delete(item)


class OrderSubitemRepository:
    """Repository for OrderSubitem persistence operations.

    All database interactions related to OrderSubitem entities are
    encapsulated here.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, order_subitem_id: str) -> Optional[OrderSubitem]:
        """Retrieve an order subitem by its ID.

        Args:
            order_subitem_id: The unique order subitem identifier.

        Returns:
            The OrderSubitem if found, None otherwise.
        """
        return (
            self.db.query(OrderSubitem)
            .filter(OrderSubitem.order_subitem_id == order_subitem_id)
            .first()
        )

    def get_by_order_id(self, order_id: str) -> List[OrderSubitem]:
        """Retrieve all order subitems belonging to an order.

        Args:
            order_id: The parent order identifier.

        Returns:
            A list of OrderSubitem objects belonging to the order,
            ordered by created_at ascending.
        """
        return (
            self.db.query(OrderSubitem)
            .filter(OrderSubitem.order_id == order_id)
            .order_by(OrderSubitem.created_at.asc())
            .all()
        )

    def get_by_order_and_seller(
        self, order_id: str, seller_id: str
    ) -> Optional[OrderSubitem]:
        """Retrieve a seller-specific subitem within an order.

        Args:
            order_id: The parent order identifier.
            seller_id: The seller identifier.

        Returns:
            The OrderSubitem if found, None otherwise.
        """
        return (
            self.db.query(OrderSubitem)
            .filter(
                OrderSubitem.order_id == order_id,
                OrderSubitem.seller_id == seller_id,
            )
            .first()
        )

    def add(self, subitem: OrderSubitem) -> None:
        """Add a new order subitem to the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.add(subitem)

    def delete(self, subitem: OrderSubitem) -> None:
        """Delete an order subitem from the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.delete(subitem)


class PaymentRepository:
    """Repository for Payment persistence operations.

    All database interactions related to Payment entities are encapsulated here.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, payment_id: str) -> Optional[Payment]:
        """Retrieve a payment by its ID.

        Args:
            payment_id: The unique payment identifier.

        Returns:
            The Payment if found, None otherwise.
        """
        return (
            self.db.query(Payment)
            .filter(Payment.payment_id == payment_id)
            .first()
        )

    def get_by_order_id(self, order_id: str) -> List[Payment]:
        """Retrieve all payments belonging to an order.

        Args:
            order_id: The parent order identifier.

        Returns:
            A list of Payment objects belonging to the order,
            ordered by created_at ascending.
        """
        return (
            self.db.query(Payment)
            .filter(Payment.order_id == order_id)
            .order_by(Payment.created_at.asc())
            .all()
        )

    def get_by_order_and_idempotency_key(
        self, order_id: str, idempotency_key: str
    ) -> Optional[Payment]:
        """Retrieve a payment by order-scoped idempotency key.

        Prevents duplicate payment attempts when a client retries a request
        with the same idempotency key. The lookup is scoped by both
        order_id and idempotency_key to ensure clients cannot use another
        order's idempotency key to retrieve a payment.

        Args:
            order_id: The parent order identifier.
            idempotency_key: Client-provided idempotency key.

        Returns:
            The Payment if found, None otherwise.
        """
        return (
            self.db.query(Payment)
            .filter(
                Payment.order_id == order_id,
                Payment.idempotency_key == idempotency_key,
            )
            .first()
        )

    def add(self, payment: Payment) -> None:
        """Add a new payment to the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.add(payment)

    def delete(self, payment: Payment) -> None:
        """Delete a payment from the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.delete(payment)


class CommissionRepository:
    """Repository for Commission persistence operations.

    All database interactions related to Commission entities are encapsulated here.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, commission_id: str) -> Optional[Commission]:
        """Retrieve a commission by its ID.

        Args:
            commission_id: The unique commission identifier.

        Returns:
            The Commission if found, None otherwise.
        """
        return (
            self.db.query(Commission)
            .filter(Commission.commission_id == commission_id)
            .first()
        )

    def get_by_seller_id(
        self, seller_id: str, skip: int = 0, limit: int = 20
    ) -> List[Commission]:
        """Retrieve all commissions belonging to a seller, with pagination.

        Args:
            seller_id: The seller identifier.
            skip: Number of records to skip (for pagination).
            limit: Maximum number of records to return.

        Returns:
            A list of Commission objects belonging to the seller,
            ordered by created_at descending (newest first).
        """
        return (
            self.db.query(Commission)
            .filter(Commission.seller_id == seller_id)
            .order_by(Commission.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_order_subitem_id(
        self, order_subitem_id: str
    ) -> Optional[Commission]:
        """Retrieve a commission by its order subitem ID.

        Args:
            order_subitem_id: The order subitem identifier.

        Returns:
            The Commission if found, None otherwise.
        """
        return (
            self.db.query(Commission)
            .filter(Commission.order_subitem_id == order_subitem_id)
            .first()
        )

    def add(self, commission: Commission) -> None:
        """Add a new commission to the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.add(commission)

    def delete(self, commission: Commission) -> None:
        """Delete a commission from the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.delete(commission)


class ProductInventoryRepository:
    """Repository for product inventory operations.

    All database interactions related to product inventory are
    encapsulated here. Uses SQLAlchemy ``SELECT ... FOR UPDATE`` for
    row-level locking to prevent concurrent overselling.

    Repositories do NOT manage transactions (commit/rollback/refresh).
    The service layer owns transaction boundaries.
    """

    def __init__(self, db: Session):
        self.db = db

    def lock_products(self, product_ids: List[str]) -> List[Product]:
        """Lock product rows with ``SELECT ... FOR UPDATE``.

        Products are locked in ascending ``product_id`` order to reduce
        deadlock risk. Duplicate IDs are deduplicated before querying.
        Raises ``ValueError`` if any requested product ID is not found.

        Args:
            product_ids: List of product IDs to lock.

        Returns:
            A list of locked ``Product`` objects.

        Raises:
            ValueError: If any requested product ID is not found.
        """
        # Deduplicate while preserving order, then sort ascending
        # to prevent deadlocks when multiple transactions lock products.
        unique_ids = list(dict.fromkeys(product_ids))
        if not unique_ids:
            return []

        sorted_ids = sorted(unique_ids)

        products = (
            self.db.query(Product)
            .filter(Product.product_id.in_(sorted_ids))
            .with_for_update()
            .order_by(Product.product_id.asc())
            .all()
        )

        # Verify all requested products were found
        found_ids = {p.product_id for p in products}
        missing_ids = set(sorted_ids) - found_ids
        if missing_ids:
            raise ValueError(
                f"Products not found: {sorted(missing_ids)}"
            )

        return products

    def check_available_stock(
        self, product: Product, quantity: int
    ) -> bool:
        """Check if sufficient stock is available for a locked product.

        Available stock is ``stock - reserved_quantity``.

        Args:
            product: A locked ``Product`` object (from ``lock_products``).
            quantity: Quantity to check.

        Returns:
            ``True`` if available stock >= quantity, ``False`` otherwise.

        Raises:
            ValueError: If quantity is not positive.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        return product.stock - product.reserved_quantity >= quantity

    def reserve_quantity(self, product: Product, quantity: int) -> None:
        """Reserve stock by increasing ``reserved_quantity``.

        Does not decrease ``stock``. Reserved stock is consumed later
        via :meth:`confirm_consumption`.

        Args:
            product: A locked ``Product`` object.
            quantity: Quantity to reserve.

        Raises:
            ValueError: If quantity is not positive.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if product.reserved_quantity + quantity > product.stock:
            raise ValueError(
                f"Cannot reserve {quantity} units for product "
                f"{product.product_id}: would exceed stock "
                f"{product.stock} (already reserved "
                f"{product.reserved_quantity})"
            )

        product.reserved_quantity += quantity

    def release_reservation(self, product: Product, quantity: int) -> None:
        """Release reserved stock by decreasing ``reserved_quantity``.

        Never allows ``reserved_quantity`` to become negative.

        Args:
            product: A locked ``Product`` object.
            quantity: Quantity to release.

        Raises:
            ValueError: If quantity is not positive or would make
                ``reserved_quantity`` negative.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if product.reserved_quantity < quantity:
            raise ValueError(
                f"Cannot release {quantity} from reserved_quantity "
                f"{product.reserved_quantity}"
            )

        product.reserved_quantity -= quantity

    def confirm_consumption(self, product: Product, quantity: int) -> None:
        """Consume reserved stock by decreasing both ``stock`` and
        ``reserved_quantity``.

        This should be called after payment is confirmed, to permanently
        deduct the reserved items from stock.

        Args:
            product: A locked ``Product`` object.
            quantity: Quantity to consume.

        Raises:
            ValueError: If quantity is not positive, exceeds
                ``reserved_quantity``, or exceeds ``stock``.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if product.reserved_quantity < quantity:
            raise ValueError(
                f"Cannot consume {quantity} from reserved_quantity "
                f"{product.reserved_quantity}"
            )

        if product.stock < quantity:
            raise ValueError(
                f"Cannot consume {quantity} from stock {product.stock}"
            )

        product.stock -= quantity
        product.reserved_quantity -= quantity


class StoreRepository:
    """Repository for Store persistence operations.

    Provides data access operations for Store entities, including
    efficient resolution of seller IDs for stores associated with
    order products. Used by OrderService to group order items by
    seller without N+1 queries.

    Repositories do NOT manage transactions (commit/rollback/refresh).
    The service layer owns transaction boundaries.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_seller_id(self, store_id: str) -> Optional[str]:
        """Retrieve the seller ID for a single store.

        Args:
            store_id: The store identifier.

        Returns:
            The seller ID if the store exists, None otherwise.
        """
        store = (
            self.db.query(Store)
            .filter(Store.store_id == store_id)
            .first()
        )
        if store is None:
            return None
        return str(store.seller_id)

    def get_seller_ids(self, store_ids: List[str]) -> dict:
        """Retrieve seller IDs for multiple stores in a single query.

        Avoids N+1 queries when resolving sellers for multiple products
        belonging to different stores. Returns a mapping of store ID to
        seller ID for all stores found. Stores that do not exist are
        omitted from the result.

        Args:
            store_ids: List of store identifiers to look up.

        Returns:
            A dict mapping store_id -> seller_id for found stores.
        """
        unique_ids = list(dict.fromkeys(store_ids))
        if not unique_ids:
            return {}

        stores = (
            self.db.query(Store.store_id, Store.seller_id)
            .filter(Store.store_id.in_(unique_ids))
            .all()
        )

        return {str(store_id): str(seller_id) for store_id, seller_id in stores}
