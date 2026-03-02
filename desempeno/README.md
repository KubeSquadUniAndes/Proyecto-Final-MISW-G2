# TravelHub - Reservations Service

Sistema de gestión de reservas con arquitectura de microservicios, monitoreo con Prometheus y visualización con Grafana.

## 📐 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                       │
│                                                                   │
│  ┌──────────────┐      ┌──────────────────────────────────┐    │
│  │   Ingress    │──────▶│   Reservations Service (x2)      │    │
│  │  Controller  │      │   - FastAPI                       │    │
│  └──────────────┘      │   - Port 8000                     │    │
│                         │   - /metrics endpoint             │    │
│                         └──────────┬───────────────────────┘    │
│                                    │                             │
│                         ┌──────────▼───────────┐                │
│                         │   PostgreSQL DB      │                │
│                         │   - Port 5432        │                │
│                         │   - PVC Storage      │                │
│                         └──────────────────────┘                │
│                                    │                             │
│  ┌──────────────┐      ┌──────────▼───────────┐                │
│  │  Prometheus  │◀─────│   Metrics Scraper    │                │
│  │  - Port 9090 │      │   - Interval: 5s     │                │
│  └──────┬───────┘      └──────────────────────┘                │
│         │                                                        │
│  ┌──────▼───────┐                                               │
│  │   Grafana    │                                               │
│  │  - Port 3000 │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Estructura de Directorios

```
desempeno/
├── k8s/                                    # Manifiestos de Kubernetes
│   ├── grafana/
│   │   ├── deployment.yaml                # Deployment de Grafana
│   │   └── service.yaml                   # Service de Grafana
│   ├── postgres/
│   │   ├── configmap.yaml                 # Configuración de PostgreSQL
│   │   ├── deployment.yaml                # Deployment de PostgreSQL
│   │   ├── pvc.yaml                       # Persistent Volume Claim
│   │   ├── secret.yaml                    # Credenciales encriptadas
│   │   └── service.yaml                   # Service de PostgreSQL
│   ├── prometheus/
│   │   ├── configmap.yaml                 # Configuración de scraping
│   │   ├── deployment.yaml                # Deployment de Prometheus
│   │   └── service.yaml                   # Service de Prometheus
│   ├── reservations/
│   │   ├── configmap.yaml                 # Variables de entorno
│   │   ├── deployment.yaml                # Deployment del servicio
│   │   └── service.yaml                   # Service del API
│   ├── ingress.yaml                       # Ingress Controller
│   └── namespace.yaml                     # Namespace travelhub
├── reservations-service/                  # Microservicio de reservas
│   ├── app/
│   │   ├── controllers/                   # Capa de controladores
│   │   │   └── reservation_controller.py  # Endpoints REST
│   │   ├── database/
│   │   │   └── connection.py              # Pool de conexiones
│   │   ├── models/                        # Modelos de dominio
│   │   │   └── reservation.py             # Entidad Reservation
│   │   ├── repositories/                  # Capa de persistencia
│   │   │   ├── base.py                    # Abstract Repository
│   │   │   └── reservation_repository.py  # Implementación
│   │   ├── schemas/                       # DTOs y validación
│   │   │   └── reservation.py             # Pydantic schemas
│   │   ├── services/                      # Lógica de negocio
│   │   │   └── reservation_service.py     # Service layer
│   │   ├── config.py                      # Configuración
│   │   └── main.py                        # Entry point
│   ├── init-db/
│   │   └── 01-init.sql                    # Script de inicialización
│   ├── tests/                             # Suite de pruebas
│   │   ├── conftest.py                    # Fixtures de pytest
│   │   ├── test_encryption.py             # Tests de encriptación
│   │   ├── test_performance.py            # Tests de rendimiento
│   │   └── test_reservations.py           # Tests funcionales
│   ├── Dockerfile                         # Imagen del servicio
│   └── requirements.txt                   # Dependencias Python
├── docker-compose.yaml                    # Entorno de desarrollo
└── reservations-api.json                  # Colección Postman
```

