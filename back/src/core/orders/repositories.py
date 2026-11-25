"""Repository layer for order domain models.

Provides data access operations for Order and OrderItem entities.
Encapsulates all SQLAlchemy queries so that business logic in services
does not depend directly on database query patterns.

Repositories do NOT manage transactions (commit/rollback/refresh).
The service layer owns transaction boundaries.
"""

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from src.core.models.order import Order, OrderItem


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
                joinedload(Order.items).joinedload(OrderItem.product)
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
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
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
