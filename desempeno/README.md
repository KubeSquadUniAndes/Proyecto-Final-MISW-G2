# TravelHub - Reservations Service

Sistema de gestión de reservas con arquitectura de microservicios, monitoreo con Prometheus y visualización con Grafana.

## 📐 Diagrama de Arquitectura

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                           │
│                                                                      │
│  ┌───────────────────┐    TLS 1.3     ┌────────────────────────┐     │
│  │   NGINX Ingress   │──────────────▶│  Reservations Service   │     │
│  │   + TLS (cert-mgr)│  Rate Limit   │  (x2 replicas)         │     │
│  │   + Rate Limiting │  100rps/50conn│  - FastAPI + Python 3.13│     │
│  └───────────────────┘               │  - /metrics endpoint    │     │
│         ▲                            └──────────┬──────────────┘     │
│         │ HTTPS                                 │ SSL                │
│      Cliente                         ┌──────────▼──────────────┐     │
│                                      │   PostgreSQL 16         │     │
│                                      │   - SSL enabled         │     │
│                                      │   - pgcrypto (AES-256)  │     │
│                                      │   - PVC 1Gi             │     │
│                                      └─────────────────────────┘     │
│                                                                      │
│  ┌──────────────┐       ┌──────────────┐                             │
│  │  Prometheus  │◀──────│  Scraper 5s  │                             │
│  │  - Port 9090 │       └──────────────┘                             │
│  └──────┬───────┘                                                    │
│  ┌──────▼───────┐       ┌──────────────┐                             │
│  │   Grafana    │       │ cert-manager │                             │
│  │  - Port 3000 │       │ (self-signed)│                             │
│  └──────────────┘       └──────────────┘                             │
└──────────────────────────────────────────────────────────────────────┘
```

## 📁 Estructura de Directorios

```
desempeno/
├── k8s/                                    # Manifiestos de Kubernetes
│   ├── cert-manager/
│   │   ├── cluster-issuer.yaml            # ClusterIssuer self-signed
│   │   └── certificate.yaml              # Certificate TLS para travelhub.local
│   ├── grafana/
│   │   ├── deployment.yaml                # Deployment de Grafana
│   │   └── service.yaml                   # Service de Grafana
│   ├── postgres/
│   │   ├── configmap.yaml                 # Configuracion de PostgreSQL
│   │   ├── deployment.yaml                # Deployment de PostgreSQL (SSL enabled)
│   │   ├── pvc.yaml                       # Persistent Volume Claim
│   │   ├── secret.yaml                    # Credenciales encriptadas
│   │   └── service.yaml                   # Service de PostgreSQL
│   ├── prometheus/
│   │   ├── configmap.yaml                 # Configuracion de scraping
│   │   ├── deployment.yaml                # Deployment de Prometheus
│   │   └── service.yaml                   # Service de Prometheus
│   ├── reservations/
│   │   ├── configmap.yaml                 # Variables de entorno (DATABASE_SSL)
│   │   ├── deployment.yaml                # Deployment del servicio
│   │   └── service.yaml                   # Service del API
│   ├── ingress.yaml                       # Ingress con TLS + Rate Limiting
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

- minikube instalado con driver Docker
- kubectl instalado
- Addons habilitados: ingress, metrics-server

### 1. Iniciar minikube

```bash
minikube start --memory=4096 --cpus=2 --driver=docker
minikube addons enable ingress
minikube addons enable metrics-server
```

### 2. Construir la Imagen Docker (dentro de minikube)

```bash
eval $(minikube docker-env)
cd reservations-service
docker build -t travelhub/reservations-service:latest .
```

### 3. Instalar cert-manager (para TLS)

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.yaml
kubectl -n cert-manager rollout status deployment/cert-manager --timeout=120s
kubectl -n cert-manager rollout status deployment/cert-manager-webhook --timeout=120s
```

### 4. Desplegar en orden

```bash
# Namespace
kubectl apply -f k8s/namespace.yaml

# cert-manager (TLS)
kubectl apply -f k8s/cert-manager/cluster-issuer.yaml
kubectl apply -f k8s/cert-manager/certificate.yaml

# PostgreSQL (con SSL)
kubectl apply -f k8s/postgres/

# Servicio de Reservas
kubectl apply -f k8s/reservations/

