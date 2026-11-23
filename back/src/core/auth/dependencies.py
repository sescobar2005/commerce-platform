"""Authentication dependencies for FastAPI.

Provides reusable dependencies for extracting and validating JWT access tokens
from the Authorization header, and resolving the authenticated user.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.database import get_db
from src.core.models.user import User
from src.core.security.jwt import JWTService
from src.core.security.password import PasswordService
from src.core.security.schemas import UserResponse
from sqlalchemy.orm import Session

bearer_scheme = HTTPBearer(auto_error=False)


def get_password_service() -> PasswordService:
    """Dependency that provides a PasswordService instance."""
    return PasswordService()


def get_jwt_service() -> JWTService:
    """Dependency that provides a JWTService instance."""
    return JWTService()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session = Depends(get_db),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> UserResponse:
    """Validate a Bearer access token and return the authenticated user.

    Args:
        credentials: Bearer token credentials from the Authorization header.
        db: Database session dependency.
        jwt_service: JWT token service dependency.

    Returns:
        UserResponse: The authenticated user's public data.

    Raises:
        HTTPException: 401 if credentials are missing, invalid, expired,
            malformed, or if the user does not exist.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = jwt_service.verify_access_token(token)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserResponse(
        user_id=str(user.user_id),
        username=user.username,
        email=user.email,
        is_seller=user.is_seller,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        created_at=user.created_at,
    )


# Dependency alias for use in route definitions
CurrentUser = Annotated[UserResponse, Depends(get_current_user)]
