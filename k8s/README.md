# k8s — Kubernetes Manifests

Deploys the full microservices ecosystem on Kubernetes with NGINX Ingress Controller.

## Structure

```
k8s/
├── deploy.sh                              ← Apply / delete all manifests
├── reservas-ms/
│   └── reservas-ms.yaml                  ← Namespace, Secret, ConfigMap, PVC, DB, Deployment, Service, Ingress
├── login-handler-ms/
│   └── login-handler-ms.yaml
├── detector-anomalias-ms/
│   └── detector-anomalias-ms.yaml
└── notificaciones-ms/
    └── notificaciones-ms.yaml
```

Each file contains everything that microservice needs — one file per service.

## Architecture

```
Internet
    └── NGINX Ingress Controller
            ├── /auth/...           → login-handler-ms     (namespace: login-handler-ms)
            ├── /reservas/...       → reservas-ms          (namespace: reservas-ms)
            ├── /detector/...       → detector-anomalias-ms (namespace: detector-anomalias-ms)
            └── /notifications/...  → notificaciones-ms    (namespace: notificaciones-ms)
```

Internal service-to-service calls use fully qualified cluster DNS:
```
http://<service>.<namespace>.svc.cluster.local:<port>
```

## Prerequisites

```bash
# NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.0/deploy/static/provider/cloud/deploy.yaml

# Verify it's running
kubectl get pods -n ingress-nginx
```

## Deploy

```bash
cd k8s
chmod +x deploy.sh

# Apply everything
./deploy.sh apply

# Tear down
./deploy.sh delete
```

Or apply individually:
```bash
kubectl apply -f login-handler-ms/login-handler-ms.yaml
kubectl apply -f reservas-ms/reservas-ms.yaml
kubectl apply -f detector-anomalias-ms/detector-anomalias-ms.yaml
kubectl apply -f notificaciones-ms/notificaciones-ms.yaml
```

## Update secrets before deploying

Edit the `stringData` blocks in each manifest with real values:

| Secret field | Where used |
|---|---|
| `JWT_SECRET_KEY` | `reservas-ms` + `login-handler-ms` — **must be the same value** |
| `INTERNAL_API_KEY` | All services — **must be the same value** |
| `LOGIN_HANDLER_MS_INTERNAL_API_KEY` | `detector-anomalias-ms` |
| `NOTIFICACIONES_MS_API_KEY` | `detector-anomalias-ms` |
| `SMTP_USER` / `SMTP_PASSWORD` | `notificaciones-ms` |
| `SLACK_WEBHOOK_URL` | `notificaciones-ms` |

> For production, use **Sealed Secrets** or an external secrets manager (Vault, AWS Secrets Manager) instead of plaintext `stringData`.

## Change the domain

Replace `api.experiment.local` in every Ingress spec and in `deploy.sh`:

```bash
grep -r "api.experiment.local" . --include="*.yaml" -l
# Then replace:
sed -i 's/api.experiment.local/your.domain.com/g' **/*.yaml
```

For local testing, add to `/etc/hosts`:
```
127.0.0.1  api.experiment.local
```

## Run database migrations

After deploying, run Alembic migrations inside each pod:

```bash
# reservas_ms
kubectl exec -n reservas-ms deploy/reservas-ms -- alembic upgrade head

# login_handler_ms
kubectl exec -n login-handler-ms deploy/login-handler-ms -- alembic upgrade head

# detector_anomalias_ms
kubectl exec -n detector-anomalias-ms deploy/detector-anomalias-ms -- alembic upgrade head
```

## Verify

```bash
# Check all pods are Running
kubectl get pods -A | grep -E "reservas|login|detector|notificaciones"

# Check ingress routes
kubectl get ingress -A

# Test health endpoints
curl http://api.experiment.local/auth/health
curl http://api.experiment.local/reservas/health
curl http://api.experiment.local/detector/health
curl http://api.experiment.local/notifications/health
```

## Scaling

```bash
# Scale a specific microservice
kubectl scale deployment reservas-ms -n reservas-ms --replicas=4

# Enable autoscaling
kubectl autoscale deployment reservas-ms -n reservas-ms --min=2 --max=8 --cpu-percent=70
```
