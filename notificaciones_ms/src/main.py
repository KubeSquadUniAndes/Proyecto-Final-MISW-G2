from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.config.settings import settings
from src.infrastructure.http.routes.health_router import router as health_router
from src.infrastructure.http.routes.notification_router import (
    router as notification_router,
)
from src.infrastructure.http.routes.reservation_notification_router import (
    router as reservation_notification_router,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Notification microservice — dispatches alerts and reservation confirmations.\n\n"
            "**Called by:** `detector_anomalias_ms`, `reservas_ms`\n\n"
            "**Channels:** Email · Slack"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(notification_router, prefix="/api/v1")
    app.include_router(reservation_notification_router, prefix="/api/v1")

    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} started")
    return app


app = create_app()
