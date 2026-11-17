"""SQLAlchemy 2.0 database engine and session configuration."""

from typing import Generator

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

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

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session per request.

    Yields:
        A SQLAlchemy Session instance bound to the application engine.

    The session is automatically closed when the generator is exhausted,
    even if an exception occurs during the request. Callers should use
    this as a FastAPI dependency:

        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()