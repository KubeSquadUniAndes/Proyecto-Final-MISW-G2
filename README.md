# TravelHub - Microservices Project

---

## Section 1: Local Development (Python + Docker)

### 1.1 Prerequisites

1. Install `uv` to manage Python packages

### 1.2 Python Environment Setup

1. Navigate to the root folder (`experimento-g2`) and create a new virtual environment:

```bash
uv venv
```

2. Open the root folder in VS Code and select the Python environment:
   - Go to: Environment Managers -> venv -> experimento-g2

3. Install dependencies for each microservice:

```bash
uv pip install -r requirements.txt
```

4. Use the same library versions across all microservices to avoid package conflicts in local development.

### 1.3 Docker Build

1. Build the image:

```bash
docker build --rm --no-cache --platform linux/amd64 -t app:latest .
```

### 1.4 Docker Run

1. Run the container locally:

```bash
docker run -p 8000:8000 hospedajesms
```

### 1.5 Postgres Local (Docker)

1. Start Postgres:

```bash
docker run --name pg-local \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  -d postgres
```

2. Connect to psql:

```bash
docker exec -it pg-local psql -U postgres -d postgres
```

### 1.6 Run the Service Locally

1. Start the service:

```bash
uv run uvicorn main:app --reload
```

---

## Section 2: Minikube / Kubernetes (Localhost)

### 2.1 Prerequisites

1. Install `kubectl`
2. Install `minikube`

### 2.2 Start Minikube

1. Start minikube:

```bash
minikube start --cpus=2 --memory=3g
```

2. Set the minikube context (optional):

```bash
kubectl config set-context minikube
```

3. Start tunnel for local cluster testing:

```bash
minikube tunnel
```

### 2.3 Load Images into Minikube

1. Load application images:

```bash
minikube image load postgres
minikube image load usersms:latest
minikube image load hospedajesms:latest
minikube image load reservasms:latest
minikube image load loginhandlerms:latest
minikube image load detectoranomaliasms:latest
minikube image load notificacionesms:latest
```

### 2.4 Minikube Dashboard

1. Open the dashboard:

```bash
minikube dashboard
```

### 2.5 Istio Service Mesh (Localhost)

1. Download Istio:

```bash
curl -L https://istio.io/downloadIstio | sh -
```

2. Add Istio to PATH:

```bash
export PATH="$PATH:/Users/juanseromo/istio-1.29.0/bin"
```

3. Run pre-check:

```bash
istioctl x precheck
```

4. Analyze configuration:

```bash
istioctl analyze
```

5. Restart deployments to inject sidecars:

```bash
kubectl rollout restart deployment/users-deployment deployment/hospedajes-deployment deployment/reservas-deployment deployment/login-handler-deployment deployment/detector-anomalias-deployment deployment/notificaciones-deployment deployment/postgres-deployment
```

### 2.6 Important: Istio Configuration Order

To avoid HTTP 503 errors caused by Envoy configurations referring to non-existent upstream pools:

**When adding subsets:**
1. Apply `DestinationRule` first
2. Wait a few seconds for the configuration to propagate to Envoy sidecars
3. Apply `VirtualService` referencing the new subsets

**When removing subsets:**
1. Update `VirtualService` to remove references to the subset
2. Wait a few seconds for the configuration to propagate to Envoy sidecars
3. Update `DestinationRule` to remove the subset

### 2.7 Useful Debugging Commands

1. Check gateway:

```bash
kubectl get gateway
```

2. View pod logs:

```bash
kubectl logs -l app=reservas-app --tail=50
kubectl logs -l app=login-handler-app --tail=50
kubectl logs -l app=detector-anomalias-app --tail=50
kubectl logs -l app=notificaciones-app --tail=50
```

3. Monitor node memory pressure:

```bash
kubectl top node
```

4. Watch pod memory and OOMKills:

```bash
kubectl top pods -n default --sort-by=memory
```

5. Check for evictions/OOMKills:

```bash
kubectl get events -n default --sort-by='.lastTimestamp' | grep -E "OOMKill|Evict|Failed|Back-off"
```

