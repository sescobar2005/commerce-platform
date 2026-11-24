"""Cart-specific application exceptions.

These exceptions are raised by the CartService and CartRepository layers
and translated into HTTP responses by the router layer. Keeping them
separate from HTTP-specific exceptions keeps business logic independent
of the transport layer.
"""


class CartError(Exception):
    """Base exception for all cart-related errors."""

    pass


class CartNotFoundError(CartError):
    """Raised when a cart with the given ID does not exist."""

    def __init__(self, cart_id: str):
        self.cart_id = cart_id
        super().__init__(f"Cart not found: {cart_id}")


class CartItemNotFoundError(CartError):
    """Raised when a cart item with the given ID does not exist."""

    def __init__(self, item_id: str):
        self.item_id = item_id
        super().__init__(f"Cart item not found: {item_id}")


class ProductNotFoundError(CartError):
    """Raised when a product with the given ID does not exist."""

    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Product not found: {product_id}")


class ProductInactiveError(CartError):
    """Raised when a product exists but is not active."""

    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Product not available: {product_id}")


class InsufficientStockError(CartError):
    """Raised when requested quantity exceeds available stock."""

    def __init__(self, product_id: str, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for product {product_id}: "
            f"requested {requested}, available {available}"
        )


class CartOwnershipError(CartError):
    """Raised when a user attempts to access a cart they do not own."""

    def __init__(self, cart_id: str, user_id: str):
        self.cart_id = cart_id
        self.user_id = user_id
        super().__init__(
            f"Cart {cart_id} does not belong to user {user_id}"
        )
