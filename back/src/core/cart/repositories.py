"""Repository layer for cart domain models.

Provides data access operations for Cart and CartItem entities.
Encapsulates all SQLAlchemy queries so that business logic in services
does not depend directly on database query patterns.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from src.core.models.cart import Cart, CartItem


class CartRepository:
    """Repository for Cart persistence operations.

    All database interactions related to Cart entities are encapsulated here.
    Business logic (ownership checks, stock validation, etc.) lives in
    CartService, not here.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, cart_id: str) -> Optional[Cart]:
        """Retrieve a cart by its ID, eagerly loading items and products.

        Uses joinedload to avoid N+1 queries when accessing cart items
        and their associated products.
        """
        return (
            self.db.query(Cart)
            .options(
                joinedload(Cart.items).joinedload(CartItem.product)
            )
            .filter(Cart.cart_id == cart_id)
            .first()
        )

    def get_by_id_for_update(self, cart_id: str) -> Optional[Cart]:
        """Retrieve a cart by its ID with a row-level lock.

        Acquires ``SELECT ... FOR UPDATE`` on the parent Cart row to
        coordinate concurrent mutations (e.g., order creation vs. cart
        item add/update/remove). The lock is held until the caller's
        transaction commits or rolls back.

        Uses joinedload to avoid N+1 queries when accessing cart items
        and their associated products.

        Args:
            cart_id: The cart identifier.

        Returns:
            The locked Cart if found, None otherwise.
        """
        return (
            self.db.query(Cart)
            .options(
                joinedload(Cart.items).joinedload(CartItem.product)
            )
            .filter(Cart.cart_id == cart_id)
            .with_for_update()
            .first()
        )

    def get_by_user_id(self, user_id: str) -> Optional[Cart]:
        """Retrieve the first cart belonging to a user.

        Args:
            user_id: The authenticated user's identifier.

        Returns:
            The Cart if found, None otherwise.
        """
        return (
            self.db.query(Cart)
            .filter(Cart.user_id == user_id)
            .first()
        )

    def add(self, cart: Cart) -> None:
        """Add a new cart to the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.add(cart)

    def delete(self, cart: Cart) -> None:
        """Delete a cart from the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.delete(cart)

    def commit(self) -> None:
        """Commit the current transaction on the session."""
        self.db.commit()

    def rollback(self) -> None:
        """Rollback the current transaction on the session."""
        self.db.rollback()

    def refresh(self, obj) -> None:
        """Refresh the given object from the database."""
        self.db.refresh(obj)


class CartItemRepository:
    """Repository for CartItem persistence operations.

    All database interactions related to CartItem entities are encapsulated here.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, cart_item_id: str) -> Optional[CartItem]:
        """Retrieve a cart item by its ID."""
        return (
            self.db.query(CartItem)
            .filter(CartItem.cart_item_id == cart_item_id)
            .first()
        )

    def get_by_cart_and_product(
        self, cart_id: str, product_id: str
    ) -> Optional[CartItem]:
        """Retrieve a cart item by cart ID and product ID.

        Used to check whether a product already exists in a cart,
        in which case its quantity is incremented rather than
        creating a duplicate line item.
        """
        return (
            self.db.query(CartItem)
            .filter(
                CartItem.cart_id == cart_id,
                CartItem.product_id == product_id,
            )
            .first()
        )

    def add(self, item: CartItem) -> None:
        """Add a new cart item to the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.add(item)

    def delete(self, item: CartItem) -> None:
        """Delete a cart item from the session.

        The caller is responsible for calling commit() on the session.
        """
        self.db.delete(item)

    def commit(self) -> None:
        """Commit the current transaction on the session."""
        self.db.commit()

    def rollback(self) -> None:
        """Rollback the current transaction on the session."""
        self.db.rollback()

    def refresh(self, obj) -> None:
        """Refresh the given object from the database."""
        self.db.refresh(obj)
