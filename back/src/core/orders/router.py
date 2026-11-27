"""Orders HTTP router and exception mapping for Plataforma de Comercio.

Provides order management endpoints for authenticated buyers and
administrators. This router is intentionally thin: it handles HTTP
concerns only (routing, request/response serialization, HTTP status
codes, and exception translation). All business logic lives in
``src.core.orders.services.OrderService`` and all database access lives
in ``src.core.orders.repositories``.
"""

import json
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    Header,
    HTTPException,
    Query,
    Response,
    status,
)
from fastapi.responses import JSONResponse

from src.core.auth.dependencies import get_current_user
from src.core.cart.exceptions import CartNotFoundError, CartOwnershipError
from src.core.database import get_db
from src.core.security.schemas import CurrentUser
from src.core.orders.schemas import (
    OrderCreateRequest,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
    OrderSubitemResponse,
    OrderSummaryResponse,
)
from src.core.orders.services import OrderService
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

router = APIRouter(prefix="/orders", tags=["orders"])


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
    if not isinstance(exc, OrderError) and not isinstance(exc, CartNotFoundError) and not isinstance(exc, CartOwnershipError):
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
    if isinstance(exc, CartNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    if isinstance(exc, CartOwnershipError):
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


def _validate_uuid(order_id: str) -> None:
    """Validate that a string is a valid UUID.

    Raises:
        HTTPException: 404 NOT FOUND if the string is not a valid UUID,
            to avoid information disclosure about UUID format.
    """
    try:
        UUID(order_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )


@router.post(
    "/",
    summary="Create an order from a cart",
    description="Create an order from the authenticated user's cart. "
    "The idempotency key is supplied via the Idempotency-Key header. "
    "Returns HTTP 201 for a newly created order, HTTP 200 for a "
    "compatible idempotent retry.",
)
def create_order(
    cart_id: UUID = Body(...),
    idempotency_key: Optional[str] = Header(
        None, alias="Idempotency-Key"
    ),
    db=Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> JSONResponse:
    """Create an order from a cart.

    Converts the authenticated user's cart into an order. All monetary
    values, seller assignments, and statuses are derived server-side
    from trusted database records. The client supplies only the cart_id;
    the idempotency key is received via the HTTP Idempotency-Key header.

    On first successful creation, returns HTTP 201. On a compatible
    idempotent retry, returns the existing order with HTTP 200.

    Args:
        cart_id: Cart identifier to convert into an order.
        idempotency_key: Optional client idempotency key from header.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        OrderResponse: The created or existing order.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 400 if idempotency key is invalid.
        HTTPException: 404 if cart not found or not owned by user.
        HTTPException: 409 if insufficient stock or idempotency conflict.
        HTTPException: 500 if database error occurs.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    service = OrderService(db)
    try:
        result = service.create_order_from_cart(
            str(cart_id), current_user, idempotency_key
        )
    except (OrderError, CartNotFoundError, CartOwnershipError) as exc:
        raise _handle_service_error(exc)
    order_response = OrderResponse.model_validate(result.order)
    response = Response()
    response.status_code = (
        status.HTTP_201_CREATED if result.is_new else status.HTTP_200_OK
    )
    return JSONResponse(
        content=json.loads(order_response.model_dump_json()),
        status_code=response.status_code,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get an order by ID",
    description="Retrieve an order by its unique identifier. "
    "Only the order owner or an administrator can retrieve it.",
)
def get_order(
    order_id: str,
    db=Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> OrderResponse:
    """Retrieve an order by its unique identifier.

    Only the authenticated user who owns the order, or an
    administrator, can retrieve it. Returns 404 if the order does not
    exist or does not belong to the authenticated user, avoiding
    information disclosure.

    Args:
        order_id: The unique order identifier.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        OrderResponse: The requested order with items and subitems.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 404 if order not found or not owned by user.
        HTTPException: 500 if database error occurs.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _validate_uuid(order_id)
    service = OrderService(db)
    try:
        order = service.get_order_by_id(order_id, current_user)
    except OrderError as exc:
        raise _handle_service_error(exc)
    return OrderResponse.model_validate(order)


@router.get(
    "/",
    response_model=OrderListResponse,
    status_code=status.HTTP_200_OK,
    summary="List the authenticated user's orders",
    description="Retrieve a paginated list of orders belonging to the "
    "authenticated user.",
)
def list_orders(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        20, ge=1, le=100, description="Maximum number of records to return"
    ),
    db=Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> OrderListResponse:
    """List orders belonging to the authenticated user.

    Returns a paginated list of order summaries. Results are scoped to
    the authenticated user's ID.

    Args:
        skip: Number of records to skip (pagination).
        limit: Maximum number of records to return.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        OrderListResponse: Paginated list of order summaries.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 400 if skip or limit are invalid.
        HTTPException: 500 if database error occurs.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    service = OrderService(db)
    try:
        orders, total = service.list_orders_by_user(
            current_user, skip=skip, limit=limit
        )
    except OrderError as exc:
        raise _handle_service_error(exc)
    return OrderListResponse(
        orders=[
            OrderSummaryResponse.model_validate(order) for order in orders
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{order_id}/items",
    response_model=list[OrderItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get an order's line items",
    description="Retrieve all line items for an order. "
    "Only the order owner or an administrator can access them.",
)
def get_order_items(
    order_id: str,
    db=Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[OrderItemResponse]:
    """Retrieve all order items for an order.

    First verifies the caller can access the parent order. Buyers and
    administrators may retrieve all items.

    Args:
        order_id: The parent order identifier.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        List[OrderItemResponse]: The order's line items.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 404 if order not found or not owned by user.
        HTTPException: 500 if database error occurs.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _validate_uuid(order_id)
    service = OrderService(db)
    try:
        items = service.get_order_items(order_id, current_user)
    except OrderError as exc:
        raise _handle_service_error(exc)
    return [OrderItemResponse.model_validate(item) for item in items]


@router.get(
    "/{order_id}/subitems",
    response_model=list[OrderSubitemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get an order's seller subitems",
    description="Retrieve all seller subitems for an order. "
    "Only the order owner or an administrator can access them.",
)
def get_order_subitems(
    order_id: str,
    db=Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[OrderSubitemResponse]:
    """Retrieve all order subitems for an order.

    First verifies the caller can access the parent order. Buyers and
    administrators may retrieve all subitems.

    Args:
        order_id: The parent order identifier.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        List[OrderSubitemResponse]: The order's seller subitems.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 404 if order not found or not owned by user.
        HTTPException: 500 if database error occurs.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _validate_uuid(order_id)
    service = OrderService(db)
    try:
        subitems = service.get_order_subitems(order_id, current_user)
    except OrderError as exc:
        raise _handle_service_error(exc)
    return [
        OrderSubitemResponse.model_validate(subitem)
        for subitem in subitems
    ]

