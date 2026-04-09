from uuid import UUID

from fastapi import Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.infrastructure.config.settings import settings
from src.infrastructure.security.jwt_service import JWTService

bearer_scheme = HTTPBearer()
_jwt_service = JWTService()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> UUID:
    """Extracts and validates the JWT access token, returning the user_id."""
    try:
        payload = _jwt_service.decode_access_token(credentials.credentials)
        return UUID(payload["sub"])
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_internal_api_key(x_api_key: str = Header(...)) -> None:
    """Validates the internal API key used by other microservices (e.g. detector_anomalias_ms)."""
    if x_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing internal API key",
        )
