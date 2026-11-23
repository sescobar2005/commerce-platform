"""Product router for Plataforma de Comercio.

Provides product creation endpoint for authenticated sellers.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.auth.dependencies import get_current_user
from src.core.database import get_db
from src.core.models.category import Category
from src.core.models.product import Product
from src.core.models.seller import Seller
from src.core.models.store import Store
from src.core.security.schemas import UserResponse
from src.core.products.schemas import (
    ProductCreateRequest,
    ProductResponse,
    ProductUpdateRequest,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
    description="Create a new product in a store owned by the authenticated seller.",
)
def create_product(
    request: ProductCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> ProductResponse:
    """Create a new product in the authenticated seller's store.

    The authenticated user must have a seller profile and must own
    the target store. The category must exist.

    Args:
        request: Product creation request.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        ProductResponse: The created product.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 403 if user has no seller profile or
            does not own the store.
        HTTPException: 404 if store or category not found.
        HTTPException: 409 if SKU already exists.
        HTTPException: 500 if database error occurs.
    """
    # Verify the user has a seller profile
    seller = db.query(Seller).filter(Seller.seller_id == current_user.user_id).first()
    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have a seller profile",
        )

    # Verify the store exists
    store = db.query(Store).filter(Store.store_id == request.store_id).first()
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found",
        )

    # Verify the authenticated seller owns this store
    if str(store.seller_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Store does not belong to the authenticated seller",
        )

    # Verify the category exists
    category = (
        db.query(Category).filter(Category.category_id == request.category_id).first()
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Create the product
    product = Product(
        store_id=request.store_id,
        category_id=request.category_id,
        name=request.name,
        description=request.description,
        price=request.price,
        cost=request.cost or 0.0,
        sku=request.sku,
        stock=request.stock or 0,
        images_urls=request.images_urls,
        is_active=True,
    )

    try:
        db.add(product)
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product SKU already exists",
        )

    return ProductResponse(
        product_id=str(product.product_id),
        store_id=str(product.store_id),
        category_id=str(product.category_id),
        name=product.name,
        description=product.description,
        price=product.price,
        cost=product.cost,
        sku=product.sku,
        stock=product.stock,
        is_active=product.is_active,
        images_urls=product.images_urls,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a product by ID",
    description="Retrieve a product by its unique identifier.",
)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
) -> ProductResponse:
    """Retrieve a product by its unique identifier.

    Args:
        product_id: The unique product identifier.
        db: Database session dependency.

    Returns:
        ProductResponse: The requested product.

    Raises:
        HTTPException: 404 if the product does not exist.
    """
    product = (
        db.query(Product).filter(Product.product_id == product_id).first()
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return ProductResponse(
        product_id=str(product.product_id),
        store_id=str(product.store_id),
        category_id=str(product.category_id),
        name=product.name,
        description=product.description,
        price=product.price,
        cost=product.cost,
        sku=product.sku,
        stock=product.stock,
        is_active=product.is_active,
        images_urls=product.images_urls,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a product by ID",
    description="Update an existing product. Only the owning seller can update a product.",
)
def update_product(
    product_id: str,
    request: ProductUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> ProductResponse:
    """Update an existing product by its unique identifier.

    Only the seller who owns the store associated with the product
    can update it. Fields omitted from the request are preserved
    unchanged. The product cannot be moved to another store.

    Args:
        product_id: The unique product identifier.
        request: Product update request (partial fields allowed).
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        ProductResponse: The updated product.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 403 if user has no seller profile or
            does not own the product's store.
        HTTPException: 404 if the product does not exist.
        HTTPException: 409 if the new SKU already exists.
        HTTPException: 500 if database error occurs.
    """
    # Verify the user has a seller profile
    seller = db.query(Seller).filter(Seller.seller_id == current_user.user_id).first()
    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have a seller profile",
        )

    # Retrieve the product by ID
    product = (
        db.query(Product).filter(Product.product_id == product_id).first()
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Verify the store exists and the authenticated seller owns it
    store = db.query(Store).filter(Store.store_id == product.store_id).first()
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found",
        )

    # Verify the authenticated seller owns the product's store
    if str(store.seller_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Product does not belong to the authenticated seller",
        )

    # Prevent changing store_id (ownership cannot be transferred)
    if (
        getattr(request, "store_id", None) is not None
        and str(getattr(request, "store_id")) != str(product.store_id)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change the owning store of a product",
        )

    # Prevent changing category_id (reclassification not allowed via update)
    if (
        getattr(request, "category_id", None) is not None
        and str(getattr(request, "category_id")) != str(product.category_id)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change the category of a product via update",
        )

    # Apply updates for fields that are present in the request
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "store_id" or field == "category_id":
            continue  # ownership fields already validated above
        setattr(product, field, value)

    try:
        db.add(product)
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product SKU already exists",
        )

    return ProductResponse(
        product_id=str(product.product_id),
        store_id=str(product.store_id),
        category_id=str(product.category_id),
        name=product.name,
        description=product.description,
        price=product.price,
        cost=product.cost,
        sku=product.sku,
        stock=product.stock,
        is_active=product.is_active,
        images_urls=product.images_urls,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )
