from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from open_notebook.domain.edunote import ExamPaper, ExamTopic
from open_notebook.domain.notebook import Source
from open_notebook.exceptions import NotFoundError
from open_notebook.services.groq_service import GroqService
from open_notebook.database.repository import repo_query

router = APIRouter(prefix="/edunote/exam", tags=["exam"])
groq = GroqService()

ANALYZE_SYSTEM = """You are an exam analyst. Given past exam questions, identify recurring topics.
Return ONLY a JSON array with objects: {"topic": string, "count": int, "description": string}.
Be specific — "Pipeline Hazards" not just "Pipeline"."""


class AnalyzeRequest(BaseModel):
    notebook_id: str
    source_id: str


@router.post("/analyze")
async def analyze_exam(req: AnalyzeRequest):
    # Prevent re-analyzing the same source
    existing_paper = await repo_query(
        "SELECT id FROM exam_paper WHERE notebook_id=$nb AND file_name=$sid",
        {"nb": req.notebook_id, "sid": req.source_id}
    )
    if existing_paper:
        existing_topics = await repo_query(
            "SELECT * FROM exam_topic WHERE exam_paper_id=$pid ORDER BY `count` DESC",
            {"pid": str(existing_paper[0]["id"])}
        )
        return {"exam_paper_id": str(existing_paper[0]["id"]), "topics": existing_topics, "cached": True}

    try:
        source = await Source.get(req.source_id)
    except NotFoundError:
        raise HTTPException(404, "Source not found")

    exam_text = source.full_text or ""
    if not exam_text:
        raise HTTPException(422, "Source has no text content — please upload a text-layer PDF")

    # Groq free tier: 6000 TPM limit. ~4000 chars ≈ 4500 tokens for mixed Chinese/English
    exam_text = exam_text[:4000]

    topics_raw = await groq.call_json(
        ANALYZE_SYSTEM,
        f"Past exam questions:\n{exam_text}"
    )

    paper = ExamPaper(notebook_id=req.notebook_id, file_name=req.source_id)
    await paper.save()

    saved_topics = []
    for t in topics_raw:
        topic = ExamTopic(
            exam_paper_id=str(paper.id),
            notebook_id=req.notebook_id,
            topic=t["topic"],
            count=t["count"],
            description=t.get("description", "")
        )
        await topic.save()
        saved_topics.append(topic)

    return {
        "exam_paper_id": str(paper.id),
        "topics": [{"topic": t.topic, "count": t.count, "description": t.description} for t in saved_topics]
    }


@router.delete("/topics/{notebook_id}")
async def clear_topics(notebook_id: str):
    await repo_query("DELETE exam_topic WHERE notebook_id=$nb", {"nb": notebook_id})
    await repo_query("DELETE exam_paper WHERE notebook_id=$nb", {"nb": notebook_id})
    return {"cleared": True}


@router.get("/topics/{notebook_id}")
async def get_topics(notebook_id: str):
    rows = await repo_query(
        "SELECT * FROM exam_topic WHERE notebook_id=$nb ORDER BY `count` DESC",
        {"nb": notebook_id}
    )
    return rows or []
