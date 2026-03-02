import os
import logging

from sqlmodel import SQLModel, create_engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import users_model as users_model


POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL, echo=True)

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)


def validate_db_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info(
            "Database connection successful (host=%s port=%s db=%s user=%s)",
            POSTGRES_HOST,
            POSTGRES_PORT,
            POSTGRES_DB,
            POSTGRES_USER,
        )
        return True
    except (SQLAlchemyError, Exception):
        logger.exception(
            "Database connection failed (host=%s port=%s db=%s user=%s)",
            POSTGRES_HOST,
            POSTGRES_PORT,
            POSTGRES_DB,
            POSTGRES_USER,
        )
        return False

def create_db_and_tables():
    if not validate_db_connection():
        return
    SQLModel.metadata.create_all(engine)


