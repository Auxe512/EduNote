from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from api.edunote.exam import analyze_exam, AnalyzeRequest
from api.edunote.quiz import generate_questions
from api.edunote.flashcards import generate_flashcards

router = APIRouter(prefix="/edunote/quickprep", tags=["quickprep"])

class QuickPrepRequest(BaseModel):
    exam_source_id: Optional[str] = None

@router.post("/{notebook_id}")
async def quick_prep(notebook_id: str, req: QuickPrepRequest):
    results = {}

    if req.exam_source_id:
        try:
            result = await analyze_exam(AnalyzeRequest(
                notebook_id=notebook_id,
                source_id=req.exam_source_id
            ))
            results["exam_analysis"] = result
        except Exception as e:
            results["exam_analysis"] = {"error": str(e)}
    else:
        results["exam_analysis"] = {"skipped": "no exam source provided"}

    try:
        results["quiz"] = await generate_questions(notebook_id)
    except Exception as e:
        results["quiz"] = {"error": str(e)}

    try:
        results["flashcards"] = await generate_flashcards(notebook_id)
    except Exception as e:
        results["flashcards"] = {"error": str(e)}

    return results
