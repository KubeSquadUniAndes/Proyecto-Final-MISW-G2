"""Infrastructure layer tests for login_handler_ms."""
import os
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient, ASGITransport

from src.infrastructure.config.settings import Settings
from src.infrastructure.http.schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
    ErrorResponse,
    BlockUserRequest,
    RefreshTokenRequest,
)
from src.domain.entities.user import User, UserStatus
from src.domain.entities.refresh_token import RefreshToken
from src.infrastructure.security.bcrypt_password_service import BcryptPasswordService
from src.infrastructure.security.jwt_service import JWTService


# ── Settings ──────────────────────────────────────────────────────────────────

def test_settings_defaults():
    s = Settings(DATABASE_URL="postgresql+asyncpg://x:x@localhost/x")
    assert s.APP_NAME == "login_handler_ms"
    assert s.JWT_ALGORITHM == "HS256"
    assert s.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0


def test_settings_override():
    s = Settings(DATABASE_URL="postgresql+asyncpg://x:x@localhost/x", DEBUG=True)
    assert s.DEBUG is True


# ── Schemas ───────────────────────────────────────────────────────────────────

def test_register_request_valid():
    r = RegisterRequest(email="user@example.com", password="securepass123")
    assert r.email == "user@example.com"


def test_register_request_short_password():
    with pytest.raises(Exception):
        RegisterRequest(email="user@example.com", password="short")


def test_login_request():
    r = LoginRequest(email="user@example.com", password="pass")
    assert r.email == "user@example.com"


def test_block_user_request():
    r = BlockUserRequest(user_id=uuid4(), reason="anomaly")
    assert r.reason == "anomaly"


def test_error_response():
    e = ErrorResponse(detail="error", code="E001")
    assert e.code == "E001"


# ── BcryptPasswordService ─────────────────────────────────────────────────────

def test_bcrypt_hash_and_verify():
    svc = BcryptPasswordService()
    hashed = svc.hash("mypassword")
    assert hashed != "mypassword"
    assert svc.verify("mypassword", hashed) is True


def test_bcrypt_wrong_password():
    svc = BcryptPasswordService()
    hashed = svc.hash("correct")
    assert svc.verify("wrong", hashed) is False


# ── JWTService ────────────────────────────────────────────────────────────────

def test_jwt_create_and_decode_access_token():
    svc = JWTService()
    uid = uuid4()
    token = svc.create_access_token(uid)
    payload = svc.decode_access_token(token)
    assert payload["sub"] == str(uid)
    assert payload["type"] == "access"


def test_jwt_create_and_decode_refresh_token():
    svc = JWTService()
    uid = uuid4()
    token, expires = svc.create_refresh_token(uid)
    assert isinstance(expires, datetime)
    payload = svc.decode_refresh_token(token)
    assert payload["sub"] == str(uid)
    assert payload["type"] == "refresh"


def test_jwt_decode_wrong_type():
    svc = JWTService()
    uid = uuid4()
    access_token = svc.create_access_token(uid)
    with pytest.raises(ValueError, match="Invalid token type"):
        svc.decode_refresh_token(access_token)


def test_jwt_decode_invalid_token():
    svc = JWTService()
    with pytest.raises(ValueError):
        svc.decode_access_token("not.a.token")


# ── User entity ───────────────────────────────────────────────────────────────

def test_user_block_and_unblock():
    u = User(email="a@b.com", hashed_password="x")
    assert u.is_active()
    u.block()
    assert u.is_blocked()
    u.unblock()
    assert u.is_active()


def test_user_block_already_blocked():
    u = User(email="a@b.com", hashed_password="x", status=UserStatus.BLOCKED)
    with pytest.raises(ValueError):
        u.block()


def test_user_unblock_not_blocked():
    u = User(email="a@b.com", hashed_password="x")
    with pytest.raises(ValueError):
        u.unblock()


# ── RefreshToken entity ───────────────────────────────────────────────────────

def test_refresh_token_valid():
    t = RefreshToken(user_id=uuid4(), token="tok", expires_at=datetime.now(timezone.utc) + timedelta(days=1))
    assert t.is_valid() is True


def test_refresh_token_expired():
    t = RefreshToken(user_id=uuid4(), token="tok", expires_at=datetime.now(timezone.utc) - timedelta(days=1))
    assert t.is_valid() is False


def test_refresh_token_revoked():
    t = RefreshToken(user_id=uuid4(), token="tok", expires_at=datetime.now(timezone.utc) + timedelta(days=1))
    t.revoke()
    assert t.is_valid() is False


