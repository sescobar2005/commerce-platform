"""Orders HTTP exception mapping for Plataforma de Comercio.

Translates Orders domain exceptions into FastAPI HTTP exceptions.
This module is intentionally thin: it handles HTTP concerns only
(status codes, detail messages). All business logic lives in
``src.core.orders.services.OrderService`` and all database access lives
in ``src.core.orders.repositories``.

The mapping function is designed to be imported and reused by the
future Orders router. No route definitions live here yet.
"""

from fastapi import HTTPException, status

from src.core.orders.exceptions import (
    IdempotencyConflictError,
    InsufficientStockError,
    OrderError,
    OrderItemNotFoundError,
    OrderNotFoundError,
    OrderOwnershipError,
    ProductInactiveError,
    ProductNotFoundError,
)


def _handle_service_error(exc: OrderError) -> HTTPException:
    """Translate Orders domain exceptions into HTTP exceptions.

    Not-found and ownership failures return 404 with generic messages
    to avoid revealing whether an order exists or who owns it.

    Only OrderError subclasses are handled. Any other exception type
    is re-raised unchanged so it is not silently converted into a
    misleading client error.

    Args:
        exc: An Orders domain exception (subclass of OrderError).

    Returns:
        An HTTPException with the appropriate status code and detail.

    Raises:
        The original exception if it is not an OrderError subclass.
    """
    if not isinstance(exc, OrderError):
        raise exc
    if isinstance(exc, OrderNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    if isinstance(exc, OrderOwnershipError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    if isinstance(exc, OrderItemNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order item not found",
        )
    if isinstance(exc, ProductNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    if isinstance(exc, ProductInactiveError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    if isinstance(exc, InsufficientStockError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Insufficient stock",
        )
    if isinstance(exc, IdempotencyConflictError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency conflict",
        )
    # Fallback for unexpected OrderError (validation, business rule, etc.)
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Order operation failed",
    )
