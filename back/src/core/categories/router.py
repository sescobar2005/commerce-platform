"""Category router for Plataforma de Comercio.

Provides category management endpoints for the product catalog.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import asc, desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from src.core.auth.dependencies import get_current_user
from src.core.database import get_db
from src.core.models.category import Category
from src.core.models.product import Product
from src.core.security.schemas import CurrentUser
from src.core.categories.schemas import (
    CategoryCreateRequest,
    CategoryListResponse,
    CategoryProductsListResponse,
    CategoryResponse,
    CategoryUpdateRequest,
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category",
    description="Create a new product category.",
)
def create_category(
    request: CategoryCreateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> CategoryResponse:
    """Create a new product category.

    Args:
        request: Category creation request.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        CategoryResponse: The created category.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 403 if user is not an administrator.
        HTTPException: 409 if category name or slug already exists.
        HTTPException: 500 if database error occurs.
    """
    # Require administrator privileges
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )

    # Check for duplicate name
    existing_name = (
        db.query(Category).filter(Category.name == request.name).first()
    )
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name already exists",
        )

    # Check for duplicate slug
    existing_slug = (
        db.query(Category).filter(Category.slug == request.slug).first()
    )
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category slug already exists",
        )

    # Validate parent_id if provided
    parent = None
    if request.parent_id:
        parent = (
            db.query(Category)
            .filter(Category.category_id == request.parent_id)
            .first()
        )
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found",
            )

    # Create the category
    category = Category(
        name=request.name,
        description=request.description,
        slug=request.slug,
        parent_id=request.parent_id,
        level=parent.level + 1 if parent else 0,
        path=parent.path + "/" + request.slug if parent else request.slug,
        is_active=True,
    )
    # Ensure server-only defaults are set for response serialization
    if category.created_at is None:
        category.created_at = datetime.now(timezone.utc)

    try:
        db.add(category)
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name or slug already exists",
        )

    return CategoryResponse(
        category_id=str(category.category_id),
        name=category.name,
        description=category.description,
        slug=category.slug,
        parent_id=str(category.parent_id) if category.parent_id else None,
        level=category.level,
        path=category.path,
        is_active=category.is_active,
        created_at=category.created_at,
    )


@router.get(
    "/",
    response_model=CategoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List categories with pagination",
    description="Retrieve a paginated list of categories.",
)
def list_categories(
    search: Optional[str] = None,
    is_active: Optional[bool] = True,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
) -> CategoryListResponse:
    """Retrieve a paginated list of categories.

    Supports search by name and active status filtering.

    Args:
        search: Optional name search term (case-insensitive).
        is_active: Optional active status filter (defaults to True).
        page: Page number (default 1).
        page_size: Items per page (default 20, max 100).
        db: Database session dependency.

    Returns:
        CategoryListResponse: Paginated category list with metadata.

    Raises:
        HTTPException: 400 if page < 1 or page_size > 100.
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

    # Build base query with eager loading to avoid N+1
    query = db.query(Category).options(
        joinedload(Category.children),
    )

    # Default to active categories only
    query = query.filter(Category.is_active == True)  # noqa: E712

    # Apply search filter (case-insensitive)
    if search:
        query = query.filter(
            func.lower(Category.name).contains(func.lower(search))
        )

    # Get total count before pagination
    total = query.count()

    # Apply sorting by level then name
    query = query.order_by(asc(Category.level), asc(Category.name))

    # Apply pagination
    offset = (page - 1) * page_size
    categories = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return CategoryListResponse(
        items=[
            CategoryResponse(
                category_id=str(c.category_id),
                name=c.name,
                description=c.description,
                slug=c.slug,
                parent_id=str(c.parent_id) if c.parent_id else None,
                level=c.level,
                path=c.path,
                is_active=c.is_active,
                created_at=c.created_at,
            )
            for c in categories
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a category by ID",
    description="Retrieve a category by its unique identifier.",
)
def get_category(
    category_id: str,
    db: Session = Depends(get_db),
) -> CategoryResponse:
    """Retrieve a category by its unique identifier.

    Args:
        category_id: The unique category identifier.
        db: Database session dependency.

    Returns:
        CategoryResponse: The requested category.

    Raises:
        HTTPException: 404 if the category does not exist.
    """
    category = (
        db.query(Category)
        .filter(Category.category_id == category_id)
        .first()
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return CategoryResponse(
        category_id=str(category.category_id),
        name=category.name,
        description=category.description,
        slug=category.slug,
        parent_id=str(category.parent_id) if category.parent_id else None,
        level=category.level,
        path=category.path,
        is_active=category.is_active,
        created_at=category.created_at,
    )


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a category by ID",
    description="Update an existing category.",
)
def update_category(
    category_id: str,
    request: CategoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> CategoryResponse:
    """Update an existing category by its unique identifier.

    Fields omitted from the request are preserved unchanged.
    The category hierarchy (parent_id) cannot be changed to create
    a cycle.

    Args:
        category_id: The unique category identifier.
        request: Category update request (partial fields allowed).
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        CategoryResponse: The updated category.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 403 if user is not an administrator.
        HTTPException: 404 if the category does not exist.
        HTTPException: 409 if the new name or slug already exists.
        HTTPException: 500 if database error occurs.
    """
    # Require administrator privileges
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )

    # Retrieve the category by ID
    category = (
        db.query(Category)
        .filter(Category.category_id == category_id)
        .first()
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Check for duplicate name if being changed
    if request.name is not None and request.name != category.name:
        existing_name = (
            db.query(Category)
            .filter(
                Category.name == request.name,
                Category.category_id != category_id,
            )
            .first()
        )
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category name already exists",
            )

    # Check for duplicate slug if being changed
    if request.slug is not None and request.slug != category.slug:
        existing_slug = (
            db.query(Category)
            .filter(
                Category.slug == request.slug,
                Category.category_id != category_id,
            )
            .first()
        )
        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category slug already exists",
            )

    # Validate parent_id if being changed
    if request.parent_id is not None:
        if request.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent",
            )
        parent = (
            db.query(Category)
            .filter(Category.category_id == request.parent_id)
            .first()
        )
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found",
            )

    # Apply updates for fields that are present in the request
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    # Recalculate level and path if parent_id changed
    if request.parent_id is not None:
        parent = (
            db.query(Category)
            .filter(Category.category_id == request.parent_id)
            .first()
        )
        category.level = parent.level + 1 if parent else 0
        category.path = (
            parent.path + "/" + category.slug
            if parent
            else category.slug
        )

    try:
        db.add(category)
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name or slug already exists",
        )

    return CategoryResponse(
        category_id=str(category.category_id),
        name=category.name,
        description=category.description,
        slug=category.slug,
        parent_id=str(category.parent_id) if category.parent_id else None,
        level=category.level,
        path=category.path,
        is_active=category.is_active,
        created_at=category.created_at,
    )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a category by ID",
    description="Soft-delete a category by setting is_active to False.",
)
def delete_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Soft-delete a category by setting is_active to False.

    The category record is preserved to maintain referential
    integrity with any related products.

    Args:
        category_id: The unique category identifier.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        dict: A status message confirming the category was deactivated.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 403 if user is not an administrator.
        HTTPException: 404 if the category does not exist.
        HTTPException: 500 if database error occurs.
    """
    # Require administrator privileges
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )

    # Retrieve the category by ID
    category = (
        db.query(Category)
        .filter(Category.category_id == category_id)
        .first()
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Soft-delete: set is_active to False
    category.is_active = False

    try:
        db.add(category)
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to deactivate category",
        )

    return {
        "message": "Category deactivated successfully",
        "category_id": str(category.category_id),
        "is_active": category.is_active,
    }


@router.get(
    "/{category_id}/products",
    status_code=status.HTTP_200_OK,
    summary="List products belonging to a category",
    description="Retrieve a paginated list of products within a category.",
)
def list_category_products(
    category_id: str,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve a paginated list of products within a category.

    Args:
        category_id: The unique category identifier.
        page: Page number (default 1).
        page_size: Items per page (default 20, max 100).
        db: Database session dependency.

    Returns:
        dict: Paginated product list with category metadata.

    Raises:
        HTTPException: 404 if the category does not exist.
        HTTPException: 400 if page < 1 or page_size > 100.
        HTTPException: 500 if database error occurs.
    """
    # Verify category exists
    category = (
        db.query(Category)
        .filter(Category.category_id == category_id)
        .first()
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

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

    # Build query for products in this category
    query = db.query(Product).filter(Product.category_id == category_id)

    # Get total count before pagination
    total = query.count()

    # Apply sorting by name
    query = query.order_by(asc(Product.name))

    # Apply pagination
    offset = (page - 1) * page_size
    products = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "category_id": str(category.category_id),
        "category_name": category.name,
        "items": [
            {
                "product_id": str(p.product_id),
                "store_id": str(p.store_id),
                "category_id": str(p.category_id),
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "cost": p.cost,
                "sku": p.sku,
                "stock": p.stock,
                "is_active": p.is_active,
                "images_urls": p.images_urls,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in products
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
