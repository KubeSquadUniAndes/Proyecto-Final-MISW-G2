"""Unit tests for additional auth use cases."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.application.dtos.auth_dto import RefreshTokenDTO
from src.application.use_cases.get_me import GetMeUseCase
from src.application.use_cases.logout import LogoutUseCase
from src.application.use_cases.refresh_token import RefreshTokenUseCase
from src.domain.entities.refresh_token import RefreshToken
from src.domain.entities.user import User, UserRole, UserStatus


class MockUserRepository:
    def __init__(self):
        self.users = {}

    async def get_by_id(self, user_id):
        return self.users.get(user_id)


class MockRefreshTokenRepository:
    def __init__(self):
        self.tokens = {}

    async def get_by_token(self, token):
        return self.tokens.get(token)

    async def revoke_by_token(self, token):
        if token in self.tokens:
            del self.tokens[token]

    async def save(self, token):
        self.tokens[token.token] = token
        return token


class MockJWTService:
    def create_access_token(self, user_id):
        return f"access.token.{user_id}"

    def create_refresh_token(self, user_id):
        return f"refresh.token.{user_id}", datetime.now(timezone.utc) + timedelta(days=7)


@pytest.mark.asyncio
async def test_get_me_success():
    """Test getting user profile."""
    repo = MockUserRepository()
    use_case = GetMeUseCase(repo)

    user_id = uuid4()
    user = User(
        id=user_id,
        email="test@example.com",
        full_name="Test User",
        hashed_password="hash",
        role=UserRole.TRAVELER,
    )
    repo.users[user_id] = user

    result = await use_case.execute(user_id)

    assert result.id == user_id
    assert result.email == "test@example.com"
    assert result.full_name == "Test User"
    assert result.role == UserRole.TRAVELER


@pytest.mark.asyncio
async def test_get_me_user_not_found():
    """Test get_me fails when user doesn't exist."""
    repo = MockUserRepository()
    use_case = GetMeUseCase(repo)

    with pytest.raises(ValueError, match="User not found"):
        await use_case.execute(uuid4())


@pytest.mark.asyncio
async def test_logout_success():
    """Test successful logout."""
    repo = MockRefreshTokenRepository()
    use_case = LogoutUseCase(repo)

    token_str = "refresh.token.123"
    token = RefreshToken(
        user_id=uuid4(),
        token=token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    repo.tokens[token_str] = token

    dto = RefreshTokenDTO(refresh_token=token_str)
    result = await use_case.execute(dto)

    assert result.message == "Logged out successfully"
    assert token_str not in repo.tokens


@pytest.mark.asyncio
async def test_logout_token_not_found():
    """Test logout fails when token doesn't exist."""
    repo = MockRefreshTokenRepository()
    use_case = LogoutUseCase(repo)

    dto = RefreshTokenDTO(refresh_token="invalid.token")

    with pytest.raises(ValueError, match="Refresh token not found"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_refresh_token_success():
    """Test successful token refresh."""
    user_repo = MockUserRepository()
    token_repo = MockRefreshTokenRepository()
    jwt_service = MockJWTService()
    use_case = RefreshTokenUseCase(jwt_service, token_repo, user_repo)

    user_id = uuid4()
    user = User(
        id=user_id,
        email="test@example.com",
        full_name="Test User",
        hashed_password="hash",
        role=UserRole.TRAVELER,
    )
    user_repo.users[user_id] = user

    old_token = "old.refresh.token"
    token_entity = RefreshToken(
        user_id=user_id,
        token=old_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    token_repo.tokens[old_token] = token_entity

    dto = RefreshTokenDTO(refresh_token=old_token)
    result = await use_case.execute(dto)

    assert result.access_token.startswith("access.token.")
    assert result.refresh_token.startswith("refresh.token.")
    assert old_token not in token_repo.tokens


@pytest.mark.asyncio
async def test_refresh_token_invalid():
    """Test refresh fails with invalid token."""
    user_repo = MockUserRepository()
    token_repo = MockRefreshTokenRepository()
    jwt_service = MockJWTService()
    use_case = RefreshTokenUseCase(jwt_service, token_repo, user_repo)

    dto = RefreshTokenDTO(refresh_token="invalid.token")

    with pytest.raises(ValueError, match="Invalid or expired refresh token"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_refresh_token_expired():
    """Test refresh fails with expired token."""
    user_repo = MockUserRepository()
    token_repo = MockRefreshTokenRepository()
    jwt_service = MockJWTService()
    use_case = RefreshTokenUseCase(jwt_service, token_repo, user_repo)

    user_id = uuid4()
    expired_token = "expired.token"
    token_entity = RefreshToken(
        user_id=user_id,
        token=expired_token,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    token_repo.tokens[expired_token] = token_entity

    dto = RefreshTokenDTO(refresh_token=expired_token)

    with pytest.raises(ValueError, match="Invalid or expired refresh token"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_refresh_token_blocked_user():
    """Test refresh fails when user is blocked."""
    user_repo = MockUserRepository()
    token_repo = MockRefreshTokenRepository()
    jwt_service = MockJWTService()
    use_case = RefreshTokenUseCase(jwt_service, token_repo, user_repo)

    user_id = uuid4()
    user = User(
        id=user_id,
        email="test@example.com",
        full_name="Test User",
        hashed_password="hash",
        role=UserRole.TRAVELER,
        status=UserStatus.BLOCKED,
    )
    user_repo.users[user_id] = user

    token_str = "valid.token"
    token_entity = RefreshToken(
        user_id=user_id,
        token=token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    token_repo.tokens[token_str] = token_entity

    dto = RefreshTokenDTO(refresh_token=token_str)

    with pytest.raises(PermissionError, match="User account is blocked or inactive"):
        await use_case.execute(dto)
