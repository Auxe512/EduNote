from typing import ClassVar, Optional, List
from datetime import datetime
from open_notebook.domain.base import ObjectModel


class ExamPaper(ObjectModel):
    table_name: ClassVar[str] = "exam_paper"
    notebook_id: str
    file_name: str
    created_at: Optional[datetime] = None


class ExamTopic(ObjectModel):
    table_name: ClassVar[str] = "exam_topic"
    exam_paper_id: str
    notebook_id: str
    topic: str
    count: int
    description: str


class Question(ObjectModel):
    table_name: ClassVar[str] = "question"
    notebook_id: str
    question: str
    options: List[str]
    correct: str
    topic: str
    explanation: str
    created_at: Optional[datetime] = None


class QuizAttempt(ObjectModel):
    table_name: ClassVar[str] = "quiz_attempt"
    notebook_id: str
    user_id: str
    question_ids: List[str]
    score: Optional[float] = None
    completed: bool = False
    created_at: Optional[datetime] = None


class AnswerRecord(ObjectModel):
    table_name: ClassVar[str] = "answer_record"
    attempt_id: str
    question_id: str
    chosen: str
    is_correct: bool
    topic: str


class Flashcard(ObjectModel):
    table_name: ClassVar[str] = "flashcard"
    notebook_id: str
    front: str
    back: str
    topic: str
    created_at: Optional[datetime] = None


class FlashcardReview(ObjectModel):
    table_name: ClassVar[str] = "flashcard_review"
    flashcard_id: str
    user_id: str
    is_correct: bool
    reviewed_at: Optional[datetime] = None


class StudySession(ObjectModel):
    table_name: ClassVar[str] = "study_session"
    user_id: str
    notebook_id: str
    note_id: Optional[str] = None
    activity_type: str
    started_at: Optional[datetime] = None
