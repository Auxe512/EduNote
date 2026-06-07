"""Route tests for the progress API (hit the real SurrealDB)."""

import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from api.main import app
from open_notebook.database.repository import repo_query


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_record_note_session_persists_and_counts_streak():
    """Recording a note-read session (with a note_id) must persist and count
    toward today's streak.

    Regression: study_session.note_id was typed record<note> while the API sends
    a plain string id, so note-read sessions failed to save.
    """
    nb = f"notebook:{uuid.uuid4().hex}"
    user = f"user:{uuid.uuid4().hex}"
    note = f"note:{uuid.uuid4().hex}"

    try:
        async with _client() as client:
            saved = await client.post(
                "/api/edunote/progress/session",
                json={"user_id": user, "notebook_id": nb,
                      "note_id": note, "activity_type": "note"},
            )
            assert saved.status_code == 200, saved.text
            assert saved.json()["saved"] is True

            prog = await client.get(f"/api/edunote/progress/{nb}/{user}")
        data = prog.json()
        assert data["streak_days"] == 1
    finally:
        await repo_query("DELETE study_session WHERE user_id=$uid", {"uid": user})
