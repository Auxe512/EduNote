from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from open_notebook.domain.edunote import Flashcard, FlashcardReview
from open_notebook.services.groq_service import GroqService
from open_notebook.database.repository import repo_query

router = APIRouter(prefix="/edunote/flashcards", tags=["flashcards"])
groq = GroqService()

CARD_SYSTEM = """You generate flashcards for studying. Return ONLY a JSON array.
Each object must have:
- "front": concise question (max 20 words)
- "back": concise answer (max 40 words)
- "topic": topic name"""

@router.get("/{notebook_id}")
async def get_flashcards(notebook_id: str):
    rows = await repo_query(
        "SELECT * FROM flashcard WHERE notebook_id=$nb",
        {"nb": notebook_id}
    )
    return rows or []

@router.post("/generate/{notebook_id}")
async def generate_flashcards(notebook_id: str):
    existing = await repo_query(
        "SELECT count() FROM flashcard WHERE notebook_id=$nb GROUP ALL",
        {"nb": notebook_id}
    )
    if existing and existing[0].get("count", 0) >= 10:
        return {"message": "Flashcards already exist", "generated": 0}

    notes_rows = await repo_query(
        "SELECT note.content as content FROM (SELECT in AS note FROM artifact WHERE out=type::thing($nb) FETCH note)",
        {"nb": notebook_id}
    )
    if not notes_rows:
        raise HTTPException(404, "No notes found in notebook")

    notes_text = "\n\n".join(r.get("content", "") for r in notes_rows)[:4000]

    topics_rows = await repo_query(
        "SELECT topic, `count` FROM exam_topic WHERE notebook_id=$nb ORDER BY `count` DESC LIMIT 8",
        {"nb": notebook_id}
    )
    topic_hint = ""
    if topics_rows:
        topic_list = ", ".join(t["topic"] for t in topics_rows)
        topic_hint = f"\nFocus especially on: {topic_list}"

    cards_raw = await groq.call_json(
        CARD_SYSTEM,
        f"Notes:\n{notes_text}{topic_hint}\n\nGenerate exactly 8 flashcards. Return ONLY the JSON array, no other text."
    )
    if not isinstance(cards_raw, list):
        raise HTTPException(502, "AI returned invalid format")

    saved = []
    for c in cards_raw[:8]:
        card = Flashcard(
            notebook_id=notebook_id,
            front=c["front"],
            back=c["back"],
            topic=c.get("topic", "General")
        )
        await card.save()
        saved.append(card)

    return {"generated": len(saved)}

class ReviewRequest(BaseModel):
    user_id: str
    is_correct: bool

@router.post("/{card_id}/review")
async def review_flashcard(card_id: str, req: ReviewRequest):
    review = FlashcardReview(
        flashcard_id=card_id,
        user_id=req.user_id,
        is_correct=req.is_correct
    )
    await review.save()
    return {"saved": True}

@router.get("/{notebook_id}/stats/{user_id}")
async def get_flashcard_stats(notebook_id: str, user_id: str):
    # flashcard_id is stored as a plain string, so we can't traverse
    # flashcard_id.notebook_id. Resolve the notebook's card ids first, then
    # match reviews against that string list.
    cards = await repo_query(
        "SELECT id FROM flashcard WHERE notebook_id=$nb",
        {"nb": notebook_id}
    )
    card_ids = [str(c["id"]) for c in cards]
    if not card_ids:
        return {"total_reviewed": 0, "correct": 0}

    rows = await repo_query(
        "SELECT is_correct FROM flashcard_review "
        "WHERE user_id=$uid AND flashcard_id IN $ids",
        {"uid": user_id, "ids": card_ids}
    )
    total = len(rows)
    correct = sum(1 for r in rows if r["is_correct"])
    return {"total_reviewed": total, "correct": correct}
