import jwt

from src.infrastructure.config.settings import settings


class JWTService:
    """Decodes and validates JWT tokens issued by login_handler_ms."""

    def decode_access_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("type") != "access":
                raise ValueError("Invalid token type")
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Access token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid access token: {e}")
