# reservas_ms

Microservicio de gestión de reservas construido con **FastAPI**, **PostgreSQL** y **arquitectura hexagonal** (Ports & Adapters).

Forma parte de un ecosistema de microservicios junto con:
- `login_handler_ms` — Autenticación JWT y control de acceso
- `detector_anomalias_ms` — Detección de patrones anómalos en reservas

---

## Arquitectura Hexagonal

```
src/
├── domain/                          ← Núcleo puro (sin dependencias externas)
│   ├── entities/
│   │   └── reserva.py               ← Entidad de dominio con reglas de negocio
│   ├── repositories/
│   │   └── reserva_repository_port.py  ← Puerto de salida (interfaz abstracta)
│   └── services/
│       └── reserva_domain_service.py   ← Lógica de negocio entre entidades
│
├── application/                     ← Casos de uso (orquestación)
│   ├── dtos/
│   │   └── reserva_dto.py           ← Objetos de transferencia de datos
│   └── use_cases/
│       └── crear_reserva.py         ← Puerto de entrada (driving port)
│
└── infrastructure/                  ← Adaptadores (implementaciones concretas)
    ├── config/
    │   └── settings.py              ← Configuración con pydantic-settings
    ├── database/
    │   ├── base.py                  ← Engine y sesión async SQLAlchemy
    │   ├── models/
    │   │   └── reserva_model.py     ← Modelo ORM
    │   └── repositories/
    │       └── sqlalchemy_reserva_repository.py  ← Adaptador de salida
    └── http/
        ├── routes/
        │   ├── reserva_router.py    ← Adaptador de entrada (HTTP)
        │   └── health_router.py     ← Health check
        └── schemas/
            └── reserva_schema.py   ← Esquemas Pydantic para HTTP
```

### Flujo de dependencias
```
HTTP Request
    → Router (adaptador de entrada)
        → CrearReservaUseCase (puerto de entrada / application)
            → Domain Entity + Domain Service (núcleo puro)
            → ReservaRepositoryPort (puerto de salida)
                → SQLAlchemyReservaRepository (adaptador de salida)
                    → PostgreSQL
```

---

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET`  | `/health` | Estado del servicio y dependencias |
| `POST` | `/api/v1/reservas/` | Crear nueva reserva |

---

## Quickstart

### 1. Con Docker Compose (recomendado)

```bash
cp .env.example .env
docker compose up --build
```

La API estará disponible en `http://localhost:8000`  
Documentación interactiva: `http://localhost:8000/docs`

### 2. Local

```bash
# Instalar dependencias
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configurar entorno
cp .env.example .env
# Editar .env con tus credenciales de PostgreSQL

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Ejemplo de uso

```bash
# Health check
curl http://localhost:8000/health

# Crear reserva
curl -X POST http://localhost:8000/api/v1/reservas/ \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": "123e4567-e89b-12d3-a456-426614174000",
    "recurso_id": "987fcdeb-51a2-43f7-b234-426614174111",
    "fecha_inicio": "2026-04-01T10:00:00",
    "fecha_fin": "2026-04-01T12:00:00",
    "notas": "Reunión de equipo Q2"
  }'
```

---

## Tests

```bash
pytest tests/ -v --cov=src
```

---

## Migraciones con Alembic

```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripcion_del_cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

---

## Integración con otros microservicios

### login_handler_ms
- Emitirá tokens JWT que `reservas_ms` validará (middleware por implementar).
- Si `detector_anomalias_ms` detecta anomalías, `login_handler_ms` bloqueará el usuario.

### detector_anomalias_ms
- `reservas_ms` enviará un evento/webhook al crear una reserva.
- El detector analiza patrones (frecuencia, horarios inusuales, recursos sospechosos).
- Si detecta anomalía → notifica a `login_handler_ms` para bloquear al usuario.

**Punto de extensión en `crear_reserva.py`:**
```python
# TODO: Integrar detector_anomalias_ms
# await anomalia_client.notificar(reserva_guardada)
```

---

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | URL de conexión a PostgreSQL |
| `DEBUG` | `false` | Modo debug |
| `JWT_SECRET_KEY` | `change-me` | Clave secreta JWT (compartir con login_handler_ms) |
| `LOGIN_HANDLER_MS_URL` | `http://login_handler_ms:8001` | URL del servicio de autenticación |
| `DETECTOR_ANOMALIAS_MS_URL` | `http://detector_anomalias_ms:8002` | URL del detector de anomalías |
