from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "notificaciones_ms"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8003
    WORKERS: int = 1

    # Internal API key (detector_anomalias_ms uses this to call this service)
    INTERNAL_API_KEY: str = "change-internal-key-in-production"

    # Email (SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "alerts@experiment.local"
    EMAIL_TO: str = "security@experiment.local"

    # Slack
    SLACK_WEBHOOK_URL: str = ""
    SLACK_CHANNEL: str = "#security-alerts"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
