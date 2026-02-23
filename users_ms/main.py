from contextlib import asynccontextmanager
import os

import httpx
from fastapi import FastAPI
from postgres_db import create_db_and_tables

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
    base_url = os.getenv("HOSPEDAJES_MS_URL", "http://hospedajes_ms:8000").rstrip("/")
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{base_url}/health")
        resp.raise_for_status()
        return {"target": base_url, "status": resp.status_code, "body": resp.json()}