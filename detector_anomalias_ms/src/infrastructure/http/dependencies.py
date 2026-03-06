from fastapi import Header, HTTPException, status

from src.infrastructure.config.settings import settings


async def require_internal_api_key(x_api_key: str = Header(...)) -> None:
    """Validates the internal API key. Only reservas_ms (and trusted services) may call this."""
    if x_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing internal API key",
        )
