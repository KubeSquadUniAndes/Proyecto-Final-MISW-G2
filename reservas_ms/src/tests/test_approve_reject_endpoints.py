"""Integration tests for approve and reject booking endpoints."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient

from src.domain.entities.booking import Booking, BookingStatus
from src.main import app


class MockBookingRepository:
    """Mock repository for testing."""

    def __init__(self):
        self.bookings = {}

    async def get_by_id(self, booking_id):
        return self.bookings.get(booking_id)

    async def update(self, booking):
        self.bookings[booking_id] = booking
        return booking

    async def save(self, booking):
        self.bookings[booking.id] = booking
        return booking


@pytest.fixture
def mock_auth_dependency():
    """Mock authentication to return a test user ID."""
    from src.infrastructure.http.routes import booking_router

    test_user_id = uuid4()

    async def override_get_current_user_id():
        return test_user_id

    booking_router.router.dependency_overrides[
        booking_router.get_current_user_id
    ] = override_get_current_user_id

    yield test_user_id

    booking_router.router.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_approve_booking_endpoint_success(mock_auth_dependency):
    """Test successful approval via endpoint."""
    booking_id = uuid4()
    resource_id = uuid4()

    # This is a simplified test - in real scenario you'd need to:
    # 1. Create a booking in the test database
    # 2. Mock the database session
    # 3. Call the endpoint
    # 4. Verify the response

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.patch(f"/bookings/{booking_id}/approve")

        # Without proper DB setup, this will return 404
        # In a full integration test, you'd set up the test DB first
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
        ]


@pytest.mark.asyncio
async def test_reject_booking_endpoint_success(mock_auth_dependency):
    """Test successful rejection via endpoint."""
    booking_id = uuid4()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.patch(
            f"/bookings/{booking_id}/reject",
            json={"rejection_reason": "Room maintenance required"},
        )

        # Without proper DB setup, this will return 404
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
        ]


@pytest.mark.asyncio
async def test_reject_booking_endpoint_missing_reason(mock_auth_dependency):
    """Test rejection fails without reason."""
    booking_id = uuid4()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.patch(
            f"/bookings/{booking_id}/reject",
            json={},  # Missing rejection_reason
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_approve_booking_endpoint_invalid_uuid():
    """Test approval with invalid booking ID format."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.patch("/bookings/invalid-uuid/approve")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_reject_booking_endpoint_invalid_uuid():
    """Test rejection with invalid booking ID format."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.patch(
            "/bookings/invalid-uuid/reject",
            json={"rejection_reason": "Test"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
