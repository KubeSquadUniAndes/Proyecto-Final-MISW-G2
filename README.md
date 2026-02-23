IN PROGRESS
1. Install kubectl
2. Install minikube
3. Install uv to install python packages
4. Ir a la carpeta root (experimento-g2) desde la terminal y correr el comando "uv venv" para crear un nuevo venv 
4. ir a cada microservicio y correr el siguiente comando
4. uv pip install -r requirements.txt  
6. recomendado usar las mismas versiones de librerias en todos los microservicios para evitar conflictos de paquetes en desarrollo local
5. se recomienda abrir la carpeta root que contiene todos los microservicios en VS Code, y desde el menu de python seleccionar Environment Managers -> venv -> experimento-g2
7. docker build --rm --no-cache --platform linux/amd64 -t app:1.0.0 .
8. docker run -p 8000:8000 hospedajesms
9. docker run --name pg-local \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  -d postgres
10. docker exec -it pg-local psql -U postgres -d postgres
11. uv run uvicorn main:app --reload 

minikube start --cpus=2 --memory=3g

kubectl config set-context minikube

minikube service ingress-nginx-controller -n ingress-nginx --url





## Kubernetes (Minikube)

Estos deployments usan imágenes locales `usersms:latest` y `hospedajesms:latest`.
En Kubernetes, el tag `:latest` por defecto intenta hacer pull; por eso los manifests incluyen `imagePullPolicy: IfNotPresent`.

### Opción A (recomendada): construir dentro del Docker daemon de Minikube

1. `minikube start --cpus=2 --memory=3g`
2. Apunta tu Docker CLI al daemon de Minikube:
  - `eval $(minikube -p minikube docker-env)`
3. Construye las imágenes:
  - `docker build -t usersms:latest ./users_ms`
  - `docker build -t hospedajesms:latest ./hospedajes_ms`
4. Despliega:
  - `kubectl apply -f k8s`
5. (Opcional) volver al Docker daemon local:
  - `eval $(minikube -p minikube docker-env -u)`

### Opción B: construir en tu máquina y cargar a Minikube

1. Construye en tu Docker local:
  - `docker build -t usersms:latest ./users_ms`
  - `docker build -t hospedajesms:latest ./hospedajes_ms`
2. Carga a Minikube:
  - `minikube image load usersms:latest`
  - `minikube image load hospedajesms:latest`
3. Despliega:
  - `kubectl apply -f k8s`

kubectl get po -A
kubectl get svc

## Run everything with Docker Compose

From the repo root:

1. docker compose up --build

Services:

- Users MS: http://localhost:8001/health
- Hospedajes MS: http://localhost:8002/health

Cross-service calls (service-to-service inside the Docker network):

- Users -> Hospedajes: http://localhost:8001/call-hospedajes
- Hospedajes -> Users: http://localhost:8002/call-users
