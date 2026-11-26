"""Service layer for cart domain.

Contains all business logic for cart management:
- Cart creation, retrieval, update, deletion
- Cart item add, update, removal
- Ownership validation, stock validation, price snapshot handling

Services depend only on repositories and domain models. They do not
know about HTTP, request objects, or response schemas.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.exc import IntegrityError

from src.core.models.cart import Cart, CartItem
from src.core.models.product import Product
from src.core.models.user import User
from .repositories import CartRepository, CartItemRepository
from src.core.security.schemas import CurrentUser
from .exceptions import (
    CartError,
    CartItemNotFoundError,
    CartNotFoundError,
    CartOwnershipError,
    InsufficientStockError,
    ProductInactiveError,
    ProductNotFoundError,
)


class CartService:
    """Service for cart business operations.

    Encapsulates all business rules for cart management:
    - Cart CRUD with ownership validation
    - Cart item add/update/remove with stock and availability checks
    - Price snapshot handling (prices always come from the database)
    """

    def __init__(self, db):
        self.cart_repo = CartRepository(db)
        self.item_repo = CartItemRepository(db)
        self.db = db

    def _get_locked_cart(
        self, cart_id: str, current_user: CurrentUser
    ) -> Cart:
        """Retrieve and lock the parent Cart row, verifying ownership.

        Acquires ``SELECT ... FOR UPDATE`` on the Cart row before any
        item-level read or mutation, coordinating concurrent access
        (e.g., cart mutations vs. order creation).

        Args:
            cart_id: The cart identifier.
            current_user: The authenticated user.

        Returns:
            The locked Cart object.

        Raises:
            CartNotFoundError: If the cart does not exist.
            CartOwnershipError: If the cart belongs to another user.
        """
        cart = self.cart_repo.get_by_id_for_update(cart_id)
        if cart is None:
            raise CartNotFoundError(cart_id)
        if str(cart.user_id) != current_user.user_id:
            raise CartOwnershipError(cart_id, current_user.user_id)
        return cart

    # ------------------------------------------------------------------
    # Cart-level operations
    # ------------------------------------------------------------------

    def get_cart(self, cart_id: str, current_user: CurrentUser) -> Cart:
        """Retrieve a cart by its unique identifier.

        Args:
            cart_id: The cart identifier.
            current_user: The authenticated user.

        Returns:
            The Cart object.

        Raises:
            CartNotFoundError: If the cart does not exist.
            CartOwnershipError: If the cart belongs to another user.
        """
        cart = self.cart_repo.get_by_id(cart_id)
        if cart is None:
            raise CartNotFoundError(cart_id)
        if str(cart.user_id) != current_user.user_id:
            raise CartOwnershipError(cart_id, current_user.user_id)
        return cart

    def create_cart(self, current_user: CurrentUser) -> Cart:
        """Create a new cart for the authenticated user.

        If the user already has a cart, returns the existing one
        (idempotent behavior). Otherwise creates a new cart.

        Args:
            current_user: The authenticated user.

        Returns:
            The Cart object (existing or newly created).
        """
        existing = self.cart_repo.get_by_user_id(current_user.user_id)
        if existing is not None:
            return existing

        cart = Cart(user_id=current_user.user_id)
        cart.created_at = datetime.now(timezone.utc)
        cart.last_updated_at = datetime.now(timezone.utc)
        self.cart_repo.add(cart)
        try:
            self.cart_repo.commit()
        except IntegrityError:
            self.cart_repo.rollback()
            raise CartError("Failed to create cart")
        self.cart_repo.refresh(cart)
        return cart

    def update_cart(self, cart_id: str, request, current_user: CurrentUser) -> Cart:
        """Update a cart's expires_at field.

        Only expires_at can be updated. Ownership, created_at, and
        last_updated_at are not editable.

        Args:
            cart_id: The cart identifier.
            request: Update request containing optional expires_at.
            current_user: The authenticated user.

        Returns:
            The updated Cart object.

        Raises:
            CartNotFoundError: If the cart does not exist.
            CartOwnershipError: If the cart belongs to another user.
        """
        cart = self.get_cart(cart_id, current_user)

        cart.expires_at = request.expires_at

        self.cart_repo.add(cart)
        try:
            self.cart_repo.commit()
        except IntegrityError:
            self.cart_repo.rollback()
            raise CartError("Failed to update cart")
        self.cart_repo.refresh(cart)
        return cart

    def delete_cart(self, cart_id: str, current_user: CurrentUser) -> Cart:
        """Delete a cart and all its items.

        Cart items are cascade-deleted via the relationship cascade rule.

        Args:
            cart_id: The cart identifier.
            current_user: The authenticated user.

        Returns:
            The deleted Cart object.

        Raises:
            CartNotFoundError: If the cart does not exist.
            CartOwnershipError: If the cart belongs to another user.
        """
        cart = self.get_cart(cart_id, current_user)

        self.cart_repo.delete(cart)
        try:
            self.cart_repo.commit()
        except IntegrityError:
            self.cart_repo.rollback()
            raise CartError("Failed to delete cart")
        return cart

    # ------------------------------------------------------------------
    # Cart item operations
    # ------------------------------------------------------------------

    def add_item(
        self, cart_id: str, product_id: str, quantity: int,
        current_user: CurrentUser
    ) -> CartItem:
        """Add a product to the cart.

        If the product already exists in the cart, its quantity is
        incremented rather than creating a duplicate line item.

        Args:
            cart_id: The cart identifier.
            product_id: The product identifier.
            quantity: The quantity to add (must be positive).
            current_user: The authenticated user.

        Returns:
            The CartItem object (existing or newly created).

        Raises:
            CartNotFoundError: If the cart does not exist.
            CartOwnershipError: If the cart belongs to another user.
            ProductNotFoundError: If the product does not exist.
            ProductInactiveError: If the product is not active.
            InsufficientStockError: If requested quantity exceeds stock.
        """
        cart = self._get_locked_cart(cart_id, current_user)

        product = self.db.query(Product).filter(
            Product.product_id == product_id
        ).first()
        if product is None:
            raise ProductNotFoundError(product_id)

        if not product.is_active:
            raise ProductInactiveError(product_id)

        if product.stock < quantity:
            raise InsufficientStockError(
                product_id, quantity, product.stock
            )

        existing_item = self.item_repo.get_by_cart_and_product(
            cart_id, product_id
        )
        if existing_item is not None:
            new_quantity = existing_item.quantity + quantity
            if product.stock < new_quantity:
                raise InsufficientStockError(
                    product_id, new_quantity, product.stock
                )
            existing_item.quantity = new_quantity
            self.item_repo.add(existing_item)
            try:
                self.item_repo.commit()
            except IntegrityError:
                self.item_repo.rollback()
                raise CartError("Failed to add item to cart")
            self.item_repo.refresh(existing_item)
            return existing_item

        item = CartItem(
            cart_id=cart_id,
            product_id=product_id,
            quantity=quantity,
            price_at_time=float(product.price),
        )
        self.item_repo.add(item)
        try:
            self.item_repo.commit()
        except IntegrityError:
            self.item_repo.rollback()
            raise CartError("Failed to add item to cart")
        self.item_repo.refresh(item)
        return item

    def update_item(
        self, cart_id: str, item_id: str, quantity: int,
        current_user: CurrentUser
    ) -> CartItem:
        """Update the quantity of an item in the cart.

        Only the cart owner can update it. The price snapshot is
        preserved and not refreshed from the current product price.

        Args:
            cart_id: The cart identifier.
            item_id: The unique cart item identifier.
            quantity: The new quantity (must be positive).
            current_user: The authenticated user.

        Returns:
            The CartItem object.

        Raises:
            CartNotFoundError: If the cart does not exist.
            CartOwnershipError: If the cart belongs to another user.
            CartItemNotFoundError: If the item does not exist.
            ProductNotFoundError: If the product does not exist.
            ProductInactiveError: If the product is not active.
            InsufficientStockError: If requested quantity exceeds stock.
        """
        cart = self._get_locked_cart(cart_id, current_user)

        item = None
        for i in cart.items:
            if str(i.cart_item_id) == item_id:
                item = i
                break

        if item is None:
            raise CartItemNotFoundError(item_id)

        product = self.db.query(Product).filter(
            Product.product_id == item.product_id
        ).first()
        if product is None:
            raise ProductNotFoundError(item.product_id)

        if not product.is_active:
            raise ProductInactiveError(item.product_id)

        if product.stock < quantity:
            raise InsufficientStockError(
                item.product_id, quantity, product.stock
            )

        item.quantity = quantity
        self.item_repo.add(item)
        try:
            self.item_repo.commit()
        except IntegrityError:
            self.item_repo.rollback()
            raise CartError("Failed to update item")
        self.item_repo.refresh(item)
        return item

    def remove_item(
        self, cart_id: str, item_id: str,
        current_user: CurrentUser
    ) -> CartItem:
        """Remove an item from the cart.

        Only the cart owner can remove it. Returns 404 if the item does
        not exist or does not belong to the specified cart.

        Args:
            cart_id: The cart identifier.
            item_id: The unique cart item identifier.
            current_user: The authenticated user.

        Returns:
            The CartItem object.

        Raises:
            CartNotFoundError: If the cart does not exist.
            CartOwnershipError: If the cart belongs to another user.
            CartItemNotFoundError: If the item does not exist.
        """
        cart = self._get_locked_cart(cart_id, current_user)

        item = None
        for i in cart.items:
            if str(i.cart_item_id) == item_id:
                item = i
                break

        if item is None:
            raise CartItemNotFoundError(item_id)

        self.item_repo.delete(item)
        try:
            self.item_repo.commit()
        except IntegrityError:
            self.item_repo.rollback()
            raise CartError("Failed to remove item from cart")
        return item
