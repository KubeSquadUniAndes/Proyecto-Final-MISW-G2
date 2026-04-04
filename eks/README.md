# EKS Deployment — travelhub

## Prerequisitos

```bash
# Instalar herramientas
brew install terraform awscli kubectl

# Configurar credenciales AWS
aws configure
# AWS Access Key ID: <tu key>
# AWS Secret Access Key: <tu secret>
# Default region: us-east-1
```

---

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
terraform apply
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
aws eks update-kubeconfig --region us-east-1 --name travelhub-prod
kubectl get nodes  # debe mostrar los nodos
```

---

## Paso 3 — Instalar NGINX Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.0/deploy/static/provider/cloud/deploy.yaml

# Esperar que esté listo
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

# Obtener el DNS del Load Balancer (usar este en tu dominio)
kubectl get svc -n ingress-nginx ingress-nginx-controller
# EXTERNAL-IP = xxxxxxx.us-east-1.elb.amazonaws.com
```

---

## Paso 4 — Actualizar los manifiestos K8s

Reemplaza estos placeholders en `k8s/users-ms/users-ms.yaml` y `k8s/login-handler-ms/login-handler-ms.yaml`:

| Placeholder | Valor |
|-------------|-------|
| `CHANGE_RDS_ENDPOINT` | endpoint de RDS sin el puerto (ej: `travelhub-prod-postgres.xxxx.us-east-1.rds.amazonaws.com`) |
| `CHANGE_ME` (password) | tu db_password |
| `CHANGE_AWS_ACCOUNT_ID` | tu AWS Account ID (12 dígitos) |
| `CHANGE_ME_USE_LONG_RANDOM_STRING` | JWT secret key seguro |
| `CHANGE_ME_INTERNAL_KEY` | internal API key |

```bash
# Obtener Account ID
aws sts get-caller-identity --query Account --output text

# Obtener RDS endpoint
cd terraform/envs/prod
terraform output rds_endpoint
```

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

## Paso 6 — Construir y subir imágenes a ECR

```bash
# Login a ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  CHANGE_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build y push users-ms
docker build -t CHANGE_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/travelhub/users-ms:latest ./users_ms
docker push CHANGE_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/travelhub/users-ms:latest

# Build y push login-handler-ms
docker build -t CHANGE_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/travelhub/login-handler-ms:latest ./login_handler_ms
docker push CHANGE_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/travelhub/login-handler-ms:latest
```

---

## Paso 7 — Desplegar en EKS

```bash
# Aplicar manifiestos
kubectl apply -f eks/k8s/shared/namespaces.yaml
kubectl apply -f eks/k8s/shared/ingress.yaml
kubectl apply -f eks/k8s/login-handler-ms/login-handler-ms.yaml
kubectl apply -f eks/k8s/users-ms/users-ms.yaml

# Verificar pods
kubectl get pods -A | grep -E "users|login"

# Correr migraciones
kubectl exec -n login-handler-ms deploy/login-handler-ms -- alembic upgrade head
kubectl exec -n users-ms deploy/users-ms -- alembic upgrade head
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

## Verificar el deploy

```bash
# Ver el DNS del Load Balancer
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Probar health checks (usar el DNS del LB)
curl http://xxxxxxx.us-east-1.elb.amazonaws.com/auth/health
curl http://xxxxxxx.us-east-1.elb.amazonaws.com/users/health
```
