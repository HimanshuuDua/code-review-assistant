import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

os.environ.setdefault("INFERENCE_MODE", "demo")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
os.environ.setdefault("STORAGE_ENABLED", "true")


@pytest.fixture
async def client():
    from backend.database import init_db
    from backend.main import app

    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_request():
    return {"code": "def divide(a, b):\n    return a / b", "language": "python", "user_name": "alice"}
