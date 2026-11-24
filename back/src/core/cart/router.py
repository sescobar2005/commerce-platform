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
from src.core.cart.schemas import (
    CartItemAddRequest,
    CartItemResponse,
    CartItemUpdateRequest,
    CartResponse,
    CartUpdateRequest,
)

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


@router.put(
    "/{cart_id}",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a cart",
    description="Update a cart's expiration time. "
    "Only the cart owner can update it. "
    "Ownership and timestamps are not editable.",
)
def update_cart(
    cart_id: str,
    request: CartUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> CartResponse:
    """Update a cart's expiration time.

    Only the expires_at field can be updated. Ownership and internal
    timestamps are not editable.

    Args:
        cart_id: The unique cart identifier.
        request: Cart update request (expires_at).
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        CartResponse: The updated cart.

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

    # Verify cart exists and belongs to user
    cart = (
        db.query(Cart)
        .filter(Cart.cart_id == cart_id)
        .first()
    )
    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    if str(cart.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    # Update editable fields only
    cart.expires_at = request.expires_at

    try:
        db.add(cart)
        db.commit()
        db.refresh(cart)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to update cart",
        )

    # Reload cart with items for response
    cart = (
        db.query(Cart)
        .options(
            joinedload(Cart.items).joinedload(CartItem.product)
        )
        .filter(Cart.cart_id == cart_id)
        .first()
    )

    return _cart_to_response(cart)


@router.delete(
    "/{cart_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a cart",
    description="Delete a cart and all its items. "
    "Only the cart owner can delete it.",
)
def delete_cart(
    cart_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Delete a cart and all its items.

    Only the cart owner can delete it. Cart items are cascade-deleted
    via the relationship cascade rule.

    Args:
        cart_id: The unique cart identifier.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        dict: A status message confirming the cart was deleted.

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

    # Verify cart exists and belongs to user
    cart = (
        db.query(Cart)
        .filter(Cart.cart_id == cart_id)
        .first()
    )
    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    if str(cart.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    try:
        db.delete(cart)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to delete cart",
        )

    return {
        "message": "Cart deleted",
        "cart_id": cart_id,
    }


@router.post(
    "/{cart_id}/items",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an item to a cart",
    description="Add a product to the authenticated user's cart. "
    "If the product already exists in the cart, its quantity is incremented.",
)
def add_item_to_cart(
    cart_id: str,
    request: CartItemAddRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> CartResponse:
    """Add a product to the authenticated user's cart.

    Verifies that the cart belongs to the authenticated user, the
    product exists and is active, and there is sufficient stock.
    If the product already exists in the cart, its quantity is
    incremented rather than creating a duplicate item.

    Args:
        cart_id: The unique cart identifier.
        request: Cart item add request (product ID and quantity).
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        CartResponse: The updated cart with items.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 404 if cart not found, not owned by user,
            or product not found.
        HTTPException: 409 if insufficient stock.
        HTTPException: 500 if database error occurs.
    """
    # Require authentication
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify cart exists and belongs to user
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

    if str(cart.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    # Verify product exists and is active
    product = (
        db.query(Product)
        .filter(Product.product_id == request.product_id)
        .first()
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Validate stock availability
    if product.stock < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Insufficient stock",
        )

    # Check if product already exists in cart
    existing_item = None
    for item in cart.items:
        if str(item.product_id) == request.product_id:
            existing_item = item
            break

    if existing_item is not None:
        # Increment quantity
        new_quantity = existing_item.quantity + request.quantity
        if product.stock < new_quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Insufficient stock",
            )
        existing_item.quantity = new_quantity
    else:
        # Create new cart item with price snapshot from product
        item = CartItem(
            cart_id=cart_id,
            product_id=request.product_id,
            quantity=request.quantity,
            price_at_time=float(product.price),
        )
        db.add(item)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to add item to cart",
        )

    # Reload cart with items for response
    cart = (
        db.query(Cart)
        .options(
            joinedload(Cart.items).joinedload(CartItem.product)
        )
        .filter(Cart.cart_id == cart_id)
        .first()
    )

    return _cart_to_response(cart)


@router.put(
    "/{cart_id}/items/{item_id}",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a cart item quantity",
    description="Update the quantity of an item in the cart. "
    "Only the cart owner can update it.",
)
def update_cart_item(
    cart_id: str,
    item_id: str,
    request: CartItemUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> CartResponse:
    """Update the quantity of an item in the cart.

    Only the cart owner can update it. The price snapshot is preserved
    and is not refreshed from the current product price.

    Args:
        cart_id: The unique cart identifier.
        item_id: The unique cart item identifier.
        request: Cart item update request (new quantity).
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        CartResponse: The updated cart with items.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 404 if cart or item not found, or not owned by user.
        HTTPException: 409 if insufficient stock.
        HTTPException: 500 if database error occurs.
    """
    # Require authentication
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify cart exists and belongs to user
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

    if str(cart.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    # Find the item in the cart
    item = None
    for i in cart.items:
        if str(i.cart_item_id) == item_id:
            item = i
            break

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    # Verify product exists and is active
    product = (
        db.query(Product)
        .filter(Product.product_id == item.product_id)
        .first()
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Validate stock availability
    if product.stock < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Insufficient stock",
        )

    # Update quantity (price snapshot preserved)
    item.quantity = request.quantity

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to update cart item",
        )

    # Reload cart with items for response
    cart = (
        db.query(Cart)
        .options(
            joinedload(Cart.items).joinedload(CartItem.product)
        )
        .filter(Cart.cart_id == cart_id)
        .first()
    )

    return _cart_to_response(cart)


@router.delete(
    "/{cart_id}/items/{item_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove an item from a cart",
    description="Remove an item from the cart. "
    "Only the cart owner can remove it.",
)
def remove_item_from_cart(
    cart_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Remove an item from the cart.

    Only the cart owner can remove it. Returns 404 if the item does
    not exist or does not belong to the specified cart.

    Args:
        cart_id: The unique cart identifier.
        item_id: The unique cart item identifier.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        dict: A status message confirming the item was removed.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 404 if cart or item not found, or not owned by user.
        HTTPException: 500 if database error occurs.
    """
    # Require authentication
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify cart exists and belongs to user
    cart = (
        db.query(Cart)
        .filter(Cart.cart_id == cart_id)
        .first()
    )
    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    if str(cart.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    # Find and remove the item
    item = None
    for i in cart.items:
        if str(i.cart_item_id) == item_id:
            item = i
            break

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    try:
        db.delete(item)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to remove item from cart",
        )

    return {
        "message": "Item removed from cart",
        "cart_id": cart_id,
        "item_id": item_id,
    }


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
