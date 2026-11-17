"""Authentication router for Plataforma de Comercio.

Provides user registration endpoint and related authentication routes.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.models.user import User
from src.core.security.jwt import JWTService
from src.core.security.password import PasswordService
from src.core.security.schemas import (
    UserLoginRequest,
    UserLoginResponse,
    UserRegisterRequest,
    UserRegisterResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_password_service() -> PasswordService:
    """Dependency that provides a PasswordService instance."""
    return PasswordService()


def get_jwt_service() -> JWTService:
    """Dependency that provides a JWTService instance."""
    return JWTService()


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
        is_seller=False,
        is_verified=False,
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


@router.post(
    "/login",
    response_model=UserLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a user",
    description="Authenticate a user with username and password, returning access and refresh tokens.",
)
def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> UserLoginResponse:
    """Authenticate a user and issue access and refresh tokens.

    Args:
        request: User login request with username and password.
        db: Database session dependency.
        password_service: Password hashing service dependency.
        jwt_service: JWT token service dependency.

    Returns:
        UserLoginResponse: Access and refresh tokens plus public user data.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    # Find user by username
    user = db.query(User).filter(User.username == request.username).first()

    # Validate password - use consistent response for unknown user or wrong password
    # to prevent user enumeration
    if user is None or not password_service.verify_password(
        request.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Generate tokens
    access_token = jwt_service.create_access_token(
        user_id=str(user.user_id),
        username=user.username,
        role="seller" if user.is_seller else "user",
    )
    refresh_token = jwt_service.create_refresh_token(
        user_id=str(user.user_id),
    )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update login timestamp",
        )

    return UserLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse(
            user_id=str(user.user_id),
            username=user.username,
            email=user.email,
            is_seller=user.is_seller,
            is_verified=user.is_verified,
            created_at=user.created_at,
        ),
    )
