from open_notebook.domain.edunote import (
    ExamPaper, ExamTopic, Question, QuizAttempt,
    AnswerRecord, Flashcard, FlashcardReview, StudySession
)

def test_model_table_names():
    assert ExamPaper.table_name == "exam_paper"
    assert ExamTopic.table_name == "exam_topic"
    assert Question.table_name == "question"
    assert QuizAttempt.table_name == "quiz_attempt"
    assert AnswerRecord.table_name == "answer_record"
    assert Flashcard.table_name == "flashcard"
    assert FlashcardReview.table_name == "flashcard_review"
    assert StudySession.table_name == "study_session"

def test_question_instantiation():
    q = Question(
        notebook_id="notebook:abc",
        question="What is Pipeline?",
        options=["A", "B", "C", "D"],
        correct="A",
        topic="Pipeline",
        explanation="Because A"
    )
    assert q.correct == "A"
    assert len(q.options) == 4

def test_flashcard_instantiation():
    f = Flashcard(
        notebook_id="notebook:abc",
        front="What is Cache?",
        back="A fast memory buffer",
        topic="Cache"
    )
    assert f.front == "What is Cache?"
