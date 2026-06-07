import random
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from open_notebook.domain.edunote import Question, QuizAttempt, AnswerRecord
from open_notebook.services.groq_service import GroqService
from open_notebook.database.repository import repo_query

router = APIRouter(prefix="/edunote/quiz", tags=["quiz"])
groq = GroqService()

QUIZ_SYSTEM = """You are an exam question writer. Generate multiple choice questions.
Return ONLY a JSON array. Each object must have:
- "question": string
- "options": array of exactly 4 strings starting with "A) ", "B) ", "C) ", "D) "
- "correct": one of "A", "B", "C", "D"
- "topic": string
- "explanation": string (1 sentence)"""


@router.get("/questions/{notebook_id}")
async def get_question_bank(notebook_id: str):
    rows = await repo_query(
        "SELECT * FROM question WHERE notebook_id=$nb",
        {"nb": notebook_id}
    )
    return rows or []


@router.post("/generate/{notebook_id}")
async def generate_questions(notebook_id: str):
    existing = await repo_query(
        "SELECT count() FROM question WHERE notebook_id=$nb GROUP ALL",
        {"nb": notebook_id}
    )
    if existing and existing[0].get("count", 0) >= 25:
        return {"message": "Question bank is full", "generated": 0}

    # Notes relate to notebooks via the artifact RELATION table (FROM note TO notebook)
    notes_rows = await repo_query(
        "SELECT note.content as content FROM (SELECT in AS note FROM artifact WHERE out=type::thing($nb) FETCH note)",
        {"nb": notebook_id}
    )
    if not notes_rows:
        raise HTTPException(404, "No notes found in this notebook")

    notes_text = "\n\n".join(r.get("content", "") for r in notes_rows if r.get("content"))[:4000]
    if not notes_text.strip():
        raise HTTPException(404, "No notes found in this notebook")

    topics_rows = await repo_query(
        "SELECT topic, `count` FROM exam_topic WHERE notebook_id=$nb ORDER BY `count` DESC LIMIT 10",
        {"nb": notebook_id}
    )

    topic_section = ""
    if topics_rows:
        topic_list = ", ".join(f"{t['topic']}({t['count']}x)" for t in topics_rows)
        topic_section = f"\n\nFocus on these high-frequency exam topics: {topic_list}"

    user_msg = f"Student notes:\n{notes_text}{topic_section}\n\nGenerate exactly 10 multiple choice questions. Return ONLY the JSON array, no other text."

    questions_raw = await groq.call_json(QUIZ_SYSTEM, user_msg)
    if not isinstance(questions_raw, list):
        raise HTTPException(500, "AI returned invalid format")

    saved = []
    for q in questions_raw[:12]:
        question = Question(
            notebook_id=notebook_id,
            question=q["question"],
            options=q["options"],
            correct=q["correct"],
            topic=q.get("topic", "General"),
            explanation=q.get("explanation", "")
        )
        await question.save()
        saved.append(question)

    return {"generated": len(saved)}


@router.post("/start/{notebook_id}")
async def start_quiz(notebook_id: str, user_id: str):
    questions = await repo_query(
        "SELECT id FROM question WHERE notebook_id=$nb",
        {"nb": notebook_id}
    )
    if not questions:
        raise HTTPException(404, "No questions yet. Call /generate first.")

    ids = [str(q["id"]) for q in questions]
    sampled = random.sample(ids, min(10, len(ids)))

    attempt = QuizAttempt(
        notebook_id=notebook_id,
        user_id=user_id,
        question_ids=sampled
    )
    await attempt.save()
    return {"attempt_id": str(attempt.id), "question_ids": sampled}


class AnswerRequest(BaseModel):
    question_id: str
    chosen: str


@router.post("/attempt/{attempt_id}/answer")
async def submit_answer(attempt_id: str, req: AnswerRequest):
    q_rows = await repo_query(
        "SELECT correct, topic FROM type::thing($id)",
        {"id": req.question_id}
    )
    if not q_rows:
        raise HTTPException(404, "Question not found")

    question = q_rows[0]
    is_correct = req.chosen.upper() == question["correct"].upper()

    record = AnswerRecord(
        attempt_id=attempt_id,
        question_id=req.question_id,
        chosen=req.chosen,
        is_correct=is_correct,
        topic=question["topic"]
    )
    await record.save()
    return {"is_correct": is_correct, "correct": question["correct"]}


@router.post("/attempt/{attempt_id}/complete")
async def complete_quiz(attempt_id: str):
    records = await repo_query(
        "SELECT is_correct, topic FROM answer_record WHERE attempt_id=$id",
        {"id": attempt_id}
    )
    if not records:
        raise HTTPException(404, "No answers found for this attempt")

    total = len(records)
    correct = sum(1 for r in records if r["is_correct"])
    score = round(correct / total * 100, 1)

    topic_stats: dict = {}
    for r in records:
        t = r["topic"]
        if t not in topic_stats:
            topic_stats[t] = {"correct": 0, "total": 0}
        topic_stats[t]["total"] += 1
        if r["is_correct"]:
            topic_stats[t]["correct"] += 1

    weak_topics = [
        {"topic": t, "error_rate": round(1 - v["correct"] / v["total"], 2)}
        for t, v in topic_stats.items()
        if v["total"] > 0
    ]
    weak_topics.sort(key=lambda x: x["error_rate"], reverse=True)

    await repo_query(
        "UPDATE type::thing($id) SET score=$score, completed=true",
        {"id": attempt_id, "score": score}
    )

    return {"score": score, "correct": correct, "total": total, "weak_topics": weak_topics}


@router.get("/attempt/{attempt_id}/result")
async def get_result(attempt_id: str):
    rows = await repo_query(
        "SELECT * FROM type::thing($id)",
        {"id": attempt_id}
    )
    if not rows:
        raise HTTPException(404, "Attempt not found")
    attempt = rows[0]

    if not attempt.get("completed"):
        return attempt

    # Compute result stats from answer_record
    records = await repo_query(
        "SELECT is_correct, topic FROM answer_record WHERE attempt_id=$id",
        {"id": attempt_id}
    )
    total = len(records)
    correct = sum(1 for r in records if r["is_correct"])
    topic_stats: dict = {}
    for r in records:
        t = r["topic"]
        if t not in topic_stats:
            topic_stats[t] = {"correct": 0, "total": 0}
        topic_stats[t]["total"] += 1
        if r["is_correct"]:
            topic_stats[t]["correct"] += 1
    weak_topics = sorted(
        [{"topic": t, "error_rate": round(1 - v["correct"] / v["total"], 2)}
         for t, v in topic_stats.items()],
        key=lambda x: x["error_rate"], reverse=True
    )

    attempt["correct"] = correct
    attempt["total"] = total
    attempt["weak_topics"] = weak_topics
    return attempt
