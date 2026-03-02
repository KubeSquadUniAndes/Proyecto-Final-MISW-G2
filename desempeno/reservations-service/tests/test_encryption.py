import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.database.connection import DatabaseManager

RESERVATION_DATA = {
    "traveler_name": "Maria Garcia",
    "traveler_email": "maria@example.com",
    "traveler_phone": "+573009876543",
    "traveler_document": "CC87654321",
    "destination": "Medellin",
    "origin": "Cali",
    "departure_date": "2026-07-01",
    "return_date": "2026-07-10",
    "num_passengers": 1,
}


@pytest.mark.asyncio
async def test_encrypted_fields_are_unintelligible(client: AsyncClient):
    """Verify that encrypted fields stored in DB are raw bytea and do not contain plaintext."""
    response = await client.post("/api/v1/reservations/", json=RESERVATION_DATA)
    assert response.status_code == 201
    reservation_id = response.json()["id"]

    factory = DatabaseManager.get_session_factory()
    async with factory() as session:
        result = await session.execute(
            text(
                "SELECT traveler_name, traveler_email, traveler_phone, traveler_document "
                "FROM reservations WHERE id = :id"
            ),
            {"id": reservation_id},
        )
        row = result.fetchone()

        assert row is not None

        for i, field_name in enumerate(
            ["traveler_name", "traveler_email", "traveler_phone", "traveler_document"]
        ):
            raw_value = row[i]
            assert isinstance(raw_value, (bytes, memoryview)), (
                f"{field_name} should be bytes, got {type(raw_value)}"
            )
            raw_bytes = bytes(raw_value)
            plaintext = RESERVATION_DATA[field_name].encode()
            assert plaintext not in raw_bytes, (
                f"{field_name} contains plaintext in encrypted storage"
            )


@pytest.mark.asyncio
async def test_decrypted_fields_match_original(client: AsyncClient):
    """Verify that decrypted fields via pgp_sym_decrypt match original values."""
    response = await client.post("/api/v1/reservations/", json=RESERVATION_DATA)
    assert response.status_code == 201
    data = response.json()

    assert data["traveler_name"] == RESERVATION_DATA["traveler_name"]
    assert data["traveler_email"] == RESERVATION_DATA["traveler_email"]
    assert data["traveler_phone"] == RESERVATION_DATA["traveler_phone"]
    assert data["traveler_document"] == RESERVATION_DATA["traveler_document"]
