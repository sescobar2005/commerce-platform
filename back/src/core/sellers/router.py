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
from src.core.models.user import User
from src.core.security.schemas import UserResponse
from src.core.sellers.schemas import SellerRegisterRequest, SellerResponse

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
    current_user: UserResponse = Depends(get_current_user),
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