# ── SQLAlchemy User Repository ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_repo_save():
    from src.infrastructure.database.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
    user = User(email="test@test.com", hashed_password="hashed")
    mock_session = AsyncMock()
    mock_model = MagicMock()
    mock_model.id = user.id
    mock_model.email = user.email
    mock_model.hashed_password = user.hashed_password
    mock_model.full_name = user.full_name
    mock_model.status = user.status
    mock_model.is_superuser = user.is_superuser
    mock_model.created_at = user.created_at
    mock_model.updated_at = user.updated_at
    mock_session.refresh = AsyncMock(side_effect=lambda m: None)

    repo = SQLAlchemyUserRepository(mock_session)
    with patch.object(repo, "_to_domain", return_value=user):
        result = await repo.save(user)
    assert result == user
    mock_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_user_repo_get_by_email_not_found():
    from src.infrastructure.database.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = SQLAlchemyUserRepository(mock_session)
    result = await repo.get_by_email("notfound@test.com")
    assert result is None


@pytest.mark.asyncio
async def test_user_repo_get_by_id_not_found():
    from src.infrastructure.database.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = SQLAlchemyUserRepository(mock_session)
    result = await repo.get_by_id(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_user_repo_delete_not_found():
    from src.infrastructure.database.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = SQLAlchemyUserRepository(mock_session)
    result = await repo.delete(uuid4())
    assert result is False


@pytest.mark.asyncio
async def test_user_repo_update_not_found():
    from src.infrastructure.database.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = SQLAlchemyUserRepository(mock_session)
    user = User(email="x@x.com", hashed_password="h")
    with pytest.raises(ValueError):
        await repo.update(user)


# ── HTTP Router ───────────────────────────────────────────────────────────────

def _make_app():
    with patch("src.infrastructure.database.base.create_async_engine") as mock_engine, \
         patch("src.infrastructure.database.base.async_sessionmaker"):
        mock_engine.return_value = MagicMock()
        from src.main import create_app
        return create_app()


@pytest.fixture
def app():
    return _make_app()


@pytest.mark.asyncio
async def test_health_endpoint(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_register_endpoint_success(app):
    from src.application.dtos.auth_dto import UserResponseDTO
    mock_result = UserResponseDTO(
        id=uuid4(), email="new@test.com", full_name=None,
        status=UserStatus.ACTIVE, is_superuser=False, role=None,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.infrastructure.database.base.AsyncSessionLocal", return_value=mock_session), \
         patch("src.infrastructure.http.routes.auth_router.RegisterUserUseCase") as MockUC:
        mock_uc = AsyncMock()
        mock_uc.execute.return_value = mock_result
        MockUC.return_value = mock_uc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/register", json={
                "email": "new@test.com",
                "password": "securepass123",
            })
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_register_endpoint_conflict(app):
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.infrastructure.database.base.AsyncSessionLocal", return_value=mock_session), \
         patch("src.infrastructure.http.routes.auth_router.RegisterUserUseCase") as MockUC:
        mock_uc = AsyncMock()
        mock_uc.execute.side_effect = ValueError("already registered")
        MockUC.return_value = mock_uc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/register", json={
                "email": "dup@test.com",
                "password": "securepass123",
            })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_endpoint_success(app):
    from src.application.dtos.auth_dto import TokenResponseDTO
    mock_result = TokenResponseDTO(access_token="acc", refresh_token="ref")
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.infrastructure.database.base.AsyncSessionLocal", return_value=mock_session), \
         patch("src.infrastructure.http.routes.auth_router.LoginUseCase") as MockUC:
        mock_uc = AsyncMock()
        mock_uc.execute.return_value = mock_result
        MockUC.return_value = mock_uc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/login", json={
                "email": "user@test.com",
                "password": "pass",
            })
    assert resp.status_code == 200
    assert resp.json()["access_token"] == "acc"


@pytest.mark.asyncio
async def test_login_endpoint_invalid_credentials(app):
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.infrastructure.database.base.AsyncSessionLocal", return_value=mock_session), \
         patch("src.infrastructure.http.routes.auth_router.LoginUseCase") as MockUC:
        mock_uc = AsyncMock()
        mock_uc.execute.side_effect = ValueError("Invalid credentials")
        MockUC.return_value = mock_uc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/login", json={
                "email": "user@test.com",
                "password": "wrong",
            })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_block_user_missing_api_key(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/block-user", json={
            "user_id": str(uuid4()),
        })
    assert resp.status_code in (403, 422)


@pytest.mark.asyncio
async def test_block_user_wrong_api_key(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/block-user",
            json={"user_id": str(uuid4())},
            headers={"x-api-key": "definitely-wrong-key"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_me_no_token(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_logout_endpoint(app):
    from src.application.dtos.auth_dto import MessageDTO
    mock_result = MessageDTO(message="logged out")
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.infrastructure.database.base.AsyncSessionLocal", return_value=mock_session), \
         patch("src.infrastructure.http.routes.auth_router.LogoutUseCase") as MockUC:
        mock_uc = AsyncMock()
        mock_uc.execute.return_value = mock_result
        MockUC.return_value = mock_uc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/logout", json={"refresh_token": "tok"})
    assert resp.status_code == 200
