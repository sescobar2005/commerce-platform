"""Authentication router for Plataforma de Comercio.

Provides user registration endpoint and related authentication routes.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
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
    TokenRefreshRequest,
    TokenResponse,
)
from src.core.security.token_revocation import TokenRevocationService

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


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Refresh an access token using a valid refresh token.",
)
def refresh(
    request: TokenRefreshRequest,
    db: Session = Depends(get_db),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> TokenResponse:
    """Refresh an access token using a valid refresh token.

    Args:
        request: Refresh token request.
        db: Database session dependency.
        jwt_service: JWT token service dependency.

    Returns:
        TokenResponse: New access token and refresh token.

    Raises:
        HTTPException: 401 if the refresh token is invalid, expired,
            revoked, or not a refresh token.
        HTTPException: 404 if the user associated with the token
            does not exist.
    """
    # Verify the refresh token
    try:
        payload = jwt_service.verify_refresh_token(request.refresh_token)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    jti = payload.get("jti")
    user_id = payload.get("sub")

    # Validate required claims
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token: missing jti claim",
        )
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token: missing subject claim",
        )

    # Check if token is revoked
    revocation_service = TokenRevocationService(db, jwt_service)
    if revocation_service.is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    # Verify user still exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Revoke the old refresh token (rotation)
    revocation_service.revoke_refresh_token(request.refresh_token)

    # Generate new access and refresh tokens
    new_access_token = jwt_service.create_access_token(
        user_id=str(user.user_id),
        username=user.username,
        role="seller" if user.is_seller else "user",
    )
    new_refresh_token = jwt_service.create_refresh_token(
        user_id=str(user.user_id),
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rotate refresh token",
        )

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Log out a user",
    description="Revoke the refresh token associated with the current session.",
)
def logout(
    request: TokenRefreshRequest,
    credentials: HTTPAuthorizationCredentials = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db),
    jwt_service: JWTService = Depends(get_jwt_service),
):
    """Log out a user by revoking their refresh token.

    Requires a valid access token. Revokes the refresh token provided
    in the request body, provided it belongs to the authenticated user.

    Args:
        request: Logout request with refresh token.
        credentials: Bearer token credentials from the Authorization header.
        db: Database session dependency.
        jwt_service: JWT token service dependency.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: 401 if access token is missing or invalid,
            or if refresh token is invalid/expired.
        HTTPException: 403 if refresh token belongs to another user.
    """
    # Verify the access token
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt_service.verify_access_token(token)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject claim",
        )

    # Verify user still exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Verify the refresh token
    try:
        refresh_payload = jwt_service.verify_refresh_token(request.refresh_token)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    token_user_id = refresh_payload.get("sub")

    # Verify the refresh token belongs to the authenticated user
    if token_user_id != str(user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Refresh token does not belong to the authenticated user",
        )

    # Revoke the refresh token
    revocation_service = TokenRevocationService(db, jwt_service)
    revocation_service.revoke_refresh_token(request.refresh_token)

    return {"message": "Successfully logged out"}