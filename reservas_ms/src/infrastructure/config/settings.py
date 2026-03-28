from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "reservas_ms"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/bookings_db"
    )
    DB_ECHO: bool = False

    # Server
    HOST: str = "0.0.0.0"  # nosec B104
    PORT: int = 8000
    WORKERS: int = 1

    # JWT (shared with login_handler_ms — used for local token decode)
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"

    # External services
    LOGIN_HANDLER_MS_URL: str = "http://login_handler_ms:8001"
    DETECTOR_ANOMALIAS_MS_URL: str = "http://detector_anomalias_ms:8002"
    DETECTOR_ANOMALIAS_MS_API_KEY: str = "change-internal-key-in-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
