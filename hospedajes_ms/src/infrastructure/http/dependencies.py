from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.infrastructure.security.jwt_service import JWTService

bearer_scheme = HTTPBearer()
_jwt_service = JWTService()


@dataclass
class TokenClaims:
    user_id: UUID
    full_name: str | None = None


async def require_hotel_role(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> TokenClaims:
    """Validates JWT and ensures the caller has the 'hotel' role."""
    try:
        payload = _jwt_service.decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = payload.get("role")
    if role != "hotel":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to hotel role",
        )

    return TokenClaims(
        user_id=UUID(payload["sub"]),
        full_name=payload.get("full_name"),
    )


async def require_hotel_or_traveler_role(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> TokenClaims:
    """Validates JWT and ensures the caller has the 'hotel' or 'traveler' role."""
    try:
        payload = _jwt_service.decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = payload.get("role")
    if role not in ("hotel", "traveler"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to hotel or traveler role",
        )

    return TokenClaims(
        user_id=UUID(payload["sub"]),
        full_name=payload.get("full_name"),
    )
