# backend/app/core/models/user.py

"""
User collection models.
Enhanced with learning profile and performance tracking.
"""

from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, EmailStr
from .base import MongoBaseModel, PyObjectId


# ============================
# USER CREATION
# ============================

class UserCreate(BaseModel):
    """Schema for user registration."""
    name: str
    email: EmailStr
    password: str


# ============================
# LEARNING PROFILE
# ============================

class ConceptMastery(BaseModel):
    """Tracks mastery level for specific concepts."""
    concept: str
    mastery_level: float  # 0.0 - 1.0 (0% - 100%)
    last_practiced: datetime
    times_practiced: int = 0
    times_correct: int = 0
    times_incorrect: int = 0


class SubjectProfile(BaseModel):
    """Per-subject learning profile."""
    subject_id: PyObjectId
    subject_name: str
    
    # Performance metrics
    total_quizzes_taken: int = 0
    average_score: float = 0.0
    highest_score: float = 0.0
    
    # Concept tracking
    strengths: List[str] = []  # Concepts with >80% accuracy
    weak_areas: List[str] = []  # Concepts with <60% accuracy
    concept_mastery: Dict[str, float] = {}  # concept → mastery_level
    
    # Learning patterns
    preferred_study_time: Optional[str] = None  # "morning" | "afternoon" | "evening"
    average_session_duration: Optional[float] = None  # minutes
    
    last_updated: datetime = datetime.utcnow()


class LearningProfile(BaseModel):
    """Comprehensive learning profile across all subjects."""
    
    # Subject-specific profiles
    subjects: Dict[str, SubjectProfile] = {}  # subject_id → profile
    
    # Overall statistics
    total_study_hours: float = 0.0
    total_quizzes_completed: int = 0
    total_objectives_completed: int = 0
    
    # Learning preferences
    learning_style: Optional[str] = None  # "visual" | "reading" | "kinesthetic"
    difficulty_preference: Optional[str] = None  # "easy" | "medium" | "hard"
    
    # Engagement metrics
    streak_days: int = 0
    last_active: Optional[datetime] = None
    
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()


# ============================
# USER IN DATABASE
# ============================

class UserInDB(MongoBaseModel):
    """Complete user document stored in MongoDB."""
    
    # Authentication
    name: str
    email: EmailStr
    password_hash: str
    
    # Authorization
    role: str = "student"  # "student" | "teacher" | "admin"
    is_active: bool = True
    
    # Learning profile (enhanced)
    learning_profile: LearningProfile = LearningProfile()
    
    # Preferences
    preferences: Dict = {}  # UI preferences, notifications, etc.
    
    # Metadata
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None
    updated_at: datetime = datetime.utcnow()


# ============================
# USER RESPONSES
# ============================

class UserPublic(BaseModel):
    """Public user information (no sensitive data)."""
    id: str  # ObjectId as string
    name: str
    email: EmailStr
    role: str
    learning_profile: LearningProfile
    created_at: datetime


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    name: Optional[str] = None
    preferences: Optional[Dict] = None
    learning_profile: Optional[LearningProfile] = None