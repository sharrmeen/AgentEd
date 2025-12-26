# backend/app/core/models/quiz.py

"""
Quiz collection models.
Enhanced with question metadata, results, and concept tagging.
"""

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from .base import MongoBaseModel, PyObjectId


# ============================
# QUIZ QUESTION
# ============================

class QuizQuestion(BaseModel):
    """Individual quiz question with metadata."""
    
    question_id: PyObjectId = Field(default_factory=PyObjectId)
    question_number: int
    
    # Question content
    text: str
    question_type: str  # "mcq" | "short_answer" | "true_false"
    
    # MCQ specific
    options: List[str] = []  # For MCQ only
    correct_answer: str
    
    # Metadata
    explanation: str = ""  # Why this answer is correct
    difficulty: str = "medium"  # "easy" | "medium" | "hard"
    marks: int = 1
    
    # Concept tagging (for analytics)
    concepts: List[str] = []  # e.g., ["photosynthesis", "light_reactions"]
    learning_objectives: List[str] = []  # Links to chapter objectives


# ============================
# QUIZ DEFINITION
# ============================

class Quiz(MongoBaseModel):
    """Quiz definition stored in MongoDB."""
    
    # Ownership
    user_id: PyObjectId
    subject_id: PyObjectId
    session_id: Optional[PyObjectId] = None  # Optional: linked to study session
    
    # Context
    subject: str
    chapter: str  # Changed from "module" for consistency
    chapter_number: Optional[int] = None
    
    # Quiz metadata
    title: str
    description: str = ""
    quiz_type: str  # "practice" | "revision" | "mock_exam" | "adaptive"
    
    # Questions
    questions: List[QuizQuestion]
    total_marks: int
    
    # Settings
    time_limit: Optional[int] = None  # Minutes
    pass_percentage: float = 60.0  # Minimum % to pass
    
    # Generation metadata (from Quiz Agent)
    generated_by: str = "quiz_agent"  # "quiz_agent" | "manual"
    source_content: Optional[str] = None  # Content used to generate quiz
    
    # Status
    is_active: bool = True
    
    # Timestamps
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()


# ============================
# QUIZ ATTEMPT / RESULTS
# ============================

class QuestionResult(BaseModel):
    """Result for a single question."""
    
    question_id: PyObjectId
    question_number: int
    question_text: str
    
    # User's answer
    user_answer: str
    correct_answer: str
    is_correct: bool
    
    # Scoring
    marks_awarded: float
    max_marks: float
    
    # Analytics
    time_spent: Optional[float] = None  # Seconds
    attempts: int = 1  # If question allows multiple attempts
    
    # Concept tracking
    concepts_tested: List[str] = []


class QuizResult(MongoBaseModel):
    """Complete quiz attempt results."""
    
    # References
    user_id: PyObjectId
    quiz_id: PyObjectId
    subject_id: PyObjectId
    session_id: Optional[PyObjectId] = None
    
    # Score
    score: float
    max_score: float
    percentage: float
    passed: bool
    
    # Question-level results
    question_results: List[QuestionResult]
    
    # Analytics
    correct_count: int
    incorrect_count: int
    skipped_count: int = 0
    
    # Time tracking
    started_at: datetime
    completed_at: datetime
    time_taken: float  # Minutes
    
    # Concept analysis (populated by FeedbackService)
    concept_scores: Dict[str, float] = {}  # concept → accuracy %
    strengths: List[str] = []  # Concepts with >80% accuracy
    weak_areas: List[str] = []  # Concepts with <60% accuracy
    
    # Status
    feedback_generated: bool = False  # Set to True after FeedbackService processes
    
    created_at: datetime = datetime.utcnow()


# ============================
# USER QUIZ SUBMISSION
# ============================

class QuizSubmission(BaseModel):
    """Schema for user submitting quiz answers."""
    
    quiz_id: str  # ObjectId as string
    answers: Dict[str, str]  # question_number → user_answer
    time_taken: Optional[float] = None  # Minutes
    
    
class QuizAttemptCreate(BaseModel):
    """Schema for starting a quiz attempt."""
    
    quiz_id: str
    session_id: Optional[str] = None