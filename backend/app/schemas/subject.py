# backend/app/schemas/subject.py

"""
Subject schemas for CRUD operations.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


# ============================
# REQUEST SCHEMAS
# ============================

class SubjectCreate(BaseModel):
    """Create subject request."""
    subject_name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Subject name (e.g., 'Biology', 'Physics')"
    )


class SubjectUpdate(BaseModel):
    """Update subject request."""
    subject_name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = None


# ============================
# RESPONSE SCHEMAS
# ============================

class ChapterInfo(BaseModel):
    """Chapter information from study plan."""
    chapter_number: int
    title: str
    objectives: List[str] = []
    estimated_hours: float = 0.0


class PlanSummary(BaseModel):
    """Summary of study plan."""
    total_chapters: int = 0
    total_hours: float = 0.0
    target_days: int = 0
    chapters: List[ChapterInfo] = []


class SubjectResponse(BaseModel):
    """Subject response."""
    id: str
    subject_name: str
    syllabus_id: Optional[str] = None
    status: str = "created"
    plan: Optional[Dict[str, Any]] = None
    plan_summary: Optional[PlanSummary] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubjectListResponse(BaseModel):
    """List of subjects response."""
    subjects: List[SubjectResponse]
    total: int


class SubjectDeleteResponse(BaseModel):
    """Subject deletion response."""
    message: str = "Subject deleted successfully"
    subject_id: str
