"""Infrastructure layer tests for reservas_ms."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient, ASGITransport

from src.infrastructure.config.settings import Settings
from src.infrastructure.http.schemas.booking_schema import (
    CreateBookingRequest,
    ErrorResponse,
)
from src.domain.entities.booking import Booking, BookingStatus
from src.domain.services.booking_domain_service import BookingDomainService


# ── Settings ──────────────────────────────────────────────────────────────────


def test_settings_defaults():
    s = Settings(DATABASE_URL="postgresql+asyncpg://x:x@localhost/x")
    assert s.APP_NAME == "reservas_ms"
    assert s.PORT == 8000


def test_settings_override():
    s = Settings(DATABASE_URL="postgresql+asyncpg://x:x@localhost/x", DEBUG=True)
    assert s.DEBUG is True


# ── Booking entity ────────────────────────────────────────────────────────────


def test_booking_confirm():
    now = datetime.utcnow()
    b = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=now,
        end_time=now + timedelta(hours=1),
    )
    b.confirm()
    assert b.status == BookingStatus.CONFIRMED


def test_booking_confirm_not_pending():
    now = datetime.utcnow()
    b = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=now,
        end_time=now + timedelta(hours=1),
        status=BookingStatus.CONFIRMED,
    )
    with pytest.raises(ValueError):
        b.confirm()


def test_booking_cancel():
    now = datetime.utcnow()
    b = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=now,
        end_time=now + timedelta(hours=1),
    )
    b.cancel()
    assert b.status == BookingStatus.CANCELLED


def test_booking_cancel_already_cancelled():
    now = datetime.utcnow()
    b = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=now,
        end_time=now + timedelta(hours=1),
        status=BookingStatus.CANCELLED,
    )
    with pytest.raises(ValueError):
        b.cancel()


def test_booking_complete():
    now = datetime.utcnow()
    b = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=now,
        end_time=now + timedelta(hours=1),
        status=BookingStatus.CONFIRMED,
    )
    b.complete()
    assert b.status == BookingStatus.COMPLETED


def test_booking_complete_not_confirmed():
    now = datetime.utcnow()
    b = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=now,
        end_time=now + timedelta(hours=1),
    )
    with pytest.raises(ValueError):
        b.complete()


def test_booking_is_valid():
    now = datetime.utcnow()
    b = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=now,
        end_time=now + timedelta(hours=1),
    )
    assert b.is_valid() is True


def test_booking_is_invalid():
    now = datetime.utcnow()
    b = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=now + timedelta(hours=1),
        end_time=now,
    )
    assert b.is_valid() is False


# ── BookingDomainService ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_conflict_different_resource():
    now = datetime.utcnow()
    uid = uuid4()
    rid1 = uuid4()
    rid2 = uuid4()
    existing = Booking(
        user_id=uid, hotel_id=uuid4(), room_id=rid1, start_time=now, end_time=now + timedelta(hours=2)
    )
    mock_repo = AsyncMock()
    mock_repo.list_by_user.return_value = [existing]
    svc = BookingDomainService(mock_repo)
    conflict = await svc.has_schedule_conflict(uid, rid2, now, now + timedelta(hours=2))
    assert conflict is False


@pytest.mark.asyncio
async def test_conflict_same_resource():
    now = datetime.utcnow()
    uid = uuid4()
    rid = uuid4()
    existing = Booking(
        user_id=uid, hotel_id=uuid4(), room_id=rid, start_time=now, end_time=now + timedelta(hours=2)
    )
    mock_repo = AsyncMock()
    mock_repo.list_by_user.return_value = [existing]
    svc = BookingDomainService(mock_repo)
    conflict = await svc.has_schedule_conflict(
        uid, rid, now + timedelta(hours=1), now + timedelta(hours=3)
    )
    assert conflict is True


@pytest.mark.asyncio
async def test_no_conflict_cancelled_booking():
    now = datetime.utcnow()
    uid = uuid4()
    rid = uuid4()
    existing = Booking(
        user_id=uid,
        hotel_id=uuid4(),
        room_id=rid,
        start_time=now,
        end_time=now + timedelta(hours=2),
        status=BookingStatus.CANCELLED,
    )
    mock_repo = AsyncMock()
    mock_repo.list_by_user.return_value = [existing]
    svc = BookingDomainService(mock_repo)
    conflict = await svc.has_schedule_conflict(uid, rid, now, now + timedelta(hours=2))
    assert conflict is False


# ── SQLAlchemy Booking Repository ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_booking_repo_get_by_id_not_found():
    from src.infrastructure.database.repositories.sqlalchemy_booking_repository import (
        SQLAlchemyBookingRepository,
    )

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    repo = SQLAlchemyBookingRepository(mock_session)
    result = await repo.get_by_id(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_booking_repo_list_by_user_empty():
    from src.infrastructure.database.repositories.sqlalchemy_booking_repository import (
        SQLAlchemyBookingRepository,
    )

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)
    repo = SQLAlchemyBookingRepository(mock_session)
    result = await repo.list_by_user(uuid4())
    assert result == []


@pytest.mark.asyncio
async def test_booking_repo_delete_not_found():
    from src.infrastructure.database.repositories.sqlalchemy_booking_repository import (
        SQLAlchemyBookingRepository,
    )

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    repo = SQLAlchemyBookingRepository(mock_session)
    result = await repo.delete(uuid4())
    assert result is False


@pytest.mark.asyncio
async def test_booking_repo_update_not_found():
    from src.infrastructure.database.repositories.sqlalchemy_booking_repository import (
        SQLAlchemyBookingRepository,
    )

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    repo = SQLAlchemyBookingRepository(mock_session)
    now = datetime.utcnow()
    booking = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=now,
        end_time=now + timedelta(hours=1),
    )
    with pytest.raises(ValueError):
        await repo.update(booking)


# ── Schemas ───────────────────────────────────────────────────────────────────


def test_create_booking_request_valid():
    now = datetime.utcnow()
    r = CreateBookingRequest(
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=now,
        end_time=now + timedelta(days=2),
    )
    assert r.end_time > r.start_time


def test_create_booking_request_invalid():
    now = datetime.utcnow()
    with pytest.raises(Exception):
        CreateBookingRequest(
            resource_id=uuid4(),
            start_time=now + timedelta(days=2),
            end_time=now,
        )


def test_error_response():
    e = ErrorResponse(detail="conflict")
    assert e.detail == "conflict"


# ── HTTP Router ───────────────────────────────────────────────────────────────


def _make_app():
    with (
        patch("src.infrastructure.database.base.create_async_engine") as mock_engine,
        patch("src.infrastructure.database.base.async_sessionmaker"),
        patch("src.infrastructure.http.routes.booking_router.AnomalyDetectorClient"),
    ):
        mock_engine.return_value = MagicMock()
        from src.main import create_app

        return create_app()


@pytest.fixture
def app():
    return _make_app()


@pytest.mark.asyncio
async def test_health_endpoint(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_booking_no_auth(app):
    now = datetime.utcnow()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/v1/bookings/",
            json={
                "resource_id": str(uuid4()),
                "start_time": now.isoformat(),
                "end_time": (now + timedelta(hours=1)).isoformat(),
            },
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_booking_success(app):
    from src.application.dtos.booking_dto import BookingResponseDTO

    now = datetime.utcnow()
    uid = uuid4()
    mock_result = BookingResponseDTO(
        id=uuid4(),
        user_id=uid,
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=now,
        end_time=now + timedelta(days=2),
        status=BookingStatus.PENDING,
        status_display="Pendiente de pago",
        notes=None,
        booking_code="TH-2026-TEST1",
        room_type=None,
        num_guests=1,
        additional_guests=None,
        special_requests=None,
        price_per_night=None,
        total_nights=None,
        total_price=None,
        taxes=None,
        final_price=None,
        traveler_name=None,
        traveler_email=None,
        traveler_phone=None,
        traveler_document=None,
        cancellable=True,
        created_at=now,
        updated_at=now,
    )
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with (
        patch(
            "src.infrastructure.database.base.AsyncSessionLocal",
            return_value=mock_session,
        ),
        patch(
            "src.infrastructure.http.middleware.auth_dependency._login_client"
        ) as mock_client,
        patch(
            "src.infrastructure.http.routes.booking_router.CreateBookingUseCase"
        ) as MockUC,
    ):
        mock_client.validate = AsyncMock(return_value=uid)
        mock_uc = AsyncMock()
        mock_uc.execute.return_value = mock_result
        MockUC.return_value = mock_uc

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/bookings/",
                json={
                    "hotel_id": str(uuid4()),
                    "room_id": str(uuid4()),
                    "start_time": now.isoformat(),
                    "end_time": (now + timedelta(hours=1)).isoformat(),
                },
                headers={"Authorization": "Bearer fake.jwt.token"},
            )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_booking_conflict(app):
    now = datetime.utcnow()
    uid = uuid4()
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with (
        patch(
            "src.infrastructure.database.base.AsyncSessionLocal",
            return_value=mock_session,
        ),
        patch(
            "src.infrastructure.http.middleware.auth_dependency._login_client"
        ) as mock_client,
        patch(
            "src.infrastructure.http.routes.booking_router.CreateBookingUseCase"
        ) as MockUC,
    ):
        mock_client.validate = AsyncMock(return_value=uid)
        mock_uc = AsyncMock()
        mock_uc.execute.side_effect = ValueError("schedule conflict")
        MockUC.return_value = mock_uc

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/bookings/",
                json={
                    "hotel_id": str(uuid4()),
                    "room_id": str(uuid4()),
                    "start_time": now.isoformat(),
                    "end_time": (now + timedelta(hours=1)).isoformat(),
                },
                headers={"Authorization": "Bearer fake.jwt.token"},
            )
    assert resp.status_code == 409
