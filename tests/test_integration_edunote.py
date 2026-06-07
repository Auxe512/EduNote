"""Integration tests for the EduNote API flows.

These mock the Groq AI calls and the SurrealDB layer (`repo_query` / domain
`.save()`), so they run without a database or network. Patch targets are the
*use sites* (e.g. ``api.edunote.exam.repo_query``) because each module imports
the symbol with ``from ... import``, binding its own name.
"""

import pytest
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

from api.main import app
from open_notebook.exceptions import NotFoundError


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


MOCK_TOPICS = [
    {"topic": "Pipeline Hazards", "count": 8, "description": "Data/control hazards"},
    {"topic": "Cache", "count": 5, "description": "Cache mapping"},
]


# --------------------------------------------------------------------------- #
# Exam analyze                                                                 #
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_exam_analyze_returns_cached_when_paper_exists():
    """If the source was already analyzed, return cached topics without calling AI."""
    repo = AsyncMock(side_effect=[
        [{"id": "exam_paper:abc"}],                    # existing_paper lookup
        [{"topic": "Pipeline Hazards", "count": 8}],   # existing_topics
    ])
    with patch("api.edunote.exam.repo_query", new=repo), \
         patch("api.edunote.exam.groq.call_json", new=AsyncMock()) as groq_call:
        async with _client() as client:
            resp = await client.post(
                "/api/edunote/exam/analyze",
                json={"notebook_id": "notebook:test", "source_id": "source:test"},
            )
    assert resp.status_code == 200
    body = resp.json()
    assert body["cached"] is True
    assert body["topics"][0]["topic"] == "Pipeline Hazards"
    groq_call.assert_not_called()  # cached path must not hit the LLM


@pytest.mark.asyncio
async def test_exam_analyze_404_when_source_missing():
    with patch("api.edunote.exam.repo_query", new=AsyncMock(return_value=[])), \
         patch("api.edunote.exam.Source.get", new=AsyncMock(side_effect=NotFoundError("nope"))):
        async with _client() as client:
            resp = await client.post(
                "/api/edunote/exam/analyze",
                json={"notebook_id": "notebook:test", "source_id": "source:missing"},
            )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_exam_analyze_422_when_source_has_no_text():
    """Image-only PDFs (no text layer) should fail clearly, not silently."""
    fake_source = SimpleNamespace(full_text="")
    with patch("api.edunote.exam.repo_query", new=AsyncMock(return_value=[])), \
         patch("api.edunote.exam.Source.get", new=AsyncMock(return_value=fake_source)):
        async with _client() as client:
            resp = await client.post(
                "/api/edunote/exam/analyze",
                json={"notebook_id": "notebook:test", "source_id": "source:empty"},
            )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_exam_analyze_fresh_generates_topics():
    """Full happy path: source text -> AI topics -> persisted -> returned."""
    fake_source = SimpleNamespace(full_text="Q1 pipeline hazards. Q2 cache mapping.")

    def make_paper(**kw):
        return SimpleNamespace(id="exam_paper:new", save=AsyncMock(), **kw)

    def make_topic(**kw):
        return SimpleNamespace(save=AsyncMock(), **kw)

    with patch("api.edunote.exam.repo_query", new=AsyncMock(return_value=[])), \
         patch("api.edunote.exam.Source.get", new=AsyncMock(return_value=fake_source)), \
         patch("api.edunote.exam.groq.call_json", new=AsyncMock(return_value=MOCK_TOPICS)), \
         patch("api.edunote.exam.ExamPaper", side_effect=make_paper), \
         patch("api.edunote.exam.ExamTopic", side_effect=make_topic):
        async with _client() as client:
            resp = await client.post(
                "/api/edunote/exam/analyze",
                json={"notebook_id": "notebook:test", "source_id": "source:exam"},
            )
    assert resp.status_code == 200
    body = resp.json()
    assert body["exam_paper_id"] == "exam_paper:new"
    assert {t["topic"] for t in body["topics"]} == {"Pipeline Hazards", "Cache"}


# --------------------------------------------------------------------------- #
# Progress                                                                     #
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_progress_zero_state():
    """A brand-new student with no activity gets an all-zero dashboard."""
    with patch("api.edunote.progress.repo_query", new=AsyncMock(return_value=[])):
        async with _client() as client:
            resp = await client.get("/api/edunote/progress/notebook:test/user:test")
    assert resp.status_code == 200
    data = resp.json()
    assert data["completion_rate"] == 0
    assert data["streak_days"] == 0
    assert data["quiz_count"] == 0
    assert data["weak_topics"] == []


@pytest.mark.asyncio
async def test_progress_completion_capped_at_100():
    """Regression: more activities than notes must not produce >100% or read>total."""
    repo = AsyncMock(side_effect=[
        [{"count": 2}],    # total_notes
        [{"count": 10}],   # activity_count (5x the note count)
        [],                # quiz attempts
        [],                # sessions (streak)
        [],                # weak_rows
    ])
    with patch("api.edunote.progress.repo_query", new=repo):
        async with _client() as client:
            resp = await client.get("/api/edunote/progress/notebook:test/user:test")
    data = resp.json()
    assert data["completion_rate"] == 100   # capped, not 500
    assert data["read_notes"] == 2          # min(activity, total), not 10
    assert data["total_notes"] == 2


# --------------------------------------------------------------------------- #
# Quiz                                                                         #
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_quiz_generate_skips_when_bank_full():
    """With >=25 cached questions, generation is skipped (no AI call)."""
    with patch("api.edunote.quiz.repo_query", new=AsyncMock(return_value=[{"count": 25}])), \
         patch("api.edunote.quiz.groq.call_json", new=AsyncMock()) as groq_call:
        async with _client() as client:
            resp = await client.post("/api/edunote/quiz/generate/notebook:test")
    assert resp.status_code == 200
    assert resp.json()["generated"] == 0
    groq_call.assert_not_called()


@pytest.mark.asyncio
async def test_quiz_result_computes_score_and_weak_topics():
    """Completed attempt result includes per-topic error rates, worst first."""
    repo = AsyncMock(side_effect=[
        [{"id": "quiz_attempt:1", "completed": True, "score": 50.0}],  # attempt
        [                                                              # answer_records
            {"is_correct": True, "topic": "Pipeline"},
            {"is_correct": False, "topic": "Pipeline"},
            {"is_correct": False, "topic": "Cache"},
        ],
    ])
    with patch("api.edunote.quiz.repo_query", new=repo):
        async with _client() as client:
            resp = await client.get("/api/edunote/quiz/attempt/quiz_attempt:1/result")
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] == 1
    assert data["total"] == 3
    # Cache is 100% wrong, Pipeline 50% wrong -> Cache ranks first
    assert data["weak_topics"][0]["topic"] == "Cache"
    assert data["weak_topics"][0]["error_rate"] == 1.0
