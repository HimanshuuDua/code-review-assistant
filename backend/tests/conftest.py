import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient

# Project root on path for `backend.*` imports (Vercel + pytest)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

os.environ.setdefault("INFERENCE_MODE", "demo")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")


@pytest.fixture
async def client():
    from backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_request():
    return {"code": "def divide(a, b):\n    return a / b", "language": "python"}
