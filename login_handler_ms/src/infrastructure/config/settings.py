from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "login_handler_ms"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database (dedicated DB for this service)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/auth_db"
    DB_ECHO: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    WORKERS: int = 1

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Internal API key (used by detector_anomalias_ms to call /block-user)
    INTERNAL_API_KEY: str = "change-internal-key-in-production"

    # External services
    DETECTOR_ANOMALIAS_MS_URL: str = "http://detector_anomalias_ms:8002"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
