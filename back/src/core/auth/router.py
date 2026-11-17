"""Authentication router for Plataforma de Comercio.

Provides user registration endpoint and related authentication routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.models.user import User
from src.core.security.password import PasswordService
from src.core.security.schemas import UserRegisterRequest, UserRegisterResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def get_password_service() -> PasswordService:
    """Dependency that provides a PasswordService instance."""
    return PasswordService()


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Register a new user account with username, email, and password.",
)
def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> UserRegisterResponse:
    """Register a new user.

    Args:
        request: User registration request with username, email, and password.
        db: Database session dependency.
        password_service: Password hashing service dependency.

    Returns:
        UserRegisterResponse: The created user's public data.

    Raises:
        HTTPException: 409 if username or email already exists.
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == request.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Hash the password
    password_hash = password_service.hash_password(request.password)

    # Create the user ORM instance
    user = User(
        username=request.username,
        email=request.email,
        password_hash=password_hash,
    )

    # Persist to database
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    return UserRegisterResponse(
        user_id=str(user.user_id),
        username=user.username,
        email=user.email,
        is_seller=user.is_seller,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )
