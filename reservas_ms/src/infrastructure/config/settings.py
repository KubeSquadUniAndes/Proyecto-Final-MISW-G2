from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "reservas_ms"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/reservas_db"
    DB_ECHO: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # Servicios externos (para futura integración)
    # login_handler_ms
    LOGIN_HANDLER_MS_URL: str = "http://login_handler_ms:8001"
    LOGIN_HANDLER_MS_API_KEY: str = ""

    # detector_anomalias_ms
    DETECTOR_ANOMALIAS_MS_URL: str = "http://detector_anomalias_ms:8002"
    DETECTOR_ANOMALIAS_MS_API_KEY: str = ""

    # JWT (compartido con login_handler_ms)
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
