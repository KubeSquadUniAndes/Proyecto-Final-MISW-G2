from contextlib import asynccontextmanager
import time

from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from app.controllers.reservation_controller import router as reservation_router
from app.database.connection import DatabaseManager

# Métricas de Prometheus
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])


@asynccontextmanager
async def lifespan(app: FastAPI):
    await DatabaseManager.initialize()
    yield
    await DatabaseManager.shutdown()


app = FastAPI(
    title="TravelHub Reservations Service",
    version="1.0.0",
    lifespan=lifespan,
)

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    REQUEST_DURATION.labels(method=request.method, endpoint=request.url.path).observe(duration)
    
    return response

app.include_router(
    reservation_router,
    prefix="/api/v1/reservations",
    tags=["reservations"],
)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
