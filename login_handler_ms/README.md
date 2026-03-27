# login_handler_ms

JWT Authentication microservice built with **FastAPI**, **PostgreSQL**, and **hexagonal architecture** (Ports & Adapters).

Part of a microservices ecosystem alongside:
- `reservas_ms` — Bookings management
- `detector_anomalias_ms` — Anomaly detection (calls `/auth/block-user` on anomaly)

---

## Hexagonal Architecture

```
src/
├── domain/                                        ← Pure core (no external dependencies)
│   ├── entities/
│   │   ├── user.py                                ← User entity (active/blocked/inactive)
│   │   └── refresh_token.py                       ← RefreshToken entity
│   ├── repositories/
│   │   ├── user_repository_port.py                ← Output port
│   │   └── refresh_token_repository_port.py       ← Output port
│   └── services/
│       ├── auth_domain_service.py                 ← Authentication business rules
│       └── password_service_port.py               ← Output port (hashing abstraction)
│
├── application/                                   ← Use cases (orchestration)
│   ├── dtos/
│   │   ├── auth_dto.py                            ← Request/Response DTOs
│   │   └── jwt_service_port.py                    ← Output port (JWT abstraction)
│   └── use_cases/
│       ├── register_user.py
│       ├── login.py
│       ├── logout.py
│       ├── refresh_token.py
│       ├── get_me.py
│       └── block_user.py                          ← Called by detector_anomalias_ms
│
└── infrastructure/                                ← Adapters
    ├── config/settings.py
    ├── security/
    │   ├── bcrypt_password_service.py             ← Output adapter (bcrypt)
    │   └── jwt_service.py                         ← Output adapter (PyJWT)
    ├── database/
    │   ├── base.py
    │   ├── models/user_model.py
    │   ├── models/refresh_token_model.py
    │   └── repositories/
    │       ├── sqlalchemy_user_repository.py
    │       └── sqlalchemy_refresh_token_repository.py
    └── http/
        ├── dependencies.py                        ← JWT extraction + internal API key guard
        ├── routes/auth_router.py                  ← All auth endpoints
        ├── routes/health_router.py
        └── schemas/auth_schema.py
```

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET`  | `/health` | — | Service health check |
| `POST` | `/api/v1/auth/register` | — | Register a new user |
| `POST` | `/api/v1/auth/login` | — | Login, get JWT tokens |
| `POST` | `/api/v1/auth/logout` | — | Logout, revoke refresh token |
| `POST` | `/api/v1/auth/refresh-token` | — | Rotate token pair |
| `GET`  | `/api/v1/auth/me` | Bearer JWT | Get current user profile |
| `POST` | `/api/v1/auth/block-user` | `X-Api-Key` | Block user + revoke sessions |

> `/block-user` is protected by an internal API key (`X-Api-Key` header), meant for machine-to-machine calls from `detector_anomalias_ms`.

---

## Quickstart

### 1. With Docker Compose

```bash
# First, make sure the shared network exists (created by reservas_ms)
docker network create experiment_net

cp .env.example .env
docker compose up --build
```

API: `http://localhost:8001` | Docs: `http://localhost:8001/docs`

### 2. Local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — use port 5433 to avoid conflict with reservas_ms DB

alembic init alembic   # only first time
# Replace alembic/env.py with the provided one
alembic upgrade head

uvicorn src.main:app --reload --port 8001
```

---

## Usage examples

```bash
# Register
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123", "full_name": "John Doe"}'

# Login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}'

# Get profile
curl http://localhost:8001/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"

# Block user (called by detector_anomalias_ms)
curl -X POST http://localhost:8001/api/v1/auth/block-user \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: change-internal-key-in-production" \
  -d '{"user_id": "<uuid>", "reason": "Anomalous booking pattern detected"}'
```

---

## Tests

```bash
pytest tests/ -v --cov=src
```

---

## Integration with other microservices

### reservas_ms
Share the same `JWT_SECRET_KEY` so `reservas_ms` can validate tokens issued here without making an HTTP call.

### detector_anomalias_ms
When an anomaly is detected, it calls:
```
POST /api/v1/auth/block-user
X-Api-Key: <INTERNAL_API_KEY>
{ "user_id": "...", "reason": "Anomalous booking pattern" }
```
This blocks the user and immediately revokes all their active sessions.
