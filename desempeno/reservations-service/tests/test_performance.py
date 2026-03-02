import time

import pytest
from httpx import AsyncClient

RESERVATION_DATA = {
    "traveler_name": "Carlos Lopez",
    "traveler_email": "carlos@example.com",
    "traveler_phone": "+573005551234",
    "traveler_document": "CC11223344",
    "destination": "Barranquilla",
    "origin": "Bogota",
    "departure_date": "2026-08-01",
    "return_date": "2026-08-05",
    "num_passengers": 3,
}

PERFORMANCE_THRESHOLD = 1.5  # seconds


@pytest.mark.asyncio
async def test_create_reservation_performance(client: AsyncClient):
    start = time.perf_counter()
    response = await client.post("/api/v1/reservations/", json=RESERVATION_DATA)
    elapsed = time.perf_counter() - start

    assert response.status_code == 201
    assert elapsed < PERFORMANCE_THRESHOLD, (
        f"POST response time {elapsed:.3f}s exceeds {PERFORMANCE_THRESHOLD}s"
    )


@pytest.mark.asyncio
async def test_get_reservation_performance(client: AsyncClient):
    create_resp = await client.post("/api/v1/reservations/", json=RESERVATION_DATA)
    reservation_id = create_resp.json()["id"]

    start = time.perf_counter()
    response = await client.get(f"/api/v1/reservations/{reservation_id}")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert elapsed < PERFORMANCE_THRESHOLD, (
        f"GET response time {elapsed:.3f}s exceeds {PERFORMANCE_THRESHOLD}s"
    )


@pytest.mark.asyncio
async def test_list_reservations_performance(client: AsyncClient):
    for _ in range(50):
        await client.post("/api/v1/reservations/", json=RESERVATION_DATA)

    start = time.perf_counter()
    response = await client.get("/api/v1/reservations/?limit=50")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert elapsed < PERFORMANCE_THRESHOLD, (
        f"LIST response time {elapsed:.3f}s exceeds {PERFORMANCE_THRESHOLD}s"
    )


@pytest.mark.asyncio
async def test_update_reservation_performance(client: AsyncClient):
    create_resp = await client.post("/api/v1/reservations/", json=RESERVATION_DATA)
    reservation_id = create_resp.json()["id"]

    start = time.perf_counter()
    response = await client.put(
        f"/api/v1/reservations/{reservation_id}",
        json={"destination": "Pereira"},
    )
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert elapsed < PERFORMANCE_THRESHOLD, (
        f"PUT response time {elapsed:.3f}s exceeds {PERFORMANCE_THRESHOLD}s"
    )
