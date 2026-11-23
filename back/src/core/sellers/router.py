"""Seller router for Plataforma de Comercio.

Provides seller registration endpoint.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.auth.dependencies import get_current_user
from src.core.database import get_db
from src.core.models.seller import Seller
from src.core.models.store import Store
from src.core.models.user import User
from src.core.security.schemas import CurrentUser
from src.core.sellers.schemas import (
    SellerRegisterRequest,
    SellerResponse,
    StoreCreateRequest,
    StoreResponse,
)

router = APIRouter(prefix="/sellers", tags=["sellers"])


@router.post(
    "/register",
    response_model=SellerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register as a seller",
    description="Register a new seller profile associated with the authenticated user.",
)
def register_seller(
    request: SellerRegisterRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> SellerResponse:
    """Register as a new seller.

    Creates a seller profile associated with the authenticated user.
    A user can only have one seller profile (1:1 relationship).

    Args:
        request: Seller registration request.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        SellerResponse: The created seller profile.

    Raises:
        HTTPException: 409 if user already has a seller profile.
        HTTPException: 500 if database error occurs.
    """
    # Check if user already has a seller profile
    existing_seller = (
        db.query(Seller).filter(Seller.seller_id == current_user.user_id).first()
    )
    if existing_seller:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has a seller profile",
        )

    # Create seller profile
    seller = Seller(
        seller_id=current_user.user_id,
        store_name=request.store_name,
        business_name=request.business_name,
        tax_id=request.tax_id,
        payment_info_json=request.payment_info_json,
        bank_account=request.bank_account,
        is_verified=False,
    )

    try:
        db.add(seller)
        db.commit()
        db.refresh(seller)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seller profile already exists",
        )

    return SellerResponse(
        seller_id=str(seller.seller_id),
        store_name=seller.store_name,
        business_name=seller.business_name,
        tax_id=seller.tax_id,
        payment_info_json=seller.payment_info_json,
        bank_account=seller.bank_account,
        is_verified=seller.is_verified,
        created_at=seller.created_at,
    )


@router.post(
    "/{seller_id}/stores",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a store",
    description="Create a new store for the authenticated seller.",
)
def create_store(
    seller_id: str,
    request: StoreCreateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> StoreResponse:
    """Create a new store for the authenticated seller.

    Creates a store associated with the authenticated seller.
    A seller can only create stores for themselves.

    Args:
        seller_id: The seller ID.
        request: Store creation request.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        StoreResponse: The created store profile.

    Raises:
        HTTPException: 404 if seller not found.
        HTTPException: 403 if seller belongs to another user.
        HTTPException: 409 if store slug already exists.
        HTTPException: 500 if database error occurs.
    """
    # Verify the seller exists
    seller = db.query(Seller).filter(Seller.seller_id == seller_id).first()
    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found",
        )

    # Verify the authenticated user owns this seller
    if str(seller.seller_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Store does not belong to the authenticated seller",
        )

    # Check if slug already exists
    existing_store = (
        db.query(Store).filter(Store.slug == request.slug).first()
    )
    if existing_store:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Store slug already exists",
        )

    # Create store
    store = Store(
        seller_id=seller_id,
        name=request.name,
        description=request.description,
        slug=request.slug,
        logo_url=request.logo_url,
        cover_image_url=request.cover_image_url,
        is_active=True,
    )

    try:
        db.add(store)
        db.commit()
        db.refresh(store)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Store slug already exists",
        )

    return StoreResponse(
        store_id=str(store.store_id),
        seller_id=str(store.seller_id),
        name=store.name,
        description=store.description,
        slug=store.slug,
        logo_url=store.logo_url,
        cover_image_url=store.cover_image_url,
        is_active=store.is_active,
        created_at=store.created_at,
        updated_at=store.updated_at,
    )


@router.get(
    "/{seller_id}",
    response_model=SellerResponse,
    status_code=status.HTTP_200_OK,
    summary="Get seller profile",
    description="Get a seller profile by seller ID.",
)
def get_seller(
    seller_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> SellerResponse:
    """Get a seller profile by seller ID.

    Retrieves the public profile of a seller.

    Args:
        seller_id: The seller ID.
        db: Database session dependency.
        current_user: Authenticated user from JWT token.

    Returns:
        SellerResponse: The seller profile.

    Raises:
        HTTPException: 404 if seller not found.
        HTTPException: 403 if seller does not belong to the authenticated user.
    """
    # Verify the seller exists
    seller = db.query(Seller).filter(Seller.seller_id == seller_id).first()
    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found",
        )

    # Verify the authenticated user owns this seller
    if str(seller.seller_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller does not belong to the authenticated user",
        )

    return SellerResponse(
        seller_id=str(seller.seller_id),
        store_name=seller.store_name,
        business_name=seller.business_name,
        tax_id=seller.tax_id,
        payment_info_json=seller.payment_info_json,
        bank_account=seller.bank_account,
        is_verified=seller.is_verified,
        created_at=seller.created_at,
    )
