"""Orders-specific application exceptions.

These exceptions are raised by the OrderService and Orders repository
layers and translated into HTTP responses by the router layer. Keeping
them separate from HTTP-specific exceptions keeps business logic
independent of the transport layer.

Cart exceptions are NOT reused here: Orders-specific business errors
live in this module.
"""


class OrderError(Exception):
    """Base exception for all order-related errors."""

    pass


class OrderNotFoundError(OrderError):
    """Raised when an order with the given ID does not exist."""

    def __init__(self, order_id: str):
        self.order_id = order_id
        super().__init__(f"Order not found: {order_id}")


class OrderOwnershipError(OrderError):
    """Raised when a user attempts to access an order they do not own."""

    def __init__(self, order_id: str, user_id: str):
        self.order_id = order_id
        self.user_id = user_id
        super().__init__(
            f"Order {order_id} does not belong to user {user_id}"
        )


class OrderItemNotFoundError(OrderError):
    """Raised when an order item with the given ID does not exist."""

    def __init__(self, order_item_id: str):
        self.order_item_id = order_item_id
        super().__init__(f"Order item not found: {order_item_id}")


class ProductNotFoundError(OrderError):
    """Raised when a product with the given ID does not exist."""

    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Product not found: {product_id}")


class ProductInactiveError(OrderError):
    """Raised when a product exists but is not active."""

    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Product not available: {product_id}")


class InsufficientStockError(OrderError):
    """Raised when requested quantity exceeds available stock."""

    def __init__(self, product_id: str, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for product {product_id}: "
            f"requested {requested}, available {available}"
        )


class IdempotencyConflictError(OrderError):
    """Raised when an idempotency key is reused with a conflicting request.

    Distinguishable from other Order errors so the router layer can map
    it to HTTP 409 CONFLICT.
    """

    def __init__(self, message: str):
        super().__init__(message)
