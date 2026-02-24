from contextlib import asynccontextmanager
import os

import httpx
from fastapi import FastAPI
from postgres_db import create_db_and_tables


def get_hospedajes_base_url() -> str:
    configured = os.getenv("HOSPEDAJES_MS_URL")
    if configured:
        return configured.rstrip("/")

    # Heuristic: if running inside Kubernetes (e.g., via Ingress), prefer the
    # in-cluster Service DNS name.
    print(os.getenv("KUBERNETES_SERVICE_HOST"))
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        return "http://hospedajes-service"

    # Local development default.
    return "http://localhost:8000"

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello Users World"}

@app.get("/health")
async def health():
    return {
        "ping": "pong"
    }


@app.get("/call-hospedajes")
async def call_hospedajes():
    base_url = get_hospedajes_base_url()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{base_url}/health")
        resp.raise_for_status()
        return {"target": base_url, "status": resp.status_code, "body": resp.json()}