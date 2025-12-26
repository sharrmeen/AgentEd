# models/planner.py

from datetime import datetime
from typing import List, Dict
from .base import MongoBaseModel, PyObjectId


class ChapterProgress(BaseModel):
    """Tracks progress within a single chapter."""
    chapter_number: int
    completed_objectives: List[str] = []  # Objective texts marked done
    total_objectives: int = 0
    is_complete: bool = False
    started_at: datetime | None = None
    completed_at: datetime | None = None
    deadline: datetime | None = None  # When this chapter should be done


class PlannerState(MongoBaseModel):
    """Represents a user's study plan and progress tracking."""
    user_id: PyObjectId
    subject_id: PyObjectId  # FK → subjects._id
    
    # Plan metadata (from agent output)
    total_chapters: int
    target_days: int
    daily_hours: float
    estimated_total_hours: float
    
    # Progress tracking
    current_chapter: int = 1
    completed_chapters: List[int] = []
    completion_percent: float = 0.0
    
    # Chapter-level progress (NEW)
    chapter_progress: Dict[str, Dict] = {}  # key: "1", "2", etc.
    # Structure: {"1": {"completed_objectives": [...], "deadline": datetime, ...}}
    
    # Auto-replanning (NEW)
    last_replanned_at: datetime | None = None
    replan_count: int = 0
    missed_deadlines: List[int] = []  # Chapter numbers that missed deadline
    
    # AI recommendations
    next_suggestion: str = ""
    study_pace: str = "on_track"  # on_track | behind | ahead (RESTORED for deadline tracking)
    
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()