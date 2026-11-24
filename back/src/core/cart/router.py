"""Cart router for Plataforma de Comercio.

Provides cart management endpoints for authenticated users.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from src.core.auth.dependencies import get_current_user
from src.core.database import get_db
from src.core.models.cart import Cart, CartItem
from src.core.models.product import Product
from src.core.security.schemas import CurrentUser
from src.core.cart.schemas import CartItemResponse, CartResponse

router = APIRouter(prefix="/carts", tags=["carts"])


@router.post(
    "/",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a cart",
    description="Create a new cart for the authenticated user. "
    "If the user already has an active cart, returns the existing cart.",
)
def create_cart(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> CartResponse:
    """Create a new cart for the authenticated user.

    If the user already has an existing cart, returns it instead of
    creating a duplicate. This enforces the business rule that a user
    may have at most one active cart at the application level.

    Note: The current schema does not enforce a database-level unique
    constraint on user_id for active carts, so concurrent requests
    could theoretically create multiple carts. The application-level
    check mitigates this but does not eliminate the race condition.

    Args:
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        CartResponse: The cart (existing or newly created).

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 500 if database error occurs.
    """
    # Require authentication
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user already has a cart
    existing_cart = (
        db.query(Cart)
        .filter(Cart.user_id == current_user.user_id)
        .first()
    )
    if existing_cart:
        # Eager-load items with products for consistent response
        existing_cart = (
            db.query(Cart)
            .options(
                joinedload(Cart.items).joinedload(CartItem.product)
            )
            .filter(Cart.cart_id == existing_cart.cart_id)
            .first()
        )
        return _cart_to_response(existing_cart)

    # Create new cart
    cart = Cart(user_id=current_user.user_id)

    try:
        db.add(cart)
        db.commit()
        db.refresh(cart)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create cart",
        )

    # Eager-load items for response
    cart = (
        db.query(Cart)
        .options(
            joinedload(Cart.items).joinedload(CartItem.product)
        )
        .filter(Cart.cart_id == cart.cart_id)
        .first()
    )

    return _cart_to_response(cart)


@router.get(
    "/{cart_id}",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a cart by ID",
    description="Retrieve a cart by its unique identifier. "
    "Only the cart owner can retrieve it.",
)
def get_cart(
    cart_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> CartResponse:
    """Retrieve a cart by its unique identifier.

    Only the authenticated user who owns the cart can retrieve it.
    Returns 404 if the cart does not exist or does not belong to the
    authenticated user, avoiding information disclosure.

    Args:
        cart_id: The unique cart identifier.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        CartResponse: The requested cart with items.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 404 if cart not found or not owned by user.
        HTTPException: 500 if database error occurs.
    """
    # Require authentication
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    cart = (
        db.query(Cart)
        .options(
            joinedload(Cart.items).joinedload(CartItem.product)
        )
        .filter(Cart.cart_id == cart_id)
        .first()
    )

    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    # Verify ownership — return 404 (not 403) to avoid information disclosure
    if str(cart.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    return _cart_to_response(cart)


def _cart_to_response(cart: Cart) -> CartResponse:
    """Convert a Cart model instance to a CartResponse schema.

    Eager-loads items with their associated products to avoid
    N+1 query issues.

    Args:
        cart: Cart model instance.

    Returns:
        CartResponse: The serialized cart response.
    """
    items = [
        CartItemResponse(
            cart_item_id=str(item.cart_item_id),
            cart_id=str(item.cart_id),
            product_id=str(item.product_id),
            quantity=item.quantity,
            price_at_time=float(item.price_at_time),
            created_at=item.created_at,
        )
        for item in cart.items
    ]

    return CartResponse(
        cart_id=str(cart.cart_id),
        user_id=str(cart.user_id),
        items=items,
        created_at=cart.created_at,
        last_updated_at=cart.last_updated_at,
        expires_at=cart.expires_at,
    )
