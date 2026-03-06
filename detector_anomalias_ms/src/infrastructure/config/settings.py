from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "detector_anomalias_ms"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/anomalies_db"
    DB_ECHO: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    WORKERS: int = 1

    # Internal API key (used by reservas_ms to call this service)
    INTERNAL_API_KEY: str = "change-internal-key-in-production"

    # External services
    LOGIN_HANDLER_MS_URL: str = "http://login_handler_ms:8001"
    LOGIN_HANDLER_MS_INTERNAL_API_KEY: str = "change-internal-key-in-production"

    NOTIFICACIONES_MS_URL: str = "http://notificaciones_ms:8003"
    NOTIFICACIONES_MS_API_KEY: str = "change-internal-key-in-production"

    # Anomaly detection tuning
    RANDOM_ANOMALY_RATE: float = 0.30
    MAX_BOOKINGS_PER_WINDOW: int = 5
    MAX_DISTINCT_RESOURCES_PER_WINDOW: int = 4
    FREQUENCY_WINDOW_HOURS: int = 1
    MIN_DURATION_MINUTES: int = 15
    MAX_DURATION_MINUTES: int = 480

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()