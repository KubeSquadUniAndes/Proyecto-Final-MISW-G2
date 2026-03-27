from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.base import get_db

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Service health check",
    response_description="Service and dependency status",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Checks the health of the microservice and its dependencies.

    Returns:
    - **status**: Overall service status
    - **database**: PostgreSQL connection status
    - **timestamp**: Current server timestamp
    """
    db_status = "ok"
    db_detail = None

    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = "error"
        db_detail = str(exc)

    overall_status = "ok" if db_status == "ok" else "degraded"

    response = {
        "status": overall_status,
        "service": "reservas_ms",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "database": {
                "status": db_status,
            }
        },
    }

    if db_detail:
        response["dependencies"]["database"]["detail"] = db_detail

    return response
