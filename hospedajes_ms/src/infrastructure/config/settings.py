from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "hospedajes_ms"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/hospedajes_db"
    )
    DB_ECHO: bool = False

    HOST: str = "0.0.0.0"  # nosec B104
    PORT: int = 8003
    WORKERS: int = 1

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"

    USERS_MS_URL: str = "http://localhost:8004"
    RESERVAS_MS_URL: str = "http://localhost:8000"
    INTERNAL_API_KEY: str = "secure_internal_api"

    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "travelhub-images-780522923809"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
