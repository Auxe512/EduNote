from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from open_notebook.domain.edunote import StudySession
from open_notebook.database.repository import repo_query
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/edunote/progress", tags=["progress"])

class SessionRequest(BaseModel):
    user_id: str
    notebook_id: str
    note_id: Optional[str] = None
    activity_type: str  # "note" | "quiz" | "flashcard"

@router.post("/session")
async def record_session(req: SessionRequest):
    session = StudySession(
        user_id=req.user_id,
        notebook_id=req.notebook_id,
        note_id=req.note_id,
        activity_type=req.activity_type,
    )
    await session.save()
    return {"saved": True}

@router.get("/{notebook_id}/{user_id}")
async def get_progress(notebook_id: str, user_id: str):
    total_notes_rows = await repo_query(
        "SELECT count() FROM (SELECT in AS note FROM artifact WHERE out=type::thing($nb) FETCH note) GROUP ALL",
        {"nb": notebook_id}
    )
    total = total_notes_rows[0].get("count", 0) if total_notes_rows else 0

    activity_rows = await repo_query(
        "SELECT count() FROM study_session "
        "WHERE user_id=$uid AND notebook_id=$nb GROUP ALL",
        {"uid": user_id, "nb": notebook_id}
    )
    activity_count = activity_rows[0].get("count", 0) if activity_rows else 0
    if total > 0:
        completion_rate = min(100, round(activity_count / total * 100))
    elif activity_count > 0:
        completion_rate = min(100, activity_count * 20)  # 5 activities = 100%
    else:
        completion_rate = 0
    read = min(activity_count, total)

    attempts = await repo_query(
        "SELECT score FROM quiz_attempt "
        "WHERE user_id=$uid AND notebook_id=$nb AND completed=true",
        {"uid": user_id, "nb": notebook_id}
    )
    scores = [a["score"] for a in attempts if a.get("score") is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    sessions = await repo_query(
        "SELECT started_at FROM study_session "
        "WHERE user_id=$uid AND notebook_id=$nb ORDER BY started_at DESC",
        {"uid": user_id, "nb": notebook_id}
    )
    streak = _compute_streak(sessions)

    weak_rows = await repo_query(
        "SELECT topic, count() as total, "
        "math::sum(if is_correct then 0 else 1 end) as wrong "
        "FROM answer_record WHERE attempt_id IN "
        "(SELECT id FROM quiz_attempt WHERE user_id=$uid AND notebook_id=$nb) "
        "GROUP BY topic",
        {"uid": user_id, "nb": notebook_id}
    )
    weak_topics = [
        {"topic": r["topic"], "error_rate": round(r["wrong"] / r["total"], 2)}
        for r in (weak_rows or []) if r.get("total", 0) > 0
    ]
    weak_topics.sort(key=lambda x: x["error_rate"], reverse=True)

    return {
        "completion_rate": completion_rate,
        "total_notes": total,
        "read_notes": read,
        "avg_quiz_score": avg_score,
        "quiz_count": len(scores),
        "streak_days": streak,
        "weak_topics": weak_topics[:5],
    }

def _compute_streak(sessions: list) -> int:
    if not sessions:
        return 0
    today = datetime.now(timezone.utc).date()
    seen_days = set()
    for s in sessions:
        ts = s.get("started_at")
        if ts:
            day = datetime.fromisoformat(str(ts)).date() if isinstance(ts, str) else ts.date()
            seen_days.add(day)
    streak = 0
    current = today
    while current in seen_days:
        streak += 1
        current -= timedelta(days=1)
    return streak
