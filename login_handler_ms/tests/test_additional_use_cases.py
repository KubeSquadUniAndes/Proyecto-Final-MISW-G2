"""Tests for logout, refresh_token, get_me use cases and domain entities."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.dtos.auth_dto import RefreshTokenDTO, BlockUserDTO
from src.application.use_cases.logout import LogoutUseCase
from src.application.use_cases.refresh_token import RefreshTokenUseCase
from src.application.use_cases.get_me import GetMeUseCase
from src.domain.entities.user import User, UserStatus
from src.domain.entities.refresh_token import RefreshToken


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_token_repo():
    return AsyncMock()


@pytest.fixture
def mock_jwt():
    svc = MagicMock()
    svc.create_access_token.return_value = "new.access.token"
    svc.create_refresh_token.return_value = ("new.refresh.token", datetime.utcnow() + timedelta(days=7))
    return svc


@pytest.fixture
def active_user():
    return User(
        id=uuid4(),
        email="user@example.com",
        hashed_password="hashed",
        status=UserStatus.ACTIVE,
    )


@pytest.fixture
def valid_token(active_user):
    return RefreshToken(
        user_id=active_user.id,
        token="valid.refresh.token",
        expires_at=datetime.utcnow() + timedelta(days=7),
    )


# ── LogoutUseCase ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout_success(mock_token_repo, valid_token):
    mock_token_repo.get_by_token.return_value = valid_token

    result = await LogoutUseCase(mock_token_repo).execute(RefreshTokenDTO(refresh_token="valid.refresh.token"))

    assert "logged out" in result.message.lower()
    mock_token_repo.revoke_by_token.assert_called_once_with("valid.refresh.token")


@pytest.mark.asyncio
async def test_logout_token_not_found(mock_token_repo):
    mock_token_repo.get_by_token.return_value = None

    with pytest.raises(ValueError, match="not found"):
        await LogoutUseCase(mock_token_repo).execute(RefreshTokenDTO(refresh_token="bad.token"))


# ── RefreshTokenUseCase ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_token_success(mock_jwt, mock_token_repo, mock_user_repo, active_user, valid_token):
    mock_token_repo.get_by_token.return_value = valid_token
    mock_token_repo.save.return_value = MagicMock()
    mock_user_repo.get_by_id.return_value = active_user

    result = await RefreshTokenUseCase(mock_jwt, mock_token_repo, mock_user_repo).execute(
        RefreshTokenDTO(refresh_token="valid.refresh.token")
    )

    assert result.access_token == "new.access.token"
    assert result.refresh_token == "new.refresh.token"
    mock_token_repo.revoke_by_token.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_token_invalid(mock_jwt, mock_token_repo, mock_user_repo):
    mock_token_repo.get_by_token.return_value = None

    with pytest.raises(ValueError, match="Invalid or expired"):
        await RefreshTokenUseCase(mock_jwt, mock_token_repo, mock_user_repo).execute(
            RefreshTokenDTO(refresh_token="bad.token")
        )


@pytest.mark.asyncio
async def test_refresh_token_revoked(mock_jwt, mock_token_repo, mock_user_repo, valid_token):
    valid_token.revoked = True
    mock_token_repo.get_by_token.return_value = valid_token

    with pytest.raises(ValueError, match="Invalid or expired"):
        await RefreshTokenUseCase(mock_jwt, mock_token_repo, mock_user_repo).execute(
            RefreshTokenDTO(refresh_token="valid.refresh.token")
        )


@pytest.mark.asyncio
async def test_refresh_token_blocked_user(mock_jwt, mock_token_repo, mock_user_repo, valid_token, active_user):
    active_user.status = UserStatus.BLOCKED
    mock_token_repo.get_by_token.return_value = valid_token
    mock_user_repo.get_by_id.return_value = active_user

    with pytest.raises(PermissionError, match="blocked"):
        await RefreshTokenUseCase(mock_jwt, mock_token_repo, mock_user_repo).execute(
            RefreshTokenDTO(refresh_token="valid.refresh.token")
        )


# ── GetMeUseCase ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_success(mock_user_repo, active_user):
    mock_user_repo.get_by_id.return_value = active_user

    result = await GetMeUseCase(mock_user_repo).execute(active_user.id)

    assert result.email == active_user.email
    assert result.status == UserStatus.ACTIVE


@pytest.mark.asyncio
async def test_get_me_not_found(mock_user_repo):
    mock_user_repo.get_by_id.return_value = None

    with pytest.raises(ValueError, match="not found"):
        await GetMeUseCase(mock_user_repo).execute(uuid4())


# ── User entity ───────────────────────────────────────────────────────────────

def test_user_block():
    user = User(email="a@b.com", hashed_password="h")
    user.block()
    assert user.status == UserStatus.BLOCKED


def test_user_block_already_blocked():
    user = User(email="a@b.com", hashed_password="h", status=UserStatus.BLOCKED)
    with pytest.raises(ValueError, match="already blocked"):
        user.block()


def test_user_unblock():
    user = User(email="a@b.com", hashed_password="h", status=UserStatus.BLOCKED)
    user.unblock()
    assert user.status == UserStatus.ACTIVE


def test_user_unblock_not_blocked():
    user = User(email="a@b.com", hashed_password="h")
    with pytest.raises(ValueError, match="not blocked"):
        user.unblock()


def test_user_is_active_and_blocked():
    user = User(email="a@b.com", hashed_password="h")
    assert user.is_active() is True
    assert user.is_blocked() is False
    user.block()
    assert user.is_active() is False
    assert user.is_blocked() is True


# ── RefreshToken entity ───────────────────────────────────────────────────────

def test_refresh_token_is_valid():
    token = RefreshToken(user_id=uuid4(), token="t", expires_at=datetime.utcnow() + timedelta(days=1))
    assert token.is_valid() is True


def test_refresh_token_expired():
    token = RefreshToken(user_id=uuid4(), token="t", expires_at=datetime.utcnow() - timedelta(days=1))
    assert token.is_valid() is False


def test_refresh_token_revoke():
    token = RefreshToken(user_id=uuid4(), token="t", expires_at=datetime.utcnow() + timedelta(days=1))
    token.revoke()
    assert token.is_valid() is False
