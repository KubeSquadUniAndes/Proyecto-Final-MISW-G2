from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.dtos.user_dto import RegisterUserDTO
from src.application.use_cases.register_user import RegisterUserUseCase
from src.domain.entities.user import User


def make_dto(**overrides) -> RegisterUserDTO:
    defaults = {
        "first_name": "Juan",
        "last_name": "Pérez",
        "email": "juan@example.com",
        "phone": "+57 300 123 4567",
        "country": "Colombia",
        "city": "Bogotá",
        "birth_date": date(1995, 6, 15),
        "password": "SecurePass123!",
    }
    defaults.update(overrides)
    return RegisterUserDTO(**defaults)


def make_user(dto: RegisterUserDTO) -> User:
    return User(
        id=uuid4(),
        first_name=dto.first_name,
        last_name=dto.last_name,
        email=dto.email,
        phone=dto.phone,
        country=dto.country,
        city=dto.city,
        birth_date=dto.birth_date,
        hashed_password="hashed_password",
    )


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.find_by_email.return_value = None
    return repo


@pytest.fixture
def mock_password_service():
    svc = MagicMock()
    svc.hash.return_value = "hashed_password"
    return svc


@pytest.fixture
def use_case(mock_repo, mock_password_service):
    return RegisterUserUseCase(
        user_repository=mock_repo,
        password_service=mock_password_service,
    )


@pytest.mark.asyncio
async def test_register_user_success(use_case, mock_repo, mock_password_service):
    dto = make_dto()
    saved_user = make_user(dto)
    mock_repo.save.return_value = saved_user

    result = await use_case.execute(dto)

    assert result.email == dto.email
    assert result.first_name == dto.first_name
    assert result.last_name == dto.last_name
    assert result.phone == dto.phone
    assert result.country == dto.country
    assert result.city == dto.city
    assert result.birth_date == dto.birth_date
    mock_password_service.hash.assert_called_once_with(dto.password)
    mock_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_email_already_taken(use_case, mock_repo):
    dto = make_dto()
    existing_user = make_user(dto)
    mock_repo.find_by_email.return_value = existing_user

    with pytest.raises(ValueError, match="already registered"):
        await use_case.execute(dto)

    mock_repo.save.assert_not_called()


@pytest.mark.asyncio
async def test_register_user_password_is_hashed(use_case, mock_repo, mock_password_service):
    dto = make_dto()
    mock_repo.save.return_value = make_user(dto)

    await use_case.execute(dto)

    mock_password_service.hash.assert_called_once_with("SecurePass123!")


def test_dto_birth_date_in_future_raises():
    with pytest.raises(Exception):
        make_dto(birth_date=date(2099, 1, 1))


def test_dto_invalid_email_raises():
    with pytest.raises(Exception):
        make_dto(email="not-an-email")


def test_dto_password_too_short_raises():
    with pytest.raises(Exception):
        make_dto(password="short")


def test_dto_phone_with_letters_raises():
    with pytest.raises(Exception):
        make_dto(phone="abc123")
