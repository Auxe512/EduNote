"""Route tests for the flashcards API.

These hit the real SurrealDB (same pattern as test_exam_routes / test_quiz_routes),
so they require the database to be running. Each DB-mutating test uses a unique
notebook/user id and cleans up after itself.
"""

import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from api.main import app
from open_notebook.domain.edunote import Flashcard
from open_notebook.database.repository import repo_query


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_get_flashcards_empty_for_unknown_notebook():
    async with _client() as client:
        resp = await client.get("/api/edunote/flashcards/notebook:__no_such_nb__")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_flashcard_review_roundtrip_and_stats():
    """A student taps 'remembered' on a card -> the review persists and shows in stats.

    Regression: a stray required `notebook_id` column on flashcard_review made
    every review save fail with HTTP 500.
    """
    notebook_id = f"notebook:{uuid.uuid4().hex}"
    user_id = f"user:{uuid.uuid4().hex}"
    card = Flashcard(notebook_id=notebook_id, front="Q?", back="A.", topic="T")
    await card.save()
    card_id = str(card.id)

    try:
        async with _client() as client:
            review = await client.post(
                f"/api/edunote/flashcards/{card_id}/review",
                json={"user_id": user_id, "is_correct": True},
            )
            assert review.status_code == 200, review.text
            assert review.json()["saved"] is True

            stats = await client.get(
                f"/api/edunote/flashcards/{notebook_id}/stats/{user_id}"
            )
        assert stats.status_code == 200
        data = stats.json()
        assert data["total_reviewed"] == 1
        assert data["correct"] == 1
    finally:
        await repo_query("DELETE flashcard_review WHERE user_id=$uid", {"uid": user_id})
        await repo_query("DELETE flashcard WHERE notebook_id=$nb", {"nb": notebook_id})
