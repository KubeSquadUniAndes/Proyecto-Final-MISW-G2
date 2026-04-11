from datetime import datetime, timedelta
from uuid import UUID

import jwt

from src.application.dtos.jwt_service_port import JWTServicePort
from src.infrastructure.config.settings import settings


class JWTService(JWTServicePort):
    """Output adapter: JWT creation and validation using PyJWT."""

    def create_access_token(
        self, user_id: UUID, extra_claims: dict | None = None
    ) -> str:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    def create_refresh_token(self, user_id: UUID) -> tuple[str, datetime]:
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
        }
        token = jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return token, expire

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

    def decode_refresh_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid refresh token: {e}")