6. Check waypoint health:

```bash
kubectl get pods -n default -l gateway.networking.k8s.io/gateway-name=waypoint-private
```

---

## Section 3: Istio in EKS Cluster (Production)

### 3.1 Configure kubectl for EKS

1. Update kubeconfig:

```bash
aws eks update-kubeconfig --region us-east-1 --name travelhub-eks
```

### 3.2 Install Istio

1. Install Gateway API CRDs:

```bash
kubectl get crd gateways.gateway.networking.k8s.io &> /dev/null || \
  kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.0/experimental-install.yaml
```

2. Install Istio with ambient profile:

```bash
istioctl install --set profile=ambient --skip-confirmation
```


3. Apply standard Gateway API:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml
```

### 3.3 Push Docker Images to ECR

1. Build images (run from each microservice directory):

```bash
# From reservas_ms/
docker build --rm --no-cache --platform linux/amd64 -t reservasms:latest .

# From login_handler_ms/
docker build --rm --no-cache --platform linux/amd64 -t loginhandlerms:latest .

# From detector_anomalias_ms/
docker build --rm --no-cache --platform linux/amd64 -t detectoranomaliasms:latest .

# From notificaciones_ms/
docker build --rm --no-cache --platform linux/amd64 -t notificacionesms:latest .

# From users_ms/
docker build --rm --no-cache --platform linux/amd64 -t usersms:latest .

# From hospedajes_ms/
docker build --rm --no-cache --platform linux/amd64 -t hospedajesms:latest .
```

2. Tag images:

```bash
docker tag reservasms:latest 780522923809.dkr.ecr.us-east-1.amazonaws.com/travelhub/reservasms:latest
docker tag loginhandlerms:latest 780522923809.dkr.ecr.us-east-1.amazonaws.com/travelhub/loginhandlerms:latest
docker tag detectoranomaliasms:latest 780522923809.dkr.ecr.us-east-1.amazonaws.com/travelhub/detectoranomaliasms:latest
docker tag notificacionesms:latest 780522923809.dkr.ecr.us-east-1.amazonaws.com/travelhub/notificacionesms:latest
docker tag usersms:latest 780522923809.dkr.ecr.us-east-1.amazonaws.com/travelhub/usersms:latest
docker tag hospedajesms:latest 780522923809.dkr.ecr.us-east-1.amazonaws.com/travelhub/hospedajesms:latest
```

3. Push images:

```bash
docker push 780522923809.dkr.ecr.us-east-1.amazonaws.com/travelhub/reservasms:latest
docker push 780522923809.dkr.ecr.us-east-1.amazonaws.com/travelhub/loginhandlerms:latest
docker push 780522923809.dkr.ecr.us-east-1.amazonaws.com/travelhub/detectoranomaliasms:latest
docker push 780522923809.dkr.ecr.us-east-1.amazonaws.com/travelhub/notificacionesms:latest
docker push 780522923809.dkr.ecr.us-east-1.amazonaws.com/travelhub/usersms:latest
docker push 780522923809.dkr.ecr.us-east-1.amazonaws.com/travelhub/hospedajesms:latest
```

### 3.4 Install Istio Addons (Observability)

1. Install Kiali, Jaeger, Prometheus, and Grafana:

```bash
for ADDON in kiali jaeger prometheus grafana
do
ADDON_URL="https://raw.githubusercontent.com/istio/istio/release-1.29.1/samples/addons/$ADDON.yaml"
    kubectl apply --server-side -f $ADDON_URL
done
```

### 3.5 Verify Installation

1. Check gateway status:

```bash
kubectl get gateway
```

# Start the project from scratch


## Paso 1 — Crear infraestructura con Terraform

```bash
cd terraform/envs/prod

# Copiar y editar variables
cp terraform.tfvars.example terraform.tfvars
# Edita terraform.tfvars con tu db_password

# Inicializar
terraform init

# Ver plan
terraform plan

