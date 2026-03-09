import ssl as ssl_module
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

RESERVATIONS_DDL = """
CREATE TABLE IF NOT EXISTS reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    traveler_name BYTEA NOT NULL,
    traveler_email BYTEA NOT NULL,
    traveler_phone BYTEA NOT NULL,
    traveler_document BYTEA NOT NULL,
    destination VARCHAR(255) NOT NULL,
    origin VARCHAR(255) NOT NULL,
    departure_date DATE NOT NULL,
    return_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    num_passengers INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""


class DatabaseManager:
    """Singleton database manager for async SQLAlchemy engine and session factory."""

    _engine = None
    _session_factory = None

    @classmethod
    async def initialize(cls) -> None:
        if cls._engine is not None:
            return

        settings = get_settings()

        # --- SSL: cifrado en transito hacia PostgreSQL (ASR-01) ---
        connect_args: dict = {}
        if settings.database_ssl:
            ssl_ctx = ssl_module.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl_module.CERT_NONE  # self-signed certs
            connect_args["ssl"] = ssl_ctx

        cls._engine = create_async_engine(
            settings.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        cls._session_factory = async_sessionmaker(
            bind=cls._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with cls._engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            await conn.execute(text(RESERVATIONS_DDL))

    @classmethod
    async def shutdown(cls) -> None:
        if cls._engine:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None

    @classmethod
    def get_session_factory(cls) -> async_sessionmaker[AsyncSession]:
        if cls._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return cls._session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    factory = DatabaseManager.get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
