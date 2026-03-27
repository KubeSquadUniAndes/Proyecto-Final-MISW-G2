from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.config.settings import settings
from src.infrastructure.database.base import Base, engine
from src.infrastructure.http.routes.analysis_router import router as analysis_router
from src.infrastructure.http.routes.health_router import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} started")
    print(f"   Random anomaly rate: {settings.RANDOM_ANOMALY_RATE:.0%}")
    yield
    await engine.dispose()
    print(f"🛑 {settings.APP_NAME} stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Anomaly detection microservice with hexagonal architecture.\n\n"
            "**Detection rules:**\n"
            "- 🎲 Random sampling (configurable rate, default 30%) — for experiment testing\n"
            "- 📈 High booking frequency (> N bookings in last hour)\n"
            "- ⏱ Unusual booking duration (too short or too long)\n"
            "- 🔀 Multiple different resources in a short window\n\n"
            "**On anomaly detected:**\n"
            "1. Persists `AnomalyEvent` to DB\n"
            "2. Calls `login_handler_ms → POST /auth/block-user` (revokes all sessions)\n"
            "3. Sends security alert email via SMTP\n"
            "4. Logs structured security entry\n"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(analysis_router, prefix="/api/v1")

    return app


app = create_app()
