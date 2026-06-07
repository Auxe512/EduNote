import uuid

import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app
from open_notebook.domain.edunote import Question, QuizAttempt
from open_notebook.database.repository import repo_query


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_get_question_bank_empty():
    async with _client() as client:
        resp = await client.get("/api/edunote/quiz/questions/notebook:empty")
    assert resp.status_code == 200
    assert resp.json() == []

@pytest.mark.asyncio
async def test_generate_quiz_no_notes():
    async with _client() as client:
        resp = await client.post("/api/edunote/quiz/generate/notebook:empty")
    assert resp.status_code in [200, 404]


@pytest.mark.asyncio
async def test_submit_answer_is_idempotent_per_question():
    """Answering the same question twice must not create two answer_records,
    which would otherwise inflate the denominator of the quiz score."""
    nb = f"notebook:{uuid.uuid4().hex}"
    user = f"user:{uuid.uuid4().hex}"
    q = Question(
        notebook_id=nb, question="2+2?",
        options=["A) 3", "B) 4", "C) 5", "D) 6"],
        correct="B", topic="Math", explanation="",
    )
    await q.save()
    qid = str(q.id)
    attempt = QuizAttempt(notebook_id=nb, user_id=user, question_ids=[qid])
    await attempt.save()
    aid = str(attempt.id)

    try:
        async with _client() as client:
            first = await client.post(
                f"/api/edunote/quiz/attempt/{aid}/answer",
                json={"question_id": qid, "chosen": "B"},
            )
            assert first.status_code == 200, first.text
            assert first.json()["is_correct"] is True
            await client.post(
                f"/api/edunote/quiz/attempt/{aid}/answer",
                json={"question_id": qid, "chosen": "A"},
            )
        recs = await repo_query(
            "SELECT id FROM answer_record WHERE attempt_id=$aid", {"aid": aid}
        )
        assert len(recs) == 1
    finally:
        await repo_query("DELETE answer_record WHERE attempt_id=$aid", {"aid": aid})
        await repo_query("DELETE quiz_attempt WHERE notebook_id=$nb", {"nb": nb})
        await repo_query("DELETE question WHERE notebook_id=$nb", {"nb": nb})


@pytest.mark.asyncio
async def test_complete_quiz_scores_and_ranks_weak_topics():
    """End-to-end scoring: answer one right and one wrong, complete, and verify
    the score, counts, and weak-topic ranking — also reflected by /result."""
    nb = f"notebook:{uuid.uuid4().hex}"
    user = f"user:{uuid.uuid4().hex}"
    q1 = Question(notebook_id=nb, question="q1", options=["A) a", "B) b", "C) c", "D) d"],
                  correct="A", topic="Easy", explanation="")
    q2 = Question(notebook_id=nb, question="q2", options=["A) a", "B) b", "C) c", "D) d"],
                  correct="A", topic="Hard", explanation="")
    await q1.save()
    await q2.save()
    qid1, qid2 = str(q1.id), str(q2.id)
    attempt = QuizAttempt(notebook_id=nb, user_id=user, question_ids=[qid1, qid2])
    await attempt.save()
    aid = str(attempt.id)

    try:
        async with _client() as client:
            await client.post(f"/api/edunote/quiz/attempt/{aid}/answer",
                              json={"question_id": qid1, "chosen": "A"})  # correct
            await client.post(f"/api/edunote/quiz/attempt/{aid}/answer",
                              json={"question_id": qid2, "chosen": "B"})  # wrong
            done = await client.post(f"/api/edunote/quiz/attempt/{aid}/complete")
            result = await client.get(f"/api/edunote/quiz/attempt/{aid}/result")

        body = done.json()
        assert body["score"] == 50.0
        assert body["correct"] == 1
        assert body["total"] == 2
        assert body["weak_topics"][0]["topic"] == "Hard"
        assert body["weak_topics"][0]["error_rate"] == 1.0

        rbody = result.json()
        assert rbody["completed"] is True
        assert rbody["score"] == 50.0
        assert rbody["correct"] == 1
    finally:
        await repo_query("DELETE answer_record WHERE attempt_id=$aid", {"aid": aid})
        await repo_query("DELETE quiz_attempt WHERE notebook_id=$nb", {"nb": nb})
        await repo_query("DELETE question WHERE notebook_id=$nb", {"nb": nb})