# Aplicar (~15 min por el RDS y EKS)
./tf-apply.sh
```

Guarda los outputs — los necesitas en el siguiente paso:
```bash
terraform output cluster_name        # travelhub-prod
terraform output ecr_urls            # URLs de ECR
terraform output rds_endpoint        # endpoint de RDS (sensitive)
terraform output configure_kubectl   # comando para configurar kubectl
```

---

## Paso 2 — Configurar kubectl

```bash
cd ../../../
aws eks update-kubeconfig --region us-east-1 --name travelhub-prod
kubectl get nodes  # debe mostrar los nodos
```

---

## Paso 3 — Instalar Istio Service mmesh - Ambient mode

```bash
# Run the Istio installation script

cd ./k8s
./install-istio-ambient.sh
```

1. Check gateway status:

```bash
kubectl get gateway -n workloads
```

## Paso 4 — Actualizar los manifiestos K8s

Reemplaza estos placeholders en `k8s/users-ms/users-ms.yaml` y `k8s/login-handler-ms/login-handler-ms.yaml`:

| Placeholder | Valor |
|-------------|-------|
| `CHANGE_RDS_ENDPOINT` | endpoint de RDS sin el puerto (ej: `travelhub-prod-postgres.xxxx.us-east-1.rds.amazonaws.com`) |
| `CHANGE_ME` (password) | tu db_password |
| `CHANGE_AWS_ACCOUNT_ID` | tu AWS Account ID (12 dígitos) |
| `CHANGE_ME_USE_LONG_RANDOM_STRING` | JWT secret key seguro |
| `CHANGE_ME_INTERNAL_KEY` | internal API key |


---


## Paso 5 — Crear las bases de datos en RDS

```bash
# Conectar al RDS (desde dentro del cluster o via bastion)
kubectl run psql-client --rm -it --image=postgres:16-alpine -- \
  psql -h CHANGE_RDS_ENDPOINT -U postgres -c "CREATE DATABASE users_db;"

kubectl run psql-client --rm -it --image=postgres:16-alpine -- \
  psql -h travelhub-prod-postgres.ci3w0yecas02.us-east-1.rds.amazonaws.com -U postgres -c "CREATE DATABASE auth_db;"
```

---
## Paso 3 - Apply /k8s files. 

```
git commit -m 'anything'
git push
```
---

# Obtener Account ID
aws sts get-caller-identity --query Account --output text

# Obtener RDS endpoint
cd terraform/envs/prod
terraform output rds_endpoint
```



---

## Paso 8 — CI/CD automático con GitHub Actions

Agrega estos secrets en tu repositorio (Settings → Secrets):

| Secret | Valor |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | Access key de un IAM user con permisos EKS + ECR |
| `AWS_SECRET_ACCESS_KEY` | Secret key |
| `AWS_ACCOUNT_ID` | Tu AWS Account ID |

Cada push a `main` construye las imágenes, las sube a ECR y despliega en EKS automáticamente.

---

kubectl run psql-create-dbs --image=postgres:alpine3.22 --restart=Never --env="PGPASSWORD=SecurePass123!" --command -- psql -h travelhub-prod-postgres.ci3w0yecas02.us-east-1.rds.amazonaws.com -U postgres -d postgres -c "CREATE DATABASE users_db;" -c "CREATE DATABASE anomalies_db;" -c "CREATE DATABASE auth_db" 2>&1


kubectl exec -n default deploy/users-deployment -- python /app/run_migrations.py
kubectl exec -n default deploy/detector-anomalias-deployment -- python /app/run_migrations.py



```
patch_deployments() {
  local namespace=$1
  echo "Patching deployments in namespace: $namespace"
  
  kubectl get deployment -n "$namespace" -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n' | while read deploy; do
    kubectl patch deployment "$deploy" -n "$namespace" --type=merge -p '{"spec":{"template":{"spec":{"nodeSelector":{"role":"observability"},"tolerations":[{"key":"dedicated","operator":"Equal","value":"observability","effect":"NoSchedule"}]}}}}'
  done
}

# Patch namespaces
patch_deployments "istio-system"
patch_deployments "monitoring" || true
```
