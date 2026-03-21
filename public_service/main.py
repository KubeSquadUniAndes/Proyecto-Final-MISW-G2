from contextlib import asynccontextmanager
import os

import httpx
from fastapi import FastAPI, HTTPException
from sqlmodel import Session
from postgres_db import create_db_and_tables, engine
from hospedajes_model import Hospedaje, HospedajeCreate


def get_hospedajes_base_url() -> str:
    configured = os.getenv("HOSPEDAJES_MS_URL")
    if configured:
        return configured.rstrip("/")

    if os.getenv("KUBERNETES_SERVICE_HOST"):
        return "http://hospedajes-service"

    return "http://localhost:8000"


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


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def force_json_content_type(request, call_next):
    response = await call_next(request)
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


@app.get("/health")
async def health():
    return {"ping": "pong"}


@app.post("/hospedajes", status_code=201)
async def create_hospedaje(body: HospedajeCreate):
    # Save locally
    hospedaje = Hospedaje(**body.model_dump())
    with Session(engine) as session:
        session.add(hospedaje)
        session.commit()
        session.refresh(hospedaje)

    # Forward to hospedajes_ms
    client = get_http_client()
    base_url = get_hospedajes_base_url()
    resp = await client.post(f"{base_url}/", json=body.model_dump())
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()
