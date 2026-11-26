"""Service layer for order domain.

Contains all business logic for order creation from carts,
including idempotency checks, cart locking, product locking,
inventory reservation, and seller grouping.

The service owns the transaction boundary. Repositories do NOT
commit, roll back, or refresh.
"""

from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from src.core.cart.exceptions import (
    CartError,
    CartNotFoundError,
    CartOwnershipError,
)
from src.core.cart.repositories import CartRepository
from src.core.database import Session
from src.core.models.cart import Cart
from src.core.models.order import Order, OrderItem, OrderSubitem
from src.core.models.product import Product
from src.core.orders.exceptions import (
    IdempotencyConflictError,
    InsufficientStockError,
    OrderError,
    ProductInactiveError,
    ProductNotFoundError,
)
from src.core.orders.fingerprint import generate_cart_fingerprint
from src.core.orders.repositories import (
    OrderItemRepository,
    OrderRepository,
    OrderSubitemRepository,
    ProductInventoryRepository,
    StoreRepository,
)
from src.core.security.schemas import CurrentUser


class OrderService:
    """Service for order creation from cart.

    Encapsulates the complete transactional order creation flow:
    idempotency checks, cart locking, product locking, inventory
    reservation, and order record creation.

    The service owns the transaction boundary. Repositories do NOT
    commit, roll back, or refresh.
    """

    IDEMPOTENCY_KEY_MAX_LENGTH = 100

    def __init__(self, db: Session):
        self.order_repo = OrderRepository(db)
        self.order_item_repo = OrderItemRepository(db)
        self.order_subitem_repo = OrderSubitemRepository(db)
        self.product_inventory_repo = ProductInventoryRepository(db)
        self.store_repo = StoreRepository(db)
        self.cart_repo = CartRepository(db)
        self.db = db

    def create_order_from_cart(
        self,
        cart_id: str,
        current_user: CurrentUser,
        idempotency_key: Optional[str] = None,
    ) -> Order:
        """Create an order from a cart.

        Implements the full transactional order creation flow:

        1. Validate idempotency key input
        2. Lock and retrieve the cart row
        3. Handle missing-cart idempotency retries
        4. Read consistent cart snapshot
        5. Calculate canonical fingerprint
        6. Check idempotency against existing orders
        7. Lock products in ascending order
        8. Validate product active status and stock
        9. Resolve seller IDs
        10. Reserve inventory
        11. Create Order, OrderItems, OrderSubitems
        12. Commit once and return

        On any failure, rolls back the entire transaction.

        Args:
            cart_id: The cart identifier.
            current_user: The authenticated user.
            idempotency_key: Optional client idempotency key.

        Returns:
            The created Order.

        Raises:
            CartNotFoundError: If cart does not exist (and no compatible
                existing order for idempotency retry).
            CartOwnershipError: If cart belongs to another user.
            IdempotencyConflictError: If idempotency key conflicts.
            ProductNotFoundError: If a product does not exist.
            ProductInactiveError: If a product is not active.
            InsufficientStockError: If stock is insufficient.
            OrderError: For other order creation failures.
        """
        # Step 1: Validate idempotency key input
        if idempotency_key is not None:
            self._validate_idempotency_key(idempotency_key)

        # Step 2: Retrieve and lock the cart row
        cart = self.cart_repo.get_by_id_for_update(cart_id)

        # Step 3: Handle missing-cart idempotency retries
        if cart is None:
            if idempotency_key is not None:
                existing = self.order_repo.get_by_user_and_idempotency_key(
                    str(current_user.user_id), idempotency_key
                )
                if (
                    existing is not None
                    and existing.source_cart_id == cart_id
                ):
                    return existing
            raise CartNotFoundError(cart_id)

        # Revalidate ownership after acquiring the lock
        if str(cart.user_id) != current_user.user_id:
            raise CartOwnershipError(cart_id, current_user.user_id)

        # Step 4: Read consistent cart snapshot
        items = list(cart.items)
        if not items:
            raise CartError("Cart is empty")

        # Validate quantities and monetary values
        for item in items:
            if not isinstance(item.quantity, int) or item.quantity <= 0:
                raise OrderError(
                    f"Invalid quantity for product {item.product_id}: "
                    f"{item.quantity}"
                )
            if not isinstance(item.price_at_time, Decimal):
                raise OrderError(
                    f"Invalid price for product {item.product_id}: "
                    f"{item.price_at_time!r}"
                )

        # Step 5: Calculate canonical fingerprint
        fingerprint = generate_cart_fingerprint(cart)

        # Save values for IntegrityError handling after rollback
        saved_cart_id = cart_id
        saved_fingerprint = fingerprint
        saved_user_id = str(current_user.user_id)

        try:
            # Step 6: Check idempotency against existing orders
            if idempotency_key is not None:
                existing = self.order_repo.get_by_user_and_idempotency_key(
                    saved_user_id, idempotency_key
                )
                if existing is not None:
                    if (
                        existing.source_cart_id == saved_cart_id
                        and existing.request_fingerprint == saved_fingerprint
                    ):
                        return existing
                    raise IdempotencyConflictError(
                        f"Idempotency key '{idempotency_key}' conflicts "
                        f"with existing order {existing.order_id}"
                    )

            # Step 7: Lock products in ascending order
            product_ids = sorted(
                set(str(item.product_id) for item in items)
            )
            try:
                products = self.product_inventory_repo.lock_products(
                    product_ids
                )
            except ValueError as exc:
                raise ProductNotFoundError(
                    product_ids[0] if product_ids else "unknown"
                ) from exc

            product_map = {str(p.product_id): p for p in products}

            # Step 8: Validate product active status and available stock
            for item in items:
                product = product_map.get(str(item.product_id))
                if product is None:
                    raise ProductNotFoundError(str(item.product_id))

                if not product.is_active:
                    raise ProductInactiveError(str(item.product_id))

                available = product.stock - product.reserved_quantity
                if available < item.quantity:
                    raise InsufficientStockError(
                        str(item.product_id), item.quantity, available
                    )

            # Step 9: Resolve seller IDs
            store_ids = sorted(set(str(p.store_id) for p in products))
            seller_map = self.store_repo.get_seller_ids(store_ids)

            for p in products:
                if str(p.store_id) not in seller_map:
                    raise OrderError(
                        f"No seller mapping for store {p.store_id}"
                    )

            # Step 10: Reserve inventory
            for item in items:
                product = product_map[str(item.product_id)]
                self.product_inventory_repo.reserve_quantity(
                    product, item.quantity
                )

            # Step 11: Create Order
            total_amount = sum(
                (
                    Decimal(str(item.price_at_time)) * item.quantity
                    for item in items
                ),
                Decimal("0"),
            )

            order_id = str(uuid4())
            order = Order(
                order_id=order_id,
                user_id=saved_user_id,
                total_amount=total_amount,
                status="pending",
                payment_status="pending",
                idempotency_key=idempotency_key,
                source_cart_id=saved_cart_id,
                request_fingerprint=saved_fingerprint,
            )
            self.order_repo.add(order)

            # Step 12: Create OrderItems
            seller_subtotals = {}
            for item in items:
                product = product_map[str(item.product_id)]
                seller_id = seller_map[str(product.store_id)]
                line_total = (
                    Decimal(str(item.price_at_time)) * item.quantity
                )
                seller_subtotals[seller_id] = (
                    seller_subtotals.get(seller_id, Decimal("0"))
                    + line_total
                )

                order_item = OrderItem(
                    order_item_id=str(uuid4()),
                    order_id=order_id,
                    product_id=str(item.product_id),
                    seller_id=seller_id,
                    product_name=product.name,
                    product_sku=product.sku,
                    quantity=item.quantity,
                    price=Decimal(str(item.price_at_time)),
                )
                self.order_item_repo.add(order_item)

            # Step 13: Create OrderSubitems
            for seller_id, subtotal in seller_subtotals.items():
                subitem = OrderSubitem(
                    order_subitem_id=str(uuid4()),
                    order_id=order_id,
                    seller_id=seller_id,
                    subtotal=subtotal,
                    status="pending",
                )
                self.order_subitem_repo.add(subitem)

            # Step 14: Commit once
            self.db.commit()
            return order

        except IntegrityError as exc:
            self.db.rollback()
            if (
                idempotency_key is not None
                and self._is_idempotency_constraint_violation(exc)
            ):
                existing = (
                    self.order_repo.get_by_user_and_idempotency_key(
                        saved_user_id, idempotency_key
                    )
                )
                if existing is not None:
                    if (
                        existing.source_cart_id == saved_cart_id
                        and existing.request_fingerprint
                        == saved_fingerprint
                    ):
                        return existing
                    raise IdempotencyConflictError(
                        f"Idempotency key '{idempotency_key}' conflicts "
                        f"with existing order {existing.order_id}"
                    ) from exc
            raise

        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _is_idempotency_constraint_violation(
        exc: IntegrityError,
    ) -> bool:
        """Check if the IntegrityError is from the idempotency unique constraint.

        Inspects the database driver's structured error metadata
        (psycopg ``diag.constraint_name``) rather than parsing human-readable
        messages. Only the unique constraint on ``(user_id, idempotency_key)``
        is treated as an idempotency conflict; all other constraint violations
        (foreign-key, CHECK, NOT NULL, unrelated unique) are re-raised.

        Args:
            exc: The IntegrityError raised by the database driver.

        Returns:
            True if the error is positively identified as the idempotency
            unique constraint violation, False otherwise.
        """
        constraint_name = OrderService._extract_constraint_name(exc)
        return constraint_name == "uq_order_user_idempotency_key"

    @staticmethod
    def _extract_constraint_name(
        exc: IntegrityError,
    ) -> Optional[str]:
        """Extract constraint name from SQLAlchemy/driver exception metadata.

        Checks both the SQLAlchemy exception's ``diag`` attribute and the
        wrapped driver exception in ``orig`` (psycopg3 exposes
        ``diag.constraint_name`` for structured error metadata).

        Args:
            exc: The IntegrityError raised by the database driver.

        Returns:
            The constraint name if available, None otherwise.
        """
        diag = getattr(exc, "diag", None)
        if diag is not None:
            name = getattr(diag, "constraint_name", None)
            if name:
                return name

        orig = getattr(exc, "orig", None)
        if orig is not None:
            diag = getattr(orig, "diag", None)
            if diag is not None:
                name = getattr(diag, "constraint_name", None)
                if name:
                    return name

        return None

    def _validate_idempotency_key(self, idempotency_key: str) -> None:
        """Validate idempotency key against model constraints.

        Args:
            idempotency_key: The client-provided idempotency key.

        Raises:
            OrderError: If the key is empty or exceeds max length.
        """
        if not isinstance(idempotency_key, str) or len(idempotency_key) == 0:
            raise OrderError("Idempotency key must be a non-empty string")
        if len(idempotency_key) > self.IDEMPOTENCY_KEY_MAX_LENGTH:
            raise OrderError(
                f"Idempotency key exceeds maximum length of "
                f"{self.IDEMPOTENCY_KEY_MAX_LENGTH} characters"
            )
