"""Tests for hospedajes_ms."""
import os
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.entities.room import Room, RoomStatus, RoomType
from src.infrastructure.config.settings import Settings
from src.infrastructure.http.schemas.room_schema import (
    CreateRoomRequest,
    UpdateRoomRequest,
)
from src.infrastructure.security.jwt_service import JWTService


# ── Settings ──────────────────────────────────────────────────────────────────

def test_settings_defaults():
    s = Settings(DATABASE_URL="postgresql+asyncpg://x:x@localhost/x")
    assert s.APP_NAME == "hospedajes_ms"
    assert s.JWT_ALGORITHM == "HS256"


# ── Room entity ───────────────────────────────────────────────────────────────

def _make_room(**kwargs) -> Room:
    defaults = dict(
        name="Room 101",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("100.00"),
        capacity=2,
        beds="1 cama doble",
        size=25.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi, AC",
    )
    defaults.update(kwargs)
    return Room(**defaults)


def test_room_is_available():
    room = _make_room(status=RoomStatus.DISPONIBLE)
    assert room.is_available() is True


def test_room_mark_occupied():
    room = _make_room()
    room.mark_occupied()
    assert room.status == RoomStatus.OCUPADA
    assert room.is_available() is False


def test_room_mark_maintenance():
    room = _make_room()
    room.mark_maintenance()
    assert room.status == RoomStatus.MANTENIMIENTO


def test_room_mark_available():
    room = _make_room(status=RoomStatus.OCUPADA)
    room.mark_available()
    assert room.is_available() is True


# ── Schemas ───────────────────────────────────────────────────────────────────

def test_create_room_request_valid():
    r = CreateRoomRequest(
        name="Suite 1",
        room_type=RoomType.SUITE,
        price=Decimal("250.00"),
        capacity=4,
        beds="2 camas dobles",
        size=50.0,
        amenities="WiFi, AC, Jacuzzi",
    )
    assert r.room_type == RoomType.SUITE


def test_create_room_request_invalid_price():
    with pytest.raises(Exception):
        CreateRoomRequest(
            name="Room",
            room_type=RoomType.INDIVIDUAL,
            price=Decimal("-10"),
            capacity=1,
            beds="1 cama",
            size=20.0,
            amenities="WiFi",
        )


def test_create_room_request_invalid_capacity():
    with pytest.raises(Exception):
        CreateRoomRequest(
            name="Room",
            room_type=RoomType.INDIVIDUAL,
            price=Decimal("50"),
            capacity=0,
            beds="1 cama",
            size=20.0,
            amenities="WiFi",
        )


def test_update_room_request_partial():
    r = UpdateRoomRequest(status=RoomStatus.MANTENIMIENTO)
    assert r.status == RoomStatus.MANTENIMIENTO
    assert r.name is None


# ── Use cases ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_room_use_case():
    from src.application.dtos.room_dto import CreateRoomDTO
    from src.application.use_cases.create_room import CreateRoomUseCase

    saved_room = _make_room()
    mock_repo = AsyncMock()
    mock_repo.save.return_value = saved_room

    uc = CreateRoomUseCase(mock_repo)
    dto = CreateRoomDTO(
        name="Room 101",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("100.00"),
        capacity=2,
        beds="1 cama doble",
        size=25.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi",
    )
    result = await uc.execute(dto)
    assert result.name == "Room 101"
    mock_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_get_room_use_case_not_found():
    from src.application.use_cases.get_room import GetRoomUseCase

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    uc = GetRoomUseCase(mock_repo)
    with pytest.raises(ValueError, match="not found"):
        await uc.execute(uuid4())


@pytest.mark.asyncio
async def test_list_rooms_use_case():
    from src.application.use_cases.list_rooms import ListRoomsUseCase

    rooms = [_make_room(name=f"Room {i}") for i in range(3)]
    mock_repo = AsyncMock()
    mock_repo.list_all.return_value = rooms

    uc = ListRoomsUseCase(mock_repo)
    results = await uc.execute()
    assert len(results) == 3


