from uuid import UUID

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.infrastructure.clients.login_handler_client import LoginHandlerClient
from src.infrastructure.config.settings import settings

bearer_scheme = HTTPBearer()

_login_client = LoginHandlerClient(
    base_url=settings.LOGIN_HANDLER_MS_URL,
    jwt_secret=settings.JWT_SECRET_KEY,
    jwt_algorithm=settings.JWT_ALGORITHM,
)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> UUID:
    """Validates the JWT and checks the user is not blocked via login_handler_ms.

    Raises 401 for invalid/expired tokens.
    Raises 403 if the user is blocked or inactive.
    Raises 503 if login_handler_ms is unreachable.
    """
    token = credentials.credentials
    try:
        user_id = await _login_client.validate(token)
        return user_id
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except ConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )


async def get_current_user_role(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> tuple[UUID, str]:
    """Validates JWT and returns (user_id, role).
    
    Returns:
        tuple[UUID, str]: (user_id, role) where role is 'traveler' or 'hotel'
    
    Raises:
        401: Invalid/expired token
        403: User blocked or inactive
        503: Login handler unreachable
    """
    token = credentials.credentials
    try:
        user_data = await _login_client.validate_with_role(token)
        return user_data["user_id"], user_data["role"]
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except ConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
