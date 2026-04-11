# Despliegue parcial: login-handler-ms + users-ms

Manifests para desplegar únicamente `login-handler-ms` y `users-ms` con Istio ambient mode en EKS.

## Prerrequisitos

- AWS CLI configurado con permisos sobre el cluster y ECR
- `kubectl` instalado
- `docker` instalado
- Istio 1.29.1 instalado en el cluster con ambient mode
- Gateway API CRDs instalados
- RDS PostgreSQL desplegado y accesible desde los nodos

## 1. Conectar al cluster

```bash
aws eks update-kubeconfig --region us-east-1 --name travelhub-prod
```

Verifica que los nodos tengan el label `role=workloads`:

```bash
kubectl get nodes --show-labels | grep "role=workloads"
```

## 2. Crear las bases de datos en RDS

Si es la primera vez, las bases de datos deben existir en el RDS antes de desplegar.

```bash
kubectl run psql-pod -n default --image=postgres:alpine3.22 --restart=Never -- sleep 3600
kubectl wait pod/psql-pod -n default --for=condition=Ready --timeout=60s
kubectl exec -it psql-pod -n default -- sh
```

Dentro del pod:

```sh
PGPASSWORD='<DB_PASSWORD>' psql -h <RDS_ENDPOINT> -U postgres -d postgres -c "CREATE DATABASE auth_db; CREATE DATABASE users_db;"
```

Limpia el pod:

```bash
exit
kubectl delete pod psql-pod -n default
```

## 3. Autenticar Docker con ECR

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
```

## 4. Build y push de imágenes

Desde la raíz del repositorio:

```bash
docker build -t <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/travelhub/login-handler-ms:latest login_handler_ms/
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/travelhub/login-handler-ms:latest

docker build -t <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/travelhub/users-ms:latest users_ms/
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/travelhub/users-ms:latest
```

## 5. Aplicar los manifests

Aplicar en orden (la numeración garantiza las dependencias):

```bash
kubectl apply -f k8s/partial/00-namespace.yaml
kubectl apply -f k8s/partial/01-service-accounts.yaml
kubectl apply -f k8s/partial/02-secrets-configmaps.yaml
kubectl apply -f k8s/partial/03-waypoint.yaml
kubectl apply -f k8s/partial/04-gateway.yaml
kubectl apply -f k8s/partial/05-services.yaml
kubectl apply -f k8s/partial/06-destination-rules.yaml
kubectl apply -f k8s/partial/07-http-routes.yaml
kubectl apply -f k8s/partial/08-deployments.yaml
```

O de una sola vez:

```bash
kubectl apply -f k8s/partial/
```

## 6. Verificar el despliegue

```bash
# Estado de los pods (esperar 1/1 Running)
kubectl get pods -n workloads -w

# Obtener el endpoint del NLB
kubectl get svc travelhub-gateway-istio -n workloads
```

El campo `EXTERNAL-IP` del service puede tardar 1-3 minutos en aparecer.

## 7. Probar los servicios

Reemplaza `<NLB_ENDPOINT>` con el valor de `EXTERNAL-IP`:

```bash
# Health checks
curl http://<NLB_ENDPOINT>/login-handler/health
curl http://<NLB_ENDPOINT>/users/health

# Registrar un usuario
curl -X POST http://<NLB_ENDPOINT>/users/api/v1/users/register \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "juan@example.com",
    "phone": "+57 300 123 4567",
    "country": "Colombia",
    "city": "Bogotá",
    "birth_date": "1995-06-15",
    "password": "SecurePass123!",
    "user_type": "traveler",
    "identification_type": "CC",
    "identification_number": "1234567890"
  }'

# Login
curl -X POST http://<NLB_ENDPOINT>/login-handler/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email": "juan@example.com", "password": "SecurePass123!"}'

# Perfil del usuario autenticado (usar el access_token del login)
curl http://<NLB_ENDPOINT>/login-handler/api/v1/auth/me \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

## 8. Redeploy de código

Cuando hay cambios en el código, rebuild, push y restart:

```bash
# Rebuild y push
docker build -t <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/travelhub/login-handler-ms:latest login_handler_ms/
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/travelhub/login-handler-ms:latest

# Restart del deployment
kubectl rollout restart deployment/login-handler-deployment -n workloads
kubectl rollout status deployment/login-handler-deployment -n workloads
```

## Archivos incluidos

| Archivo | Descripción |
|---|---|
| `00-namespace.yaml` | Namespace `workloads` con Istio ambient mode |
| `01-service-accounts.yaml` | ServiceAccount para `login-handler-ms` |
| `02-secrets-configmaps.yaml` | Secrets y ConfigMaps de ambos servicios |
| `03-waypoint.yaml` | Waypoint proxy para tráfico east-west (L7) |
| `04-gateway.yaml` | Ingress Gateway — crea el NLB en EKS |
| `05-services.yaml` | ClusterIP Services |
| `06-destination-rules.yaml` | Outlier detection y connection pools |
| `07-http-routes.yaml` | HTTPRoutes: `/login-handler` y `/users` |
| `08-deployments.yaml` | Deployments de ambos microservicios |

## Notas

- Las credenciales en `02-secrets-configmaps.yaml` deben actualizarse antes de desplegar en producción.
- El NLB usa el controlador in-tree de EKS (no requiere AWS Load Balancer Controller).
- Los deployments usan `nodeSelector: role: workloads` — los nodos deben tener ese label.
- Los init containers verifican conectividad con RDS antes de arrancar la aplicación.
