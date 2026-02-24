## Prerrequisitos
1. Install kubectl
2. Install minikube
3. Install uv to install python packages

## Setup de entorno (desarrollo local)
1. Ir a la carpeta root (experimento-g2) desde la terminal y correr el comando para crear un nuevo venv:

```bash
uv venv
```

2. Se recomienda abrir la carpeta root que contiene todos los microservicios en VS Code, y desde el menu de python seleccionar:
Environment Managers -> venv -> experimento-g2

3. Ir a cada microservicio y correr el siguiente comando:

```bash
uv pip install -r requirements.txt
```
IN PROGRESS

## Prerrequisitos
1. Install kubectl
2. Install minikube
3. Install uv to install python packages

## Setup de entorno (desarrollo local)
1. Ir a la carpeta root (experimento-g2) desde la terminal y correr el comando para crear un nuevo venv:

```bash
uv venv
```

2. Se recomienda abrir la carpeta root que contiene todos los microservicios en VS Code, y desde el menu de python seleccionar:
Environment Managers -> venv -> experimento-g2

3. Ir a cada microservicio y correr el siguiente comando:

```bash
uv pip install -r requirements.txt
```

4. Recomendado usar las mismas versiones de librerias en todos los microservicios para evitar conflictos de paquetes en desarrollo local

## Docker (build)
1. Build de la imagen:

```bash
docker build --rm --no-cache --platform linux/amd64 -t app:latest .
```

## Docker (run)
1. Run del contenedor en local:

```bash
docker run -p 8000:8000 hospedajesms
```

## Postgres local (Docker)
1. Iniciar Postgres:

```bash
docker run --name pg-local \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  -d postgres
```

2. Entrar a psql:

```bash
docker exec -it pg-local psql -U postgres -d postgres
```

## Ejecutar el servicio (local)
1. Levantar el servicio:

```bash
uv run uvicorn main:app --reload
```

## Minikube / Kubernetes
1. Iniciar minikube:

```bash
minikube start --cpus=2 --memory=3g
```

2. Habilitar addon de Ingress:

```bash
minikube addons enable ingress ingress-dns
```

3. Usar el contexto de minikube (opcional):

```bash
kubectl config set-context minikube
```

4. Iniciar tunnel para pruebas del cluster local:

```bash
minikube tunnel
```

5. Obtener URL del Ingress Controller:

```bash
minikube service ingress-nginx-controller -n ingress-nginx --url
```

6. Cargar la imagen en minikube:

```bash
minikube image load app:latest
```

7. Esperar a que los deployments estén listos:

```bash
kubectl rollout status deployment/users-deployment --timeout=120s && kubectl rollout status deployment/hospedajes-deployment --timeout=120s
```

8. Abrir dashboard:

```bash
minikube dashboard
```
