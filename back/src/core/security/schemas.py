"""Authentication request/response schemas using Pydantic.

Provides validated schemas for authentication requests and responses.
Never exposes sensitive fields such as password_hash.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    """Public user representation without sensitive fields.

    Excludes password_hash and other internal fields to prevent
    accidental exposure in API responses.
    """

    user_id: str
    username: str
    email: str
    is_seller: bool = False
    is_verified: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class UserRegisterRequest(BaseModel):
    """Request schema for user registration.

    Contains the required user registration fields following the
    existing User model and documented API contract.
    """

    username: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique username",
    )
    email: EmailStr = Field(
        ...,
        max_length=255,
        description="Unique email address",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Account password",
    )


class UserRegisterResponse(BaseModel):
    """Response schema for user registration.

    Returns public user data without sensitive fields.
    """

    user_id: str
    username: str
    email: str
    is_seller: bool = False
    is_verified: bool = False
    created_at: datetime


class UserLoginRequest(BaseModel):
    """Request schema for user login."""

    username: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Username for login",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Account password",
    )


class TokenResponse(BaseModel):
    """Reusable token response schema.

    Provides access and refresh tokens with token type.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    """Request schema for refreshing an access token using a refresh token."""

    refresh_token: str = Field(
        ...,
        min_length=1,
        description="Refresh token issued during login",
    )


class UserLoginResponse(BaseModel):
    """Response schema for user login.

    Returns authentication tokens and public user data.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
