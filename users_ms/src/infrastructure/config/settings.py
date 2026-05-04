from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "users_ms"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8004

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@travelhub-prod-postgres.ci3w0yecas02.us-east-1.rds.amazonaws.com:5432/users_db"
    LOGIN_HANDLER_MS_URL: str = "http://localhost:8000"
    INTERNAL_API_KEY: str = "secure_internal_api"
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
