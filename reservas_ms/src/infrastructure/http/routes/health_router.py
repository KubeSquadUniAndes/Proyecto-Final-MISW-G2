from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.base import get_db

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health check del microservicio",
    response_description="Estado del servicio y sus dependencias",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Verifica el estado del microservicio y sus dependencias.

    Devuelve:
    - **status**: Estado general del servicio
    - **database**: Estado de la conexión a PostgreSQL
    - **timestamp**: Fecha y hora actual del servidor
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
