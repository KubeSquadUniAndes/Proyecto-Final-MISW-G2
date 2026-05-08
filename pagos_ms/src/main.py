from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.infrastructure.config.settings import settings
from src.infrastructure.database.base import Base, engine
from src.infrastructure.http.routes.health_router import router as health_router
from src.infrastructure.http.routes.payment_router import router as payment_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the application lifecycle."""
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Enable pgcrypto extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} started")
    yield
    # Shutdown
    await engine.dispose()
    print(f"🛑 {settings.APP_NAME} stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Payments microservice with hexagonal architecture.\\n\\n"
            "**Features:**\\n"
            "- Payment confirmation with retry logic\\n"
            "- Booking status update (< 500ms)\\n"
            "- PGCrypto AES-256 encryption for sensitive data\\n"
            "- Audit logging\\n"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router)
    app.include_router(payment_router, prefix="/api/v1")

    return app


app = create_app()
