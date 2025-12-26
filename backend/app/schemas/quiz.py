# backend/app/schemas/quiz.py

"""
Quiz schemas for quiz lifecycle management.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================
# REQUEST SCHEMAS
# ============================

class QuizGenerateRequest(BaseModel):
    """Request to generate a quiz."""
    subject_id: str = Field(..., description="Subject ID")
    chapter_number: Optional[int] = Field(None, ge=1, description="Chapter number")
    num_questions: int = Field(default=10, ge=1, le=50, description="Number of questions")
    quiz_type: str = Field(
        default="practice",
        pattern="^(practice|revision|mock_exam)$",
        description="Type of quiz"
    )
    difficulty: Optional[str] = Field(
        None,
        pattern="^(easy|medium|hard|mixed)$",
        description="Difficulty level"
    )


class QuizSubmitRequest(BaseModel):
    """Submit quiz answers request."""
    quiz_id: str = Field(..., description="Quiz ID")
    answers: Dict[str, str] = Field(
        ..., 
        description="Answers mapping question_id to answer (e.g., {'q1': 'B', 'q2': 'A'})"
    )
    started_at: datetime = Field(..., description="When the user started the quiz")


# ============================
# RESPONSE SCHEMAS
# ============================

class QuizQuestionResponse(BaseModel):
    """Quiz question (without correct answer for taking quiz)."""
    question_id: str
    question_number: int
    text: str
    question_type: str
    options: List[str]
    difficulty: str = "medium"
    marks: int = 1


class QuizResponse(BaseModel):
    """Quiz response (for taking)."""
    id: str
    subject_id: str
    subject: str
    chapter: str
    chapter_number: Optional[int] = None
    title: str
    description: str = ""
    quiz_type: str
    questions: List[QuizQuestionResponse]
    total_marks: int
    time_limit: Optional[int] = None
    pass_percentage: float = 60.0
    created_at: datetime

    class Config:
        from_attributes = True


class QuizListItem(BaseModel):
    """Quiz list item (summary)."""
    id: str
    title: str
    chapter: str
    chapter_number: Optional[int] = None
    quiz_type: str
    total_marks: int
    questions_count: int
    time_limit: Optional[int] = None
    created_at: datetime


class QuizListResponse(BaseModel):
    """List of quizzes response."""
    quizzes: List[QuizListItem]
    total: int


class QuestionResultResponse(BaseModel):
    """Result for a single question."""
    question_id: str
    question_number: int
    question_text: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    marks_obtained: float
    marks_possible: float
    explanation: str = ""
    concepts: List[str] = []


class QuizResultResponse(BaseModel):
    """Quiz result response."""
    id: str
    quiz_id: str
    subject_id: str
    score: float
    max_score: float
    percentage: float
    passed: bool
    time_taken_seconds: int
    question_results: List[QuestionResultResponse]
    strengths: List[str] = []
    weak_areas: List[str] = []
    completed_at: datetime

    class Config:
        from_attributes = True


class QuizResultListItem(BaseModel):
    """Quiz result list item."""
    id: str
    quiz_id: str
    quiz_title: str
    score: float
    max_score: float
    percentage: float
    passed: bool
    completed_at: datetime


class QuizResultListResponse(BaseModel):
    """List of quiz results."""
    results: List[QuizResultListItem]
    total: int


class QuizStatisticsResponse(BaseModel):
    """Quiz statistics response."""
    subject_id: str
    total_quizzes: int
    total_attempts: int
    average_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float
    total_questions_answered: int
    correct_answers: int
    accuracy: float
    strengths: List[str] = []
    weak_areas: List[str] = []
    recent_trend: str = "stable"  # improving | stable | declining
