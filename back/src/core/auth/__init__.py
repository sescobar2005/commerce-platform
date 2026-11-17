"""Authentication module for Plataforma de Comercio."""

from src.core.auth.router import router
from src.core.auth.dependencies import get_current_user, get_jwt_service, get_password_service

__all__ = ["router", "get_current_user", "get_jwt_service", "get_password_service"]
