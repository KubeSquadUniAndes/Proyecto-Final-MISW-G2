# Copilot Instructions — TravelHub Microservices

## Project Overview

TravelHub is a Python microservices platform using **FastAPI + PostgreSQL + Istio on EKS**. Each microservice is a self-contained directory with its own dependencies, tests, and Docker image.

**Microservices:**
| Directory | Image name | Port | Role |
|---|---|---|---|
| `users_ms` | `usersms` | 8004 | User registration |
| `login_handler_ms` | `loginhandlerms` | 8000 | JWT auth, session management |
| `reservas_ms` | `reservasms` | — | Bookings |
| `hospedajes_ms` | `hospedajesms` | — | Accommodations |
| `detector_anomalias_ms` | `detectoranomaliasms` | — | Anomaly detection |
| `notificaciones_ms` | `notificacionesms` | — | Notifications |
| `pagos_ms` | `pagosms` | — | Payments |

---

## Hexagonal Architecture (Ports & Adapters)

Every microservice follows the same internal layout:

```
src/
├── domain/           # Pure Python — no framework imports
│   ├── entities/     # Dataclass-based domain objects
│   ├── repositories/ # Abstract port interfaces (ABCs)
│   └── services/     # Cross-entity business logic
├── application/
│   ├── dtos/         # Pydantic input/output DTOs
│   └── use_cases/    # One class per use case; injected with ports
└── infrastructure/   # All concrete adapters
    ├── config/       # pydantic-settings Settings class
    ├── clients/      # HTTP clients to other microservices
    ├── database/     # Async SQLAlchemy engine, ORM models, repository impls
    └── http/
        ├── middleware/  # FastAPI dependencies (e.g., JWT validation)
        ├── routes/      # Input adapters (FastAPI routers)
        └── schemas/     # Pydantic HTTP schemas (separate from DTOs)
```

**Dependency flow:** `HTTP route → auth middleware → use case → domain → repository port ← SQLAlchemy impl`

**Key rule:** `domain/` must never import from `application/` or `infrastructure/`. Use cases depend on ports (interfaces), not implementations.

---

## Inter-Service Communication

Services call each other via HTTP clients in `infrastructure/clients/`:

- `reservas_ms` → `detector_anomalias_ms` (POST `/analysis/bookings`) after every booking
- `detector_anomalias_ms` → `login_handler_ms` (POST `/auth/block-user`) on anomaly detection
- `users_ms` → `login_handler_ms` (internal endpoint) to register credentials

Internal service calls use `INTERNAL_API_KEY` header for authorization.

---

## Development Setup

**Python environment (use `uv`, Python 3.12):**
```bash
uv venv
uv pip install -r <service_dir>/requirements.txt
```

**Run a service locally:**
```bash
cd <service_dir>
PYTHONPATH=. uv run uvicorn src.main:app --reload
```

**Local Postgres:**
```bash
docker run --name pg-local -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=postgres -p 5432:5432 -d postgres
```

**Config** is loaded from a `.env` file at the repo root via `pydantic-settings`. All settings have defaults that work locally; override via environment variables.

---

## Commands (run from inside the microservice directory)

**Lint:**
```bash
python -m ruff check src
python -m ruff format --check src
```

**Type check:**
```bash
python -m mypy src/domain src/application --explicit-package-bases
```

**Security scan:**
```bash
python -m bandit -r src -ll -q
python -m pip_audit -r requirements.txt --skip-editable
```

**Run all unit tests (80% coverage required):**
```bash
PYTHONPATH=. python -m pytest tests/ --ignore=tests/test_infrastructure.py \
  --cov=src/domain --cov=src/application --cov-report=term-missing -v
```

**Run a single test:**
```bash
PYTHONPATH=. python -m pytest tests/test_register_user.py::test_register_user_success -v
```

> `PYTHONPATH` must be set to the microservice root, not the repo root.  
> `tests/test_infrastructure.py` is excluded because it requires a live DB.

**E2E tests (requires deployed EKS cluster):**
```bash
newman run postman/travelhub-collection.json -e postman/travelhub-environment.json
```

---

## Key Conventions

### Domain entities
- Use Python `@dataclass`, not Pydantic or SQLAlchemy models.
- Enums inherit from `str, Enum` for JSON serialization.
- IDs are `UUID` with `uuid4()` default.

### Testing
- Unit tests mock repository ports using `AsyncMock` (for async repos) and `MagicMock` (for sync services).
- Test the **use case** class directly — not routes, not infrastructure.
- DTO validation errors (Pydantic) are tested with `pytest.raises(Exception)`.
- Fixture pattern: build `make_dto(**overrides)` helpers so individual test overrides are minimal.

### Settings
- Each service has `src/infrastructure/config/settings.py` with a `Settings(BaseSettings)` class and a module-level `settings = Settings()` singleton.
- Add new config values there with defaults; override via `.env` or environment variables.

### Database migrations
- Use Alembic; `alembic.ini` is in each microservice root.
- DB tables are also created at startup via `Base.metadata.create_all` (for development convenience).

### Docker images
- Always build with `--platform linux/amd64` for EKS compatibility:
  ```bash
  docker build --rm --no-cache --platform linux/amd64 -t <imagename>:latest .
  ```
- ECR repository: `780522923809.dkr.ecr.us-east-1.amazonaws.com/travelhub/<imagename>:latest`

---

## Kubernetes / Istio

**Cluster:** AWS EKS `travelhub-eks` / `travelhub-prod` in `us-east-1`, Istio in **ambient mode**.

**K8s manifests** are in `k8s/` (numbered for ordered `kubectl apply -f k8s/`).

**Critical Istio ordering rule** (prevents HTTP 503):
- When **adding** subsets: apply `DestinationRule` first, wait, then apply `VirtualService`.
- When **removing** subsets: update `VirtualService` first, wait, then update `DestinationRule`.

**Configure kubectl for EKS:**
```bash
aws eks update-kubeconfig --region us-east-1 --name travelhub-prod
```

**Infrastructure provisioning** (Terraform):
```bash
cd terraform/envs/prod
cp terraform.tfvars.example terraform.tfvars  # fill in db_password
terraform init && ./tf-apply.sh
```

---

## CI/CD (GitHub Actions)

`.github/workflows/ci.yml` runs a matrix job per microservice on push/PR to `main`, `develop`, `feature/**`, `hotfix/**`:

1. `ruff check` + `ruff format --check`
2. `mypy` (domain + application layers only)
3. `bandit` SAST
4. `pip-audit` dependency scan
5. `pytest` with 80% coverage gate

E2E (Newman) runs only on push to `main` and requires the `EKS_BASE_URL` secret.
