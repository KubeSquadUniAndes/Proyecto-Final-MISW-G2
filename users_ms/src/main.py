from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.infrastructure.config.settings import settings
from src.infrastructure.database.database import Base, engine
from src.infrastructure.http.routes.user_router import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} started")
    yield
    await engine.dispose()
    print(f"🛑 {settings.APP_NAME} stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(user_router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