## 🚀 Levantar el Contenedor con Kubernetes

### Prerrequisitos

- Docker Desktop con Kubernetes habilitado
- kubectl instalado
- Imagen Docker construida

### 1. Construir la Imagen Docker

```bash
cd reservations-service
docker build -t travelhub/reservations-service:latest .
```

### 2. Crear el Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 3. Desplegar PostgreSQL

```bash
kubectl apply -f k8s/postgres/secret.yaml
kubectl apply -f k8s/postgres/configmap.yaml
kubectl apply -f k8s/postgres/pvc.yaml
kubectl apply -f k8s/postgres/deployment.yaml
kubectl apply -f k8s/postgres/service.yaml
```

### 4. Desplegar el Servicio de Reservas

```bash
kubectl apply -f k8s/reservations/configmap.yaml
kubectl apply -f k8s/reservations/deployment.yaml
kubectl apply -f k8s/reservations/service.yaml
```

### 5. Desplegar Prometheus

```bash
kubectl apply -f k8s/prometheus/configmap.yaml
kubectl apply -f k8s/prometheus/deployment.yaml
kubectl apply -f k8s/prometheus/service.yaml
```

### 6. Desplegar Grafana

```bash
kubectl apply -f k8s/grafana/deployment.yaml
kubectl apply -f k8s/grafana/service.yaml
```

### 7. Configurar Ingress (Opcional)

```bash
kubectl apply -f k8s/ingress.yaml
```

### 8. Verificar el Despliegue

```bash
# Ver todos los pods
kubectl get pods -n travelhub

# Ver servicios
kubectl get svc -n travelhub

# Ver logs del servicio
kubectl logs -n travelhub -l app=reservations-service -f
```

### 9. Acceder a los Servicios

```bash
# Port-forward para el API
kubectl port-forward -n travelhub svc/reservations-service 8000:80

# Port-forward para Grafana
kubectl port-forward -n travelhub svc/grafana 3000:3000

# Port-forward para Prometheus
kubectl port-forward -n travelhub svc/prometheus 9090:9090
```

URLs de acceso:
- API: http://localhost:8000
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

## 📊 Configuración de Prometheus

### ConfigMap de Prometheus

El archivo `k8s/prometheus/configmap.yaml` contiene la configuración de scraping:

```yaml
scrape_configs:
  - job_name: 'reservations-service'
    metrics_path: '/metrics'
    scrape_interval: 5s
    static_configs:
      - targets: ['reservations-service:80']
```

### Métricas Expuestas

El servicio expone las siguientes métricas en `/metrics`:

- **http_requests_total**: Contador de requests HTTP (labels: method, endpoint, status)
- **http_request_duration_seconds**: Histograma de duración de requests (labels: method, endpoint)

### Verificar Métricas

```bash
# Acceder al endpoint de métricas
curl http://localhost:8000/metrics

# Verificar targets en Prometheus
# Ir a http://localhost:9090/targets
```

## 📈 Configuración de Grafana

### 1. Acceder a Grafana

```bash
kubectl port-forward -n travelhub svc/grafana 3000:3000
```

Abrir http://localhost:3000
- Usuario: `admin`
- Contraseña: `admin`

### 2. Agregar Prometheus como Data Source

1. Ir a **Configuration** → **Data Sources**
2. Click en **Add data source**
3. Seleccionar **Prometheus**
4. Configurar:
   - **URL**: `http://prometheus:9090`
   - **Access**: Server (default)
5. Click en **Save & Test**

### 3. Crear Dashboard

#### Opción A: Importar Dashboard Predefinido

1. Ir a **Dashboards** → **Import**
2. Usar ID: `1860` (Node Exporter Full) o crear uno personalizado

#### Opción B: Crear Paneles Personalizados

**Panel 1: Request Rate**
```promql
rate(http_requests_total[1m])
```

**Panel 2: Request Duration (p95)**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Panel 3: Error Rate**
```promql
rate(http_requests_total{status=~"5.."}[1m])
```

