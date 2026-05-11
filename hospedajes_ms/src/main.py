import asyncio
import logging
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.config.settings import settings
from src.infrastructure.database.base import Base, engine
from src.infrastructure.database.models import room_image_model, room_model  # noqa: F401
from src.infrastructure.database.models import discount_model, rate_model  # noqa: F401
from src.infrastructure.http.routes.health_router import router as health_router
from src.infrastructure.http.routes.rate_router import router as rate_router
from src.infrastructure.http.routes.room_image_router import router as room_image_router
from src.infrastructure.http.routes.room_router import router as room_router
from src.infrastructure.messaging.sqs_room_availability_consumer import poll_sqs_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    consumer_task = asyncio.create_task(poll_sqs_loop())
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} started")
    yield
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        logging.info("sqs_consumer_stopped")
        pass
    await engine.dispose()
    print(f"🛑 {settings.APP_NAME} stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Room management microservice with hexagonal architecture.",
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
    app.include_router(room_router, prefix="/api/v1")
    app.include_router(room_image_router, prefix="/api/v1")
    app.include_router(rate_router, prefix="/api/v1")

    return app


app = create_app()
