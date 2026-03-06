from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.config.settings import settings
from src.infrastructure.database.base import Base, engine
from src.infrastructure.http.routes.health_router import router as health_router
from src.infrastructure.http.routes.booking_router import router as booking_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the application lifecycle."""
    # Startup: create tables if they don't exist (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
            "Bookings microservice with hexagonal architecture.\n\n"
            "**Microservices ecosystem:**\n"
            "- `reservas_ms` (this service): Creates and manages bookings\n"
            "- `login_handler_ms`: JWT authentication and access control\n"
            "- `detector_anomalias_ms`: Anomaly detection on booking patterns\n"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router)
    app.include_router(booking_router, prefix="/api/v1")

    return app


app = create_app()
