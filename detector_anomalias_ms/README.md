# detector_anomalias_ms

Anomaly detection microservice built with **FastAPI**, **PostgreSQL**, and **hexagonal architecture**.

Part of a microservices ecosystem alongside:
- `reservas_ms` — calls this service after every booking creation
- `login_handler_ms` — receives the block-user command when an anomaly is found

---

## How it works

```
reservas_ms  ──POST /api/v1/analysis/booking──►  detector_anomalias_ms
                                                        │
                                         ┌──────────────┼──────────────────┐
                                         ▼              ▼                  ▼
                                   Random sample   High frequency    Unusual duration
                                   (30% default)   (> 5 / 1h)        (< 15m or > 8h)
                                         │         Multi-resource
                                         │         (> 4 distinct / 1h)
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                     Persist AnomalyEvent    login_handler_ms
                     to PostgreSQL           POST /auth/block-user
                                                     │
                                             Send security alert
                                             email via SMTP
```

---

## Anomaly detection rules

| Rule | Trigger | Score |
|------|---------|-------|
| **Random sample** | Configurable rate (default 30%) | 0.6 – 0.9 random |
| **High frequency** | > 5 bookings in last 1h | proportional to count |
| **Unusual duration** | < 15 min or > 8h | proportional to deviation |
| **Multi-resource** | > 4 different resources in last 1h | proportional to count |

All thresholds are configurable via environment variables.

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET`  | `/health` | — | Service health check |
| `POST` | `/api/v1/analysis/booking` | `X-Api-Key` | Analyze a booking for anomalies |

---

## Quickstart

```bash
cp .env.example .env
alembic init alembic   # first time only — replace env.py with provided one
alembic upgrade head
uvicorn src.main:app --reload --port 8002
```

---

## Usage example

```bash
curl -X POST http://localhost:8002/api/v1/analysis/booking \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: change-internal-key-in-production" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "booking_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "resource_id": "987fcdeb-51a2-43f7-b234-426614174111",
    "start_time": "2026-04-01T10:00:00",
    "end_time": "2026-04-01T12:00:00"
  }'
```

**Clean response:**
```json
{ "is_anomalous": false, "anomaly_count": 0, "action_taken": "none" }
```

**Anomalous response:**
```json
{
  "is_anomalous": true,
  "anomaly_count": 1,
  "action_taken": "user_blocked_and_alerted",
  "events": [{ "anomaly_type": "random_sample", "severity": "medium", "score": 0.73 }]
}
```

---

## Tuning the random rate

Set `RANDOM_ANOMALY_RATE` in `.env`:
- `0.0` → never triggers randomly (only heuristic rules)
- `0.30` → 30% of requests flagged (default for testing)
- `1.0` → every request flagged (useful for integration tests)

---

## Tests

```bash
pytest tests/ -v --cov=src
```

---

## Integration: wiring reservas_ms

Add this call in `reservas_ms/src/application/use_cases/create_booking.py` after saving:

```python
# After: saved_booking = await self._repo.save(booking)
await anomaly_client.post("/api/v1/analysis/booking", json={
    "user_id": str(saved_booking.user_id),
    "booking_id": str(saved_booking.id),
    "resource_id": str(saved_booking.resource_id),
    "start_time": saved_booking.start_time.isoformat(),
    "end_time": saved_booking.end_time.isoformat(),
}, headers={"X-Api-Key": settings.DETECTOR_ANOMALIAS_MS_API_KEY})
```
