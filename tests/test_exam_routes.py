import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app

@pytest.mark.asyncio
async def test_get_exam_topics_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/edunote/exam/topics/notebook:test123")
    assert resp.status_code == 200
    assert resp.json() == []

@pytest.mark.asyncio
async def test_analyze_exam_invalid_source():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/edunote/exam/analyze",
            json={"notebook_id": "notebook:nonexistent", "source_id": "source:abc"}
        )
    assert resp.status_code in [404, 422, 500]