@pytest.mark.asyncio
async def test_get_room_stats_use_case():
    from src.application.use_cases.get_room_stats import GetRoomStatsUseCase

    mock_repo = AsyncMock()
    mock_repo.count_total.return_value = 10
    mock_repo.count_by_status.side_effect = lambda s: {
        RoomStatus.DISPONIBLE: 5,
        RoomStatus.OCUPADA: 3,
        RoomStatus.MANTENIMIENTO: 2,
    }[s]

    uc = GetRoomStatsUseCase(mock_repo)
    result = await uc.execute()
    assert result.total == 10
    assert result.disponibles == 5
    assert result.ocupadas == 3
    assert result.mantenimiento == 2


@pytest.mark.asyncio
async def test_delete_room_use_case_not_found():
    from src.application.use_cases.delete_room import DeleteRoomUseCase

    mock_repo = AsyncMock()
    mock_repo.delete.return_value = False

    uc = DeleteRoomUseCase(mock_repo)
    with pytest.raises(ValueError, match="not found"):
        await uc.execute(uuid4())


# ── HTTP endpoints ────────────────────────────────────────────────────────────

def _make_app():
    with patch("src.infrastructure.database.base.create_async_engine") as mock_engine, \
         patch("src.infrastructure.database.base.async_sessionmaker"):
        mock_engine.return_value = MagicMock()
        from src.main import create_app
        return create_app()


@pytest.fixture
def app():
    return _make_app()


def _valid_token() -> str:
    """Generate a real JWT with hotel role for testing."""
    import jwt as pyjwt
    from datetime import timedelta
    payload = {
        "sub": str(uuid4()),
        "type": "access",
        "role": "hotel",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    return pyjwt.encode(payload, "change-me-in-production", algorithm="HS256")


@pytest.mark.asyncio
async def test_health_endpoint(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_rooms_no_token(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/rooms")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_room_success(app):
    from src.application.dtos.room_dto import RoomResponseDTO

    mock_result = RoomResponseDTO(
        id=uuid4(),
        name="Suite 1",
        room_type=RoomType.SUITE,
        price=Decimal("250.00"),
        capacity=4,
        beds="2 camas dobles",
        size=50.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi, AC",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.infrastructure.database.base.AsyncSessionLocal", return_value=mock_session), \
         patch("src.infrastructure.http.routes.room_router.CreateRoomUseCase") as MockUC:
        mock_uc = AsyncMock()
        mock_uc.execute.return_value = mock_result
        MockUC.return_value = mock_uc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/rooms",
                json={
                    "name": "Suite 1",
                    "room_type": "suite",
                    "price": "250.00",
                    "capacity": 4,
                    "beds": "2 camas dobles",
                    "size": 50.0,
                    "amenities": "WiFi, AC",
                },
                headers={"Authorization": f"Bearer {_valid_token()}"},
            )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_room_wrong_role(app):
    import jwt as pyjwt
    from datetime import timedelta

    token = pyjwt.encode(
        {
            "sub": str(uuid4()),
            "type": "access",
            "role": "traveler",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
        },
        "change-me-in-production",
        algorithm="HS256",
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/rooms",
            json={
                "name": "Room",
                "room_type": "individual",
                "price": "100.00",
                "capacity": 2,
                "beds": "1 cama",
                "size": 25.0,
                "amenities": "WiFi",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_room_not_found(app):
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.infrastructure.database.base.AsyncSessionLocal", return_value=mock_session), \
         patch("src.infrastructure.http.routes.room_router.GetRoomUseCase") as MockUC:
        mock_uc = AsyncMock()
        mock_uc.execute.side_effect = ValueError("Room not found")
        MockUC.return_value = mock_uc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/v1/rooms/{uuid4()}",
                headers={"Authorization": f"Bearer {_valid_token()}"},
            )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_stats_success(app):
    from src.application.dtos.room_dto import RoomStatsDTO

    mock_result = RoomStatsDTO(total=10, disponibles=5, ocupadas=3, mantenimiento=2)
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.infrastructure.database.base.AsyncSessionLocal", return_value=mock_session), \
         patch("src.infrastructure.http.routes.room_router.GetRoomStatsUseCase") as MockUC:
        mock_uc = AsyncMock()
        mock_uc.execute.return_value = mock_result
        MockUC.return_value = mock_uc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/rooms/stats",
                headers={"Authorization": f"Bearer {_valid_token()}"},
            )
    assert resp.status_code == 200
    assert resp.json()["total"] == 10