# Ingress (TLS + Rate Limiting)
kubectl apply -f k8s/ingress.yaml

# Monitoreo
kubectl apply -f k8s/prometheus/
kubectl apply -f k8s/grafana/
```

### 5. Configurar acceso

```bash
# Agregar host (una sola vez)
sudo sh -c 'echo "127.0.0.1 travelhub.local" >> /etc/hosts'

# Iniciar tunnel (dejar corriendo en terminal aparte)
sudo minikube tunnel
```

### 6. Verificar el Despliegue

```bash
# Ver todos los pods
kubectl get pods -n travelhub

# Verificar certificado TLS
kubectl -n travelhub get certificate

# Verificar SSL en PostgreSQL
kubectl -n travelhub exec deployment/postgres -- psql -U travelhub -d travelhub \
  -c "SELECT pid, ssl FROM pg_stat_ssl JOIN pg_stat_activity USING (pid) WHERE datname = 'travelhub';"

# Verificar rate limiting
kubectl -n travelhub describe ingress travelhub-ingress | grep limit
```

### 7. Acceder a los Servicios

URLs de acceso:
- **Swagger UI**: https://travelhub.local/docs
- **API**: https://travelhub.local/api/v1/reservations/
- **Health**: https://travelhub.local/health
- **Metrics**: https://travelhub.local/metrics
- **Grafana**: `minikube service grafana-service -n travelhub` (admin/admin)

> Nota: El certificado TLS es self-signed. En el navegador aceptar la advertencia de seguridad.

### 8. Pruebas con JMeter

```bash
# Crear truststore con el certificado
echo | openssl s_client -connect 127.0.0.1:443 -servername travelhub.local 2>/dev/null \
  | openssl x509 -outform DER > /tmp/travelhub.der
keytool -importcert -alias travelhub -file /tmp/travelhub.der \
  -keystore /tmp/travelhub-truststore.jks -storepass changeit -noprompt

# Abrir JMeter con el truststore
jmeter -Djavax.net.ssl.trustStore=/tmp/travelhub-truststore.jks \
  -Djavax.net.ssl.trustStorePassword=changeit
```

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

## 🔒 Seguridad (ASR-01)

### Cifrado en reposo (AES-256)
- Campos sensibles cifrados con pgcrypto (`pgp_sym_encrypt` / `pgp_sym_decrypt`)
- Campos: `traveler_name`, `traveler_email`, `traveler_phone`, `traveler_document`
- Clave almacenada en Kubernetes Secret

### Cifrado en transito (TLS 1.3)
- **Cliente → Ingress**: TLS 1.3 / AES-256-GCM-SHA384 via cert-manager (self-signed)
- **App → PostgreSQL**: SSL con SSLContext (configurado via `DATABASE_SSL=true`)
- Redireccion forzada HTTP → HTTPS (`ssl-redirect: true`)

### Control de demanda de recursos (Rate Limiting)
- 100 requests/segundo por IP
- 50 conexiones concurrentes por IP
- Burst multiplier: x5
- Solicitudes excedentes rechazadas con HTTP 503

### Otras medidas
- Credenciales en Kubernetes Secrets (base64)
- Variables de entorno externalizadas
- Health checks: Liveness y readiness probes
- Connection pool: pool_size=10, max_overflow=20

## 📊 Resultados del Experimento

| Metrica | Resultado |
|---|---|
| POST con cifrado AES-256 | **48 ms** promedio |
| GET con descifrado AES-256 | **493 ms** promedio |
| Protocolo TLS | TLSv1.3 / AES-256-GCM-SHA384 |
| SSL App→PostgreSQL | Verificado (`pg_stat_ssl: ssl = t`) |
| Rate limiting | HTTP 503 en excedentes, 0 restarts |
| Umbral ASR-01 | < 1.500 ms → **Cumplido** |

## 📚 Tecnologias

- **Backend**: FastAPI, Python 3.13
- **Database**: PostgreSQL 16-alpine + pgcrypto
- **ORM**: SQLAlchemy 2.0 (async + asyncpg)
- **TLS**: cert-manager + NGINX Ingress Controller
- **Monitoring**: Prometheus + Grafana
- **Container**: Docker, Kubernetes (minikube)
- **Testing**: pytest, JMeter 5.6.3
