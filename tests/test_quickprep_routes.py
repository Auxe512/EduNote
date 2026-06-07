"""Tests for the quickprep orchestration endpoint.

The three sub-steps are patched at their use sites in api.edunote.quickprep, so
these run without a database or AI calls.
"""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

from api.main import app


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_quickprep_runs_all_steps_with_exam_source():
    with patch("api.edunote.quickprep.analyze_exam",
               new=AsyncMock(return_value={"topics": [{"topic": "Cache"}]})), \
         patch("api.edunote.quickprep.generate_questions",
               new=AsyncMock(return_value={"generated": 10})), \
         patch("api.edunote.quickprep.generate_flashcards",
               new=AsyncMock(return_value={"generated": 8})):
        async with _client() as client:
            resp = await client.post(
                "/api/edunote/quickprep/notebook:test",
                json={"exam_source_id": "source:x"},
            )
    assert resp.status_code == 200
    body = resp.json()
    assert body["exam_analysis"]["topics"][0]["topic"] == "Cache"
    assert body["quiz"]["generated"] == 10
    assert body["flashcards"]["generated"] == 8


@pytest.mark.asyncio
async def test_quickprep_skips_exam_and_isolates_step_errors():
    """No exam source -> exam step skipped; a failing step is reported without
    aborting the others."""
    with patch("api.edunote.quickprep.generate_questions",
               new=AsyncMock(side_effect=Exception("groq down"))), \
         patch("api.edunote.quickprep.generate_flashcards",
               new=AsyncMock(return_value={"generated": 8})):
        async with _client() as client:
            resp = await client.post(
                "/api/edunote/quickprep/notebook:test",
                json={},
            )
    assert resp.status_code == 200
    body = resp.json()
    assert body["exam_analysis"] == {"skipped": "no exam source provided"}
    assert body["quiz"] == {"error": "groq down"}
    assert body["flashcards"]["generated"] == 8
