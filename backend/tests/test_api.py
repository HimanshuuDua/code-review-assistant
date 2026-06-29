import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["inference_mode"] == "demo"
    assert data["storage_enabled"] is True


@pytest.mark.asyncio
async def test_review_compare(client, sample_request):
    response = await client.post("/api/review", json=sample_request)
    assert response.status_code == 200
    data = response.json()
    assert "base_model" in data
    assert "finetuned_model" in data
    assert len(data["base_model"]["comments"]) >= 1
    assert len(data["finetuned_model"]["comments"]) >= 1


@pytest.mark.asyncio
async def test_review_saved_to_history(client, sample_request):
    await client.post("/api/review", json=sample_request)
    response = await client.get("/api/admin/reviews", headers={"X-Admin-Key": "test-admin-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["user_name"] == "alice"


@pytest.mark.asyncio
async def test_admin_requires_key(client):
    response = await client.get("/api/admin/reviews")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_rejects_invalid_key(client):
    response = await client.get("/api/admin/reviews", headers={"X-Admin-Key": "wrong"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_stats(client, sample_request):
    await client.post("/api/review", json=sample_request)
    response = await client.get("/api/admin/stats", headers={"X-Admin-Key": "test-admin-key"})
    assert response.status_code == 200
    assert response.json()["total_reviews"] >= 1


@pytest.mark.asyncio
async def test_finetuned_finds_division_bug(client, sample_request):
    response = await client.post("/api/review/finetuned", json=sample_request)
    assert response.status_code == 200
    comments = response.json()["comments"]
    messages = " ".join(c["message"].lower() for c in comments)
    assert "zero" in messages or "division" in messages


@pytest.mark.asyncio
async def test_review_base_only(client, sample_request):
    response = await client.post("/api/review/base", json=sample_request)
    assert response.status_code == 200
    assert response.json()["model_name"]


@pytest.mark.asyncio
async def test_review_empty_code_rejected(client):
    response = await client.post("/api/review", json={"code": "", "language": "python"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_sql_injection_detected(client):
    payload = {
        "code": 'def get_user(u):\n    return db.execute("SELECT * FROM users WHERE name = \'" + u + "\'")',
        "language": "python",
    }
    response = await client.post("/api/review/finetuned", json=payload)
    assert response.status_code == 200
    types = [c["type"] for c in response.json()["comments"]]
    assert "security" in types


@pytest.mark.asyncio
async def test_cors_headers(client):
    response = await client.options(
        "/api/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code in (200, 204)
