import pytest
from httpx import AsyncClient

VALID_RESERVATION = {
    "traveler_name": "Juan Perez",
    "traveler_email": "juan@example.com",
    "traveler_phone": "+573001234567",
    "traveler_document": "CC12345678",
    "destination": "Cartagena",
    "origin": "Bogota",
    "departure_date": "2026-06-15",
    "return_date": "2026-06-20",
    "num_passengers": 2,
}


@pytest.mark.asyncio
async def test_create_reservation(client: AsyncClient):
    response = await client.post("/api/v1/reservations/", json=VALID_RESERVATION)
    assert response.status_code == 201
    data = response.json()
    assert data["traveler_name"] == "Juan Perez"
    assert data["traveler_email"] == "juan@example.com"
    assert data["status"] == "PENDING"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_reservation(client: AsyncClient):
    create_resp = await client.post("/api/v1/reservations/", json=VALID_RESERVATION)
    reservation_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/reservations/{reservation_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == reservation_id
    assert data["traveler_name"] == "Juan Perez"


@pytest.mark.asyncio
async def test_get_reservation_not_found(client: AsyncClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/reservations/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_reservations(client: AsyncClient):
    for _ in range(3):
        await client.post("/api/v1/reservations/", json=VALID_RESERVATION)

    response = await client.get("/api/v1/reservations/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3


@pytest.mark.asyncio
async def test_list_reservations_pagination(client: AsyncClient):
    for _ in range(5):
        await client.post("/api/v1/reservations/", json=VALID_RESERVATION)

    response = await client.get("/api/v1/reservations/?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 5


@pytest.mark.asyncio
async def test_update_reservation(client: AsyncClient):
    create_resp = await client.post("/api/v1/reservations/", json=VALID_RESERVATION)
    reservation_id = create_resp.json()["id"]

    update_data = {"destination": "Santa Marta"}
    response = await client.put(
        f"/api/v1/reservations/{reservation_id}", json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["destination"] == "Santa Marta"
    assert data["status"] == "MODIFIED"


@pytest.mark.asyncio
async def test_update_cancelled_reservation_fails(client: AsyncClient):
    create_resp = await client.post("/api/v1/reservations/", json=VALID_RESERVATION)
    reservation_id = create_resp.json()["id"]

    await client.put(
        f"/api/v1/reservations/{reservation_id}",
        json={"status": "CANCELLED"},
    )

    response = await client.put(
        f"/api/v1/reservations/{reservation_id}",
        json={"destination": "Medellin"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_reservation_invalid_dates(client: AsyncClient):
    invalid = {**VALID_RESERVATION, "return_date": "2026-06-10"}
    response = await client.post("/api/v1/reservations/", json=invalid)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_reservation_validation_error(client: AsyncClient):
    response = await client.post("/api/v1/reservations/", json={})
    assert response.status_code == 422
