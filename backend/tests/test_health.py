"""
API 헬스/세션 엔드포인트 테스트
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    async with client as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_generate_missing_ticker(client):
    async with client as ac:
        response = await ac.post("/api/stock/generate", json={})
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_generate_empty_ticker(client):
    async with client as ac:
        response = await ac.post("/api/stock/generate", json={"ticker": ""})
    assert response.status_code == 422



