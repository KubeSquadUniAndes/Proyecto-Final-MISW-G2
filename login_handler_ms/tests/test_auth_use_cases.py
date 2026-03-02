"""Tests for auth use cases using mocks."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.dtos.auth_dto import LoginDTO, RegisterUserDTO, BlockUserDTO
from src.application.use_cases.login import LoginUseCase
from src.application.use_cases.register_user import RegisterUserUseCase
from src.application.use_cases.block_user import BlockUserUseCase
from src.domain.entities.user import User, UserStatus
from src.domain.services.auth_domain_service import AuthDomainService


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_token_repo():
    repo = AsyncMock()
    repo.revoke_all_by_user.return_value = 2
    return repo


@pytest.fixture
def mock_password_service():
    svc = MagicMock()
    svc.hash.return_value = "hashed_password"
    svc.verify.return_value = True
    return svc


@pytest.fixture
def mock_jwt_service():
    svc = MagicMock()
    from datetime import datetime, timedelta
    svc.create_access_token.return_value = "access.token.here"
    svc.create_refresh_token.return_value = ("refresh.token.here", datetime.utcnow() + timedelta(days=7))
    return svc


@pytest.fixture
def active_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        status=UserStatus.ACTIVE,
    )


# ── Register tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(mock_user_repo, mock_password_service, active_user):
    mock_user_repo.get_by_email.return_value = None
    mock_user_repo.save.return_value = active_user

    auth_service = AuthDomainService(mock_user_repo, mock_password_service)
    use_case = RegisterUserUseCase(mock_user_repo, auth_service, mock_password_service)

    result = await use_case.execute(
        RegisterUserDTO(email="test@example.com", password="securepass123")
    )

    assert result.email == active_user.email
    mock_user_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_register_duplicate_email(mock_user_repo, mock_password_service, active_user):
    mock_user_repo.get_by_email.return_value = active_user  # email taken

    auth_service = AuthDomainService(mock_user_repo, mock_password_service)
    use_case = RegisterUserUseCase(mock_user_repo, auth_service, mock_password_service)

    with pytest.raises(ValueError, match="already registered"):
        await use_case.execute(
            RegisterUserDTO(email="test@example.com", password="securepass123")
        )


# ── Login tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(mock_user_repo, mock_password_service, mock_jwt_service, mock_token_repo, active_user):
    mock_user_repo.get_by_email.return_value = active_user
    mock_token_repo.save.return_value = MagicMock()

    auth_service = AuthDomainService(mock_user_repo, mock_password_service)
    use_case = LoginUseCase(auth_service, mock_jwt_service, mock_token_repo)

    result = await use_case.execute(LoginDTO(email="test@example.com", password="securepass123"))

    assert result.access_token == "access.token.here"
    assert result.refresh_token == "refresh.token.here"


@pytest.mark.asyncio
async def test_login_blocked_user(mock_user_repo, mock_password_service, mock_jwt_service, mock_token_repo):
    blocked_user = User(
        email="blocked@example.com",
        hashed_password="hashed",
        status=UserStatus.BLOCKED,
    )
    mock_user_repo.get_by_email.return_value = blocked_user

    auth_service = AuthDomainService(mock_user_repo, mock_password_service)
    use_case = LoginUseCase(auth_service, mock_jwt_service, mock_token_repo)

    with pytest.raises(PermissionError, match="blocked"):
        await use_case.execute(LoginDTO(email="blocked@example.com", password="pass"))


# ── Block user tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_block_user_success(mock_user_repo, mock_token_repo, active_user):
    mock_user_repo.get_by_id.return_value = active_user
    mock_user_repo.update.return_value = active_user

    use_case = BlockUserUseCase(mock_user_repo, mock_token_repo)
    result = await use_case.execute(BlockUserDTO(user_id=active_user.id, reason="Anomaly detected"))

    assert "blocked" in result.message.lower()
    mock_token_repo.revoke_all_by_user.assert_called_once_with(active_user.id)
