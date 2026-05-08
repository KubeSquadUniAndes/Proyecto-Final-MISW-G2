from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.infrastructure.config.settings import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency to inject a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            print("DEBUG: About to commit session")
            await session.commit()
            print("DEBUG: Session committed successfully")
        except Exception as e:
            print(f"DEBUG: Exception during commit: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
