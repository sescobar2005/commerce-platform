"""Product router for Plataforma de Comercio.

Provides product management endpoints for authenticated sellers.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import asc, desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from src.core.auth.dependencies import get_current_user
from src.core.database import get_db
from src.core.models.category import Category
from src.core.models.product import Product
from src.core.models.seller import Seller
from src.core.models.store import Store
from src.core.security.schemas import CurrentUser
from src.core.products.schemas import (
    ProductCreateRequest,
    ProductListResponse,
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
    current_user: CurrentUser = Depends(get_current_user),
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
    "/",
    response_model=ProductListResponse,
    status_code=status.HTTP_200_OK,
    summary="List products with filters",
    description="Retrieve a paginated list of products with optional search, filters, and sorting.",
)
def list_products(
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    store_id: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_active: Optional[bool] = True,
    sort: Optional[str] = "newest",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
) -> ProductListResponse:
    """Retrieve a paginated list of products.

    Supports search by name, category/store filtering, price range
    filtering, active status filtering, sorting, and pagination.

    Args:
        search: Optional name search term (case-insensitive).
        category_id: Optional category filter.
        store_id: Optional store filter.
        min_price: Optional minimum price.
        max_price: Optional maximum price.
        is_active: Optional active status filter (defaults to True).
        sort: Optional sort order (price_asc, price_desc, newest, oldest).
        page: Page number (default 1).
        page_size: Items per page (default 20, max 100).
        db: Database session dependency.

    Returns:
        ProductListResponse: Paginated product list with metadata.

    Raises:
        HTTPException: 400 if min_price > max_price, page < 1,
            page_size > 100, or invalid sort.
        HTTPException: 500 if database error occurs.
    """
    # Validate pagination
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="page must be at least 1",
        )
    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="page_size must be between 1 and 100",
        )

    # Validate price range
    if min_price is not None and min_price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price must be non-negative",
        )
    if max_price is not None and max_price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_price must be non-negative",
        )
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price cannot be greater than max_price",
        )

    # Validate sort order
    allowed_sorts = {"price_asc", "price_desc", "newest", "oldest"}
    if sort not in allowed_sorts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort '{sort}'. Allowed: {', '.join(sorted(allowed_sorts))}",
        )

    # Build base query with eager loading to avoid N+1
    query = db.query(Product).options(
        joinedload(Product.store),
        joinedload(Product.category),
    )

    # Default to active products only
    query = query.filter(Product.is_active == True)  # noqa: E712

    # Apply search filter (case-insensitive)
    if search:
        query = query.filter(
            func.lower(Product.name).contains(func.lower(search))
        )

    # Apply category filter
    if category_id:
        query = query.filter(Product.category_id == category_id)

    # Apply store filter
    if store_id:
        query = query.filter(Product.store_id == store_id)

    # Apply price range filters
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    if sort == "price_asc":
        query = query.order_by(asc(Product.price))
    elif sort == "price_desc":
        query = query.order_by(desc(Product.price))
    elif sort == "newest":
        query = query.order_by(desc(Product.created_at))
    elif sort == "oldest":
        query = query.order_by(asc(Product.created_at))

    # Apply pagination
    offset = (page - 1) * page_size
    products = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return ProductListResponse(
        items=[
            ProductResponse(
                product_id=str(p.product_id),
                store_id=str(p.store_id),
                category_id=str(p.category_id),
                name=p.name,
                description=p.description,
                price=p.price,
                cost=p.cost,
                sku=p.sku,
                stock=p.stock,
                is_active=p.is_active,
                images_urls=p.images_urls,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in products
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
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
    current_user: CurrentUser = Depends(get_current_user),
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


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a product by ID",
    description="Soft-delete a product by setting is_active to False. Only the owning seller can delete a product.",
)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Soft-delete a product by setting is_active to False.

    Only the seller who owns the store associated with the product
    can delete it. The product record is preserved (soft deletion)
    to maintain referential integrity with any related records.

    Args:
        product_id: The unique product identifier.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        dict: A status message confirming the product was deactivated.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 403 if user has no seller profile or
            does not own the product's store.
        HTTPException: 404 if the product does not exist.
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

    # Soft-delete: set is_active to False
    product.is_active = False

    try:
        db.add(product)
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to deactivate product",
        )

    return {
        "message": "Product deactivated successfully",
        "product_id": str(product.product_id),
        "is_active": product.is_active,
    }
