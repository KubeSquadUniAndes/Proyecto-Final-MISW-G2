from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.config.settings import settings
from src.infrastructure.database.base import Base, engine
from src.infrastructure.http.routes.health_router import router as health_router
from src.infrastructure.http.routes.reserva_router import router as reserva_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación."""
    # Startup: crear tablas si no existen (en producción usar Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} iniciado")
    yield
    # Shutdown
    await engine.dispose()
    print(f"🛑 {settings.APP_NAME} detenido")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Microservicio de gestión de reservas con arquitectura hexagonal.\n\n"
            "**Ecosistema de microservicios:**\n"
            "- `reservas_ms` (este servicio): Crea y gestiona reservas\n"
            "- `login_handler_ms`: Autenticación JWT y control de acceso\n"
            "- `detector_anomalias_ms`: Detección de patrones anómalos en reservas\n"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restringir en producción
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router)
    app.include_router(reserva_router, prefix="/api/v1")

    return app


app = create_app()
