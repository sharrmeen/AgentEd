# backend/app/schemas/subject.py

"""
Subject schemas for CRUD operations.
"""

from datetime import datetime
from typing import Optional, List
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
    class_ids: List[str] = Field(
        default=[],
        description="Class assignments for teacher-created subjects"
    )


class SubjectUpdate(BaseModel):
    """Update subject request."""
    subject_name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = None


class SubjectResponse(BaseModel):
    """Subject response."""
    id: str
    class_ids: List[str] = []
    subject_name: str
    syllabus_id: Optional[str] = None
    status: str = "created"
    
    
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
