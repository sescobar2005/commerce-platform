"""SQLAlchemy 2.0 database engine configuration."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""


def create_db_engine(database_url: str | None = None):
    """Create and return a SQLAlchemy 2.0 engine.

    Args:
        database_url: Optional database URL. If not provided, uses
            DATABASE_URL from application settings.

    Returns:
        A configured SQLAlchemy Engine instance.

    Raises:
        ValueError: If no database URL is available.
    """
    url = database_url or settings.DATABASE_URL
    if not url:
        raise ValueError(
            "DATABASE_URL is not configured. Set it in environment variables "
            "or in a .env file derived from .env.example."
        )
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
    )


engine = create_db_engine()