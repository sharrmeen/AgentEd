# backend/app/schemas/feedback.py

"""
Feedback schemas for learning insights and performance analysis.
"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel


# ============================
# RESPONSE SCHEMAS
# ============================

class ConceptAnalysisResponse(BaseModel):
    """Concept analysis detail."""
    concept: str
    questions_on_concept: int
    correct_answers: int
    accuracy_percentage: float
    mastery_level: str  # "strong" | "developing" | "needs_attention"
    needs_revision: bool
    suggestion: str


class RevisionItemResponse(BaseModel):
    """Revision recommendation."""
    concept: str
    reason: str
    priority: str  # "high" | "medium" | "low"
    source_file: Optional[str] = None
    chapter_number: Optional[int] = None
    section: Optional[str] = None
    estimated_time: Optional[float] = None  # minutes
    recommended_approach: Optional[str] = None


class LearningInsightResponse(BaseModel):
    """Learning insight."""
    insight_type: str  # "strength" | "weakness" | "pattern" | "recommendation"
    title: str
    description: str
    action_items: List[str] = []


class FeedbackResponse(BaseModel):
    """Comprehensive feedback response."""
    id: str
    quiz_result_id: str
    quiz_id: str
    subject_id: str
    session_id: Optional[str] = None
    
    # Assessment
    assessment_type: str
    
    # Score summary
    score: float
    max_score: float
    percentage: float
    performance_level: str  # "excellent" | "good" | "satisfactory" | "needs_improvement"
    
    # Analysis
    performance_summary: str
    strengths: List[str] = []
    strength_details: List[ConceptAnalysisResponse] = []
    weak_areas: List[str] = []
    weakness_details: List[ConceptAnalysisResponse] = []
    
    # Revision plan
    revision_tips: List[str] = []
    revision_items: List[RevisionItemResponse] = []
    estimated_revision_time: float = 0.0  # hours
    
    # Recommendations
    recommended_resources: List[str] = []
    recommended_chapters: List[int] = []
    
    # Insights
    insights: List[LearningInsightResponse] = []
    
    # Motivation
    motivational_message: str = ""
    encouragement: str = ""
    
    # Next steps
    next_steps: List[str] = []
    
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackListItem(BaseModel):
    """Feedback list item."""
    id: str
    quiz_result_id: str
    quiz_title: str
    score: float
    percentage: float
    performance_level: str
    created_at: datetime


class FeedbackListResponse(BaseModel):
    """List of feedback reports."""
    feedback_reports: List[FeedbackListItem]
    total: int
