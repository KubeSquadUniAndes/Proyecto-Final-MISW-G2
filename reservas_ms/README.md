# reservas_ms

Bookings microservice built with **FastAPI**, **PostgreSQL**, and **hexagonal architecture** (Ports & Adapters).

Part of a microservices ecosystem alongside:
- `login_handler_ms` — JWT authentication and access control
- `detector_anomalias_ms` — Anomaly detection on booking patterns

---

## Hexagonal Architecture

```
src/
├── domain/                               ← Pure core (no external dependencies)
│   ├── entities/
│   │   └── booking.py                    ← Domain entity with business rules
│   ├── repositories/
│   │   └── booking_repository_port.py    ← Output port (abstract interface)
│   └── services/
│       └── booking_domain_service.py     ← Cross-entity business logic
│
├── application/                          ← Use cases (orchestration)
│   ├── dtos/
│   │   └── booking_dto.py               ← CreateBookingDTO, UpdateBookingDTO, BookingResponseDTO
│   └── use_cases/
│       ├── create_booking.py            ← Input port: create + anomaly check
│       └── update_booking.py            ← Input port: update dates/notes + anomaly check
│
└── infrastructure/                       ← Adapters (concrete implementations)
    ├── config/
    │   └── settings.py                  ← Configuration via pydantic-settings
    ├── clients/
    │   ├── login_handler_client.py      ← Output adapter: JWT validation + blocked status
    │   └── anomaly_detector_client.py   ← Output adapter: calls detector_anomalias_ms
    ├── database/
    │   ├── base.py                      ← Async SQLAlchemy engine & session
    │   ├── models/
    │   │   └── booking_model.py         ← ORM model
    │   └── repositories/
    │       └── sqlalchemy_booking_repository.py  ← Output adapter
    └── http/
        ├── middleware/
        │   └── auth_dependency.py       ← FastAPI dependency: validates JWT + blocked check
        ├── routes/
        │   ├── booking_router.py        ← Input adapter (HTTP): POST + PATCH
        │   └── health_router.py         ← Health check
        └── schemas/
            └── booking_schema.py        ← Pydantic HTTP schemas
```

### Dependency flow
```
HTTP Request (Bearer token)
    → auth_dependency (validate JWT + check user not blocked via login_handler_ms)
        → Router (input adapter)
            → CreateBookingUseCase / UpdateBookingUseCase (input port)
                → Domain Entity + BookingDomainService (pure core)
                → BookingRepositoryPort → SQLAlchemyBookingRepository → PostgreSQL
                → AnomalyDetectorClient → detector_anomalias_ms
```

---

## Endpoints

| Method  | Path                          | Auth        | Description                        |
|---------|-------------------------------|-------------|------------------------------------|
| `GET`   | `/health`                     | —           | Service and dependency status      |
| `POST`  | `/api/v1/bookings/`           | Bearer JWT  | Create a new booking               |
| `PATCH` | `/api/v1/bookings/{id}`       | Bearer JWT  | Update dates and/or notes          |

### Authentication & authorization
Every protected endpoint goes through two checks:

1. **Local JWT decode** — verifies signature and expiry using the shared `JWT_SECRET_KEY` (no HTTP call).
2. **Remote status check** — calls `login_handler_ms GET /api/v1/auth/me` to confirm the user is not blocked.

| Scenario | HTTP status |
|----------|-------------|
| Missing or malformed token | `401 Unauthorized` |
| Expired token | `401 Unauthorized` |
| User is blocked | `403 Forbidden` |
| login_handler_ms unreachable | `503 Service Unavailable` |
| Modifying another user's booking | `403 Forbidden` |

---

## Anomaly detection integration

After every `POST` and `PATCH`, `reservas_ms` calls `detector_anomalias_ms` in a **fire-and-forget** fashion:

```
reservas_ms ──POST /api/v1/analysis/booking──► detector_anomalias_ms
                X-Api-Key: DETECTOR_ANOMALIAS_MS_API_KEY

Response:
  { "is_anomalous": true, "action_taken": "user_blocked_and_alerted" }
       ↓
  reservas_ms logs a warning — the booking is already saved,
  but the user will be blocked for subsequent requests.
```

The anomaly call never blocks the booking response — if the detector is down, the error is logged and the booking proceeds normally.

---

## Quickstart

### 1. With Docker Compose (recommended)

```bash
cp .env.example .env
docker compose up --build
```

API available at `http://localhost:8000` | Docs: `http://localhost:8000/docs`

### 2. Local

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials

alembic init alembic   # first time only — replace alembic/env.py with the provided one
alembic upgrade head

uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Usage examples

```bash
# 1. Login first via login_handler_ms to get a token
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Create a booking (user_id comes from the token automatically)
curl -X POST http://localhost:8000/api/v1/bookings/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_id": "987fcdeb-51a2-43f7-b234-426614174111",
    "start_time": "2026-04-01T10:00:00",
    "end_time": "2026-04-01T12:00:00",
    "notes": "Q2 team meeting"
  }'

# 3. Update a booking
curl -X PATCH http://localhost:8000/api/v1/bookings/<booking_id> \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2026-04-01T11:00:00",
    "end_time": "2026-04-01T13:00:00",
    "notes": "Rescheduled"
  }'

# 4. Health check
curl http://localhost:8000/health
```

---

## Tests

```bash
pytest tests/ -v --cov=src
```

---

## Alembic migrations

```bash
alembic revision --autogenerate -m "description_of_change"
alembic upgrade head
alembic downgrade -1
```

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection URL |
| `DEBUG` | `false` | Debug mode |
| `JWT_SECRET_KEY` | `change-me` | JWT secret — **must match** `login_handler_ms` |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `LOGIN_HANDLER_MS_URL` | `http://login_handler_ms:8001` | Auth service URL (for blocked status check) |
| `DETECTOR_ANOMALIAS_MS_URL` | `http://detector_anomalias_ms:8002` | Anomaly detector URL |
| `DETECTOR_ANOMALIAS_MS_API_KEY` | `change-internal-key` | Internal API key for the detector |
