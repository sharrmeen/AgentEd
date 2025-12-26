# backend/app/schemas/auth.py

"""
Authentication schemas for user registration, login, and profile.
"""

from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, EmailStr, Field


# ============================
# REQUEST SCHEMAS
# ============================

class UserRegisterRequest(BaseModel):
    """User registration request."""
    name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")


class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class PasswordChangeRequest(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(..., min_length=6)


class ProfileUpdateRequest(BaseModel):
    """Profile update request."""
    name: Optional[str] = None
    learning_style: Optional[str] = None
    difficulty_preference: Optional[str] = None


# ============================
# RESPONSE SCHEMAS
# ============================

class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    email: str
    name: str


class SubjectProfileResponse(BaseModel):
    """Per-subject learning profile."""
    subject_id: str
    subject_name: str
    total_quizzes_taken: int = 0
    average_score: float = 0.0
    highest_score: float = 0.0
    strengths: List[str] = []
    weak_areas: List[str] = []


class LearningProfileResponse(BaseModel):
    """User's learning profile."""
    subjects: Dict[str, SubjectProfileResponse] = {}
    total_study_hours: float = 0.0
    total_quizzes_completed: int = 0
    total_objectives_completed: int = 0
    learning_style: Optional[str] = None
    difficulty_preference: Optional[str] = None
    streak_days: int = 0
    last_active: Optional[datetime] = None


class UserResponse(BaseModel):
    """User profile response."""
    id: str
    name: str
    email: str
    role: str = "student"
    is_active: bool = True
    learning_profile: Optional[LearningProfileResponse] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
