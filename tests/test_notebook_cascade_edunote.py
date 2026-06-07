"""Deleting a notebook must also remove the EduNote study artifacts tied to it,
otherwise orphaned questions/flashcards/topics linger in the database.

DB-backed test (same pattern as the other route tests).
"""

import pytest

from open_notebook.domain.notebook import Notebook
from open_notebook.domain.edunote import (
    Question, Flashcard, FlashcardReview, ExamPaper, ExamTopic,
    QuizAttempt, AnswerRecord, StudySession,
)
from open_notebook.database.repository import repo_query


@pytest.mark.asyncio
async def test_deleting_notebook_cascades_edunote_content():
    nb_obj = Notebook(name="cascade test", description="temp")
    await nb_obj.save()
    nb = str(nb_obj.id)

    q = Question(notebook_id=nb, question="q?",
                 options=["A) a", "B) b", "C) c", "D) d"],
                 correct="A", topic="T", explanation="")
    await q.save()
    fc = Flashcard(notebook_id=nb, front="f", back="b", topic="T")
    await fc.save()
    rev = FlashcardReview(flashcard_id=str(fc.id), user_id="user:x", is_correct=True)
    await rev.save()
    ep = ExamPaper(notebook_id=nb, file_name="source:1")
    await ep.save()
    et = ExamTopic(exam_paper_id=str(ep.id), notebook_id=nb,
                   topic="T", count=1, description="")
    await et.save()
    qa = QuizAttempt(notebook_id=nb, user_id="user:x", question_ids=[str(q.id)])
    await qa.save()
    ar = AnswerRecord(attempt_id=str(qa.id), question_id=str(q.id),
                      chosen="A", is_correct=True, topic="T")
    await ar.save()
    ss = StudySession(notebook_id=nb, user_id="user:x", activity_type="quiz")
    await ss.save()

    fc_id, qa_id = str(fc.id), str(qa.id)

    try:
        await nb_obj.delete()

        for table in ("question", "flashcard", "exam_paper", "exam_topic",
                      "quiz_attempt", "study_session"):
            rows = await repo_query(
                f"SELECT id FROM {table} WHERE notebook_id=$nb", {"nb": nb}
            )
            assert rows == [], f"{table} left orphaned"

        rev_rows = await repo_query(
            "SELECT id FROM flashcard_review WHERE flashcard_id=$fid", {"fid": fc_id}
        )
        assert rev_rows == [], "flashcard_review left orphaned"
        ar_rows = await repo_query(
            "SELECT id FROM answer_record WHERE attempt_id=$aid", {"aid": qa_id}
        )
        assert ar_rows == [], "answer_record left orphaned"
    finally:
        # Defensive cleanup in case the cascade (or the test) left anything behind.
        for table in ("question", "flashcard", "exam_paper", "exam_topic",
                      "quiz_attempt", "study_session"):
            await repo_query(f"DELETE {table} WHERE notebook_id=$nb", {"nb": nb})
        await repo_query("DELETE flashcard_review WHERE flashcard_id=$fid", {"fid": fc_id})
        await repo_query("DELETE answer_record WHERE attempt_id=$aid", {"aid": qa_id})
