import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app

@pytest.mark.asyncio
async def test_get_question_bank_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/edunote/quiz/questions/notebook:empty")
    assert resp.status_code == 200
    assert resp.json() == []

@pytest.mark.asyncio
async def test_generate_quiz_no_notes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/edunote/quiz/generate/notebook:empty")
    assert resp.status_code in [200, 404]
