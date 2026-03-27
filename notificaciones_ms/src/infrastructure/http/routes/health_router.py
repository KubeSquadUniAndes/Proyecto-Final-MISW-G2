from datetime import datetime
from fastapi import APIRouter

from src.infrastructure.config.settings import settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Service health check")
async def health_check() -> dict:
    return {
        "status": "ok",
        "service": "notificaciones_ms",
        "timestamp": datetime.utcnow().isoformat(),
        "channels": {
            "email": "configured" if settings.SMTP_USER else "not configured",
            "slack": "configured" if settings.SLACK_WEBHOOK_URL else "not configured",
        },
    }
