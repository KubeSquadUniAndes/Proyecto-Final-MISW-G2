from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+asyncpg://travelhub:travelhub_dev@localhost:5432/travelhub"
    )
    encryption_key: str = "default-dev-key-change-in-production"
    app_name: str = "TravelHub Reservations Service"
    debug: bool = False

    model_config = {"env_file": ".env"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
