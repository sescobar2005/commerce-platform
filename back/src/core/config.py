"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All values are read from environment variables or a .env file.
    No credentials are hardcoded.
    """

    DATABASE_URL: str
    TEST_DATABASE_URL: str = ""

    SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_PRIVATE_KEY_PATH: str
    JWT_PUBLIC_KEY_PATH: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    ARGON2_MEMORY_COST: int
    ARGON2_TIME_COST: int
    ARGON2_PARALLELISM: int
    API_V1_STR: str
    PROJECT_NAME: str
    VERSION: str
    BACKEND_CORS_ORIGINS: str
    LOG_LEVEL: str

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()