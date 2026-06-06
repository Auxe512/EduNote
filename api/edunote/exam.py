from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from open_notebook.domain.edunote import ExamPaper, ExamTopic
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
    rows = await repo_query(
        "SELECT * FROM source WHERE id=$id",
        {"id": req.source_id}
    )
    if not rows:
        raise HTTPException(404, "Source not found")

    # Source stores text content in full_text field
    source = rows[0]
    exam_text = source.get("full_text") or ""
    if not exam_text:
        raise HTTPException(404, "Source has no text content")

    exam_text = exam_text[:12000]

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


@router.get("/topics/{notebook_id}")
async def get_topics(notebook_id: str):
    rows = await repo_query(
        "SELECT * FROM exam_topic WHERE notebook_id=$nb ORDER BY count DESC",
        {"nb": notebook_id}
    )
    return rows or []
