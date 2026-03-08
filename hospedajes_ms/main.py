from contextlib import asynccontextmanager
import uuid
import os

import httpx
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select
from postgres_db import create_db_and_tables, engine
from hospedajes_model import Hospedaje, HospedajeCreate

def get_users_base_url() -> str:
    configured = os.getenv("USERS_MS_URL")
    if configured:
        return configured.rstrip("/")

    # Heuristic: if running inside Kubernetes (e.g., via Ingress), prefer the
    # in-cluster Service DNS name.
    print(os.getenv("KUBERNETES_SERVICE_HOST"))
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        return "http://users-service"

    # Local development default.
    return "http://localhost:9000"

# Reusable httpx client – created once, shared across all requests
_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    if _http_client is None:
        raise RuntimeError("HTTP client is not initialized")
    return _http_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _http_client
    create_db_and_tables()
    _http_client = httpx.AsyncClient(timeout=5.0)
    yield
    await _http_client.aclose()
    # _http_client = None


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def force_json_content_type(request, call_next):
    response = await call_next(request)
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

@app.get("/")
async def root():
    return {"message": "Hello Hospedajes World"}

@app.get("/health")
async def health():
    return {
        "ping": "pong"
    }


@app.get("/call-users")
async def call_users():
    client = get_http_client()
    base_url = get_users_base_url()
    resp = await client.get(f"{base_url}/health")
    resp.raise_for_status()
    return {"target": base_url, "status": resp.status_code, "body": resp.json()}


@app.post("/", status_code=201)
def create_hospedaje(body: HospedajeCreate):
    hospedaje = Hospedaje(**body.model_dump())
    with Session(engine) as session:
        session.add(hospedaje)
        session.commit()
        session.refresh(hospedaje)
    return hospedaje


@app.get("/{hospedaje_id}")
def get_hospedaje(hospedaje_id: uuid.UUID):
    with Session(engine) as session:
        hospedaje = session.get(Hospedaje, hospedaje_id)
        if not hospedaje:
            raise HTTPException(status_code=404, detail="Hospedaje not found")
        return hospedaje


@app.post("/users", status_code=201)
async def create_user(body: dict):
    client = get_http_client()
    base_url = get_users_base_url()
    resp = await client.post(f"{base_url}/", json=body)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


@app.get("/users/{user_id}")
async def get_user(user_id: uuid.UUID):
    client = get_http_client()
    base_url = get_users_base_url()
    resp = await client.get(f"{base_url}/{user_id}")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="User not found")
    resp.raise_for_status()
    return resp.json()