# Pagos MS - Payment Microservice

Microservicio de pagos con arquitectura hexagonal para TravelHub.

## Características

- ✅ Confirmación de pago con actualización de estado de reserva
- ✅ Lógica de retry automático (máximo 3 intentos)
- ✅ Tiempo de respuesta < 500ms
- ✅ Encriptación AES-256 con pgcrypto para datos sensibles
- ✅ Registro de auditoría completo
- ✅ Alertas para revisión manual en caso de fallo
- ✅ Integración con reservas_ms y notificaciones_ms

## Arquitectura Hexagonal

```
src/
├── domain/              # Lógica de negocio pura
│   ├── entities/        # Payment entity
│   └── repositories/    # Repository ports
├── application/         # Casos de uso
│   └── use_cases/       # CreatePayment, ConfirmPayment
└── infrastructure/      # Adaptadores externos
    ├── database/        # PostgreSQL + pgcrypto
    ├── http/            # FastAPI routes
    └── clients/         # HTTP clients (reservas, notificaciones)
```

## Criterios de Aceptación Implementados

### ✅ Confirmación de Pago
- Al recibir confirmación del proveedor, actualiza estado a "Confirmada"
- Almacena: proveedor, ID transacción, monto, moneda, timestamp, método de pago
- Libera hold de habitación y confirma reserva

### ✅ Datos Almacenados (Encriptados con pgcrypto)
- `cardholder_name` - Nombre del titular (LargeBinary)
- `cardholder_email` - Email del titular (LargeBinary)
- `card_last_four` - Últimos 4 dígitos (sin encriptar)

### ✅ Performance
- Tiempo entre confirmación y actualización < 500ms
- Configurable via `PAYMENT_TIMEOUT_MS`

### ✅ Retry Logic
- Máximo 3 intentos automáticos
- Contador de reintentos en base de datos
- Alerta generada si falla después de 3 intentos

### ✅ Notificaciones
- Dispara email de confirmación automáticamente
- Integración con notificaciones_ms

## Endpoints

### POST /api/v1/payments
Crear registro de pago

```json
{
  "booking_id": "uuid",
  "amount": 150.00,
  "currency": "USD",
  "payment_provider": "stripe",
  "payment_method": "credit_card",
  "card_last_four": "4242",
  "cardholder_name": "John Doe",
  "cardholder_email": "john@example.com"
}
```

### POST /api/v1/payments/{booking_id}/confirm
Confirmar pago exitoso

```json
{
  "provider_transaction_id": "ch_1234567890",
  "payment_timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /api/v1/payments/{booking_id}
Obtener pago por booking_id

## Variables de Entorno

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/payments_db

# Encryption (pgcrypto)
AES_ENCRYPTION_KEY=your-256-bit-hex-key

# External services
RESERVAS_MS_URL=http://reservas_ms:8000
NOTIFICACIONES_MS_URL=http://notificaciones_ms:8003
INTERNAL_API_KEY=your-internal-api-key

# Retry config
MAX_RETRY_ATTEMPTS=3
PAYMENT_TIMEOUT_MS=500
```

## Desarrollo Local

### 1. Instalar dependencias

```bash
uv pip install -r requirements.txt
```

### 2. Configurar base de datos

```bash
# Crear base de datos
docker run --name pg-local \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=payments_db \
  -p 5432:5432 \
  -d postgres

# Habilitar pgcrypto
docker exec -it pg-local psql -U postgres -d payments_db -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
```

### 3. Ejecutar migraciones

```bash
alembic upgrade head
```

### 4. Iniciar servicio

```bash
uv run uvicorn src.main:app --reload --port 8004
```

## Docker

### Build

```bash
docker build --rm --no-cache --platform linux/amd64 -t pagosms:latest .
```

### Run

```bash
docker run -p 8004:8000 \
  -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/payments_db \
  -e AES_ENCRYPTION_KEY=your-key \
  pagosms:latest
```

## Testing

```bash
pytest tests/ -v --cov=src
```

## Seguridad

- Datos sensibles encriptados con pgcrypto AES-256
- Clave de encriptación gestionada via AWS Secrets Manager en producción
- Comunicación interna autenticada con API keys
- JWT para autenticación de usuarios

## Integración con Otros Servicios

### reservas_ms
- `PATCH /api/v1/bookings/{id}/payment-confirm` - Actualiza estado a confirmada

### notificaciones_ms
- `POST /api/v1/notifications/payment-confirmation` - Envía email de confirmación

## Monitoreo

- Logs de tiempo de ejecución
- Alertas automáticas si falla después de 3 reintentos
- Métricas de performance (< 500ms)

## Licencia

MIT