**Panel 4: Requests por Endpoint**
```promql
sum by (endpoint) (rate(http_requests_total[1m]))
```

### 4. Configurar Alertas (Opcional)

Crear alertas para:
- Tasa de errores > 5%
- Latencia p95 > 1s
- Disponibilidad del servicio

## 🏗️ Patrones y Arquitectura

### Arquitectura en Capas (Layered Architecture)
```
Controllers → Services → Repositories → Database
```

### 1. **Repository Pattern**
- **Ubicación**: `app/repositories/base.py` y `reservation_repository.py`
- **Propósito**: Abstrae el acceso a datos y encripta/desencripta información sensible
- **Implementación**: Interface abstracta con implementación concreta usando SQL raw y pgcrypto

### 2. **Service Layer Pattern**
- **Ubicación**: `app/services/reservation_service.py`
- **Propósito**: Lógica de negocio (validaciones de fechas, estados de reserva)
- **Implementación**: Coordina entre controladores y repositorios

### 3. **Dependency Injection**
- **Ubicación**: `app/controllers/reservation_controller.py`
- **Propósito**: Desacopla componentes
- **Implementación**: FastAPI Depends para inyectar sesiones y servicios

### 4. **DTO Pattern**
- **Ubicación**: `app/schemas/reservation.py`
- **Propósito**: Validación de entrada/salida
- **Implementación**: Pydantic models (ReservationCreate, ReservationUpdate, ReservationResponse)

### 5. **Singleton Pattern**
- **Ubicación**: `app/database/connection.py` y `app/config.py`
- **Propósito**: Una única instancia de configuración y pool de conexiones
- **Implementación**: DatabaseManager y Settings con @lru_cache

## 🔐 Encriptación con pgcrypto

### Configuración

La extensión pgcrypto se habilita en PostgreSQL mediante:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

### Campos Encriptados

Los siguientes campos se encriptan con AES-256:
- `traveler_name`
- `traveler_email`
- `traveler_phone`
- `traveler_document`

### Implementación

**Encriptación al insertar:**
```sql
INSERT INTO reservations (traveler_name, ...)
VALUES (pgp_sym_encrypt(:name, :key), ...)
```

**Desencriptación al consultar:**
```sql
SELECT pgp_sym_decrypt(traveler_name, :key) AS traveler_name
FROM reservations
```

**Actualización de campos encriptados:**
```sql
UPDATE reservations
SET traveler_name = pgp_sym_encrypt(:name, :key)
WHERE id = :id
```

### Clave de Encriptación

La clave se configura mediante variable de entorno:
```bash
ENCRYPTION_KEY=aes256-experiment-key-miso-uniandes-2026
```

En Kubernetes se almacena en un Secret:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
data:
  ENCRYPTION_KEY: <base64-encoded-key>
```

## 🧪 Ejecutar Tests

```bash
cd reservations-service

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar todos los tests
pytest

# Tests con cobertura
pytest --cov=app tests/

# Tests específicos
pytest tests/test_reservations.py -v
```

## 🐳 Desarrollo Local con Docker Compose

```bash
# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Limpiar volúmenes
docker-compose down -v
```

## 📝 API Endpoints

- `POST /api/v1/reservations` - Crear reserva
- `GET /api/v1/reservations` - Listar reservas
- `GET /api/v1/reservations/{id}` - Obtener reserva
- `PUT /api/v1/reservations/{id}` - Actualizar reserva
- `GET /health` - Health check
- `GET /metrics` - Métricas de Prometheus

## 🔒 Seguridad

- **Encriptación en BD**: Datos sensibles encriptados con pgcrypto (AES-256)
- **Secrets**: Credenciales en Kubernetes Secrets (base64)
- **Variables de entorno**: Configuración externalizada
- **Health checks**: Liveness y readiness probes

## 📚 Tecnologías

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy (async)
- **Monitoring**: Prometheus, Grafana
- **Container**: Docker, Kubernetes
- **Testing**: pytest, pytest-asyncio
