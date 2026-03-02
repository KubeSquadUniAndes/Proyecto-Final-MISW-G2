import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database.connection import DatabaseManager
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await DatabaseManager.initialize()
    yield
    await DatabaseManager.shutdown()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
