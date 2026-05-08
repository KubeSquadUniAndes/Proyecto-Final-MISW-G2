from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "reservas_ms"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database — default points to production RDS, override in .env for local development
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@travelhub-prod-postgres.ci3w0yecas02.us-east-1.rds.amazonaws.com:5432/bookings_db"
    DB_ECHO: bool = False

    # Server
    HOST: str = "0.0.0.0"  # nosec B104
    PORT: int = 8000
    WORKERS: int = 1

    # JWT (shared with login_handler_ms — used for local token decode)
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Encryption — injected via K8s Secret in production (AWS Secrets Manager)
    # In local development, set this in .env (never commit)
    AES_ENCRYPTION_KEY: str = (
        "ebb9c223f7a78f929a3505b3bcdcccd957121330d3a7ee5b3acd591e269e9871"
    )

    # External services
    LOGIN_HANDLER_MS_URL: str = "http://login_handler_ms:8001"
    DETECTOR_ANOMALIAS_MS_URL: str = "http://detector_anomalias_ms:8002"
    DETECTOR_ANOMALIAS_MS_API_KEY: str = "change-internal-key-in-production"
    INTERNAL_API_KEY: str = "change-internal-key-in-production"
    NOTIFICACIONES_MS_URL: str = "http://notificaciones_ms:8003"
    NOTIFICACIONES_MS_API_KEY: str = "change-internal-key-in-production"
    USERS_MS_URL: str = "http://users_ms:8004"
    USERS_MS_INTERNAL_API_KEY: str = "secure_internal_api"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
