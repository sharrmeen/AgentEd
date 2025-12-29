# backend/app/schemas/planner.py

"""
Planner schemas for study plan generation and progress tracking.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


# ============================
# REQUEST SCHEMAS
# ============================

class PlanGenerateRequest(BaseModel):
    """Generate study plan request."""
    target_days: int = Field(
        ..., 
        ge=1, 
        le=365,
        description="Number of days to complete the syllabus"
    )
    daily_hours: float = Field(
        default=2.0, 
        ge=0.5, 
        le=12.0,
        description="Hours per day for studying"
    )
    preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional preferences for plan generation"
    )


class ObjectiveCompleteRequest(BaseModel):
    """Mark objective as complete request."""
    subject_id: str = Field(..., description="Subject ID")
    chapter_number: int = Field(..., ge=1, description="Chapter number")
    objective: str = Field(..., description="Objective text to mark complete")


class PlanRegenerateRequest(BaseModel):
    """Regenerate study plan request."""
    target_days: int = Field(..., ge=1, le=365)
    daily_hours: float = Field(default=2.0, ge=0.5, le=12.0)
    preserve_progress: bool = Field(
        default=True,
        description="Whether to preserve completed chapters"
    )


# ============================
# RESPONSE SCHEMAS
# ============================

class ChapterDeadline(BaseModel):
    """Chapter deadline information."""
    chapter_number: int
    title: str
    deadline: Optional[datetime] = None
    is_complete: bool = False
    completed_objectives: List[str] = []
    total_objectives: int = 0
    progress_percent: float = 0.0


class ChapterProgressResponse(BaseModel):
    """Chapter progress response."""
    completed_objectives: List[str] = []
    total_objectives: int = 0
    is_complete: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    estimated_hours: float = 0.0


class ObjectiveCompleteResponse(BaseModel):
    """Response after marking objective complete."""
    chapter_completed: bool
    replanned: bool
    message: str
    planner_state: "PlannerStateResponse"


class PlannerStateResponse(BaseModel):
    """Full planner state response."""
    id: str
    subject_id: str
    
    # Plan metadata
    total_chapters: int
    target_days: int
    daily_hours: float
    estimated_total_hours: float
    
    # Progress
    current_chapter: int
    completed_chapters: List[int]
    completion_percent: float
    
    # Chapter progress - flexible dict structure
    chapter_progress: Dict[str, Any] = {}
    
    # Auto-replanning
    last_replanned_at: Optional[datetime] = None
    replan_count: int = 0
    missed_deadlines: List[int] = []
    
    # Recommendations
    next_suggestion: str = ""
    study_pace: str = "on_track"
    
    @field_validator('id', 'subject_id', mode='before')
    @classmethod
    def convert_objectid_to_str(cls, v):
        """Convert ObjectId to string."""
        if isinstance(v, ObjectId):
            return str(v)
        return v
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlanResponse(BaseModel):
    """Study plan generation response."""
    planner_state: PlannerStateResponse
    study_plan: Dict[str, Any]
    message: str = "Study plan generated successfully"


# Forward reference resolution
ObjectiveCompleteResponse.model_rebuild()
