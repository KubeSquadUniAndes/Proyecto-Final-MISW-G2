from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "pagos_ms"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@travelhub-prod-postgres.ci3w0yecas02.us-east-1.rds.amazonaws.com:5432/payments_db"
    DB_ECHO: bool = False

    # Server
    HOST: str = "0.0.0.0"  # nosec B104
    PORT: int = 8000
    WORKERS: int = 1

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Encryption — pgcrypto AES-256
    AES_ENCRYPTION_KEY: str = (
        "ebb9c223f7a78f929a3505b3bcdcccd957121330d3a7ee5b3acd591e269e9871"
    )

    # External services
    RESERVAS_MS_URL: str = "http://reservas_ms:8000"
    NOTIFICACIONES_MS_URL: str = "http://notificaciones_ms:8003"
    INTERNAL_API_KEY: str = "change-internal-key-in-production"

    # Payment retry config
    MAX_RETRY_ATTEMPTS: int = 3
    PAYMENT_TIMEOUT_MS: int = 500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
