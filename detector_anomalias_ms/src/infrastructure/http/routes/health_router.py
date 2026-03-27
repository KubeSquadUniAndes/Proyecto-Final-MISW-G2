from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.base import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Service health check")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    db_status = "ok"
    db_detail = None
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = "error"
        db_detail = str(exc)

    response = {
        "status": "ok" if db_status == "ok" else "degraded",
        "service": "detector_anomalias_ms",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {"database": {"status": db_status}},
    }
    if db_detail:
        response["dependencies"]["database"]["detail"] = db_detail
    return response
