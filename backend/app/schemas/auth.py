# backend/app/schemas/auth.py

"""
Authentication schemas for user registration, login, and profile.
"""

from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


# ============================
# REQUEST SCHEMAS
# ============================

class AdminCreateUserRequest(BaseModel):
    """Admin request to create a new user account."""
    name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    username: str = Field(..., min_length=2, max_length=100, description="Username (GR number or employee ID)")
    email: Optional[str] = Field(None, description="Optional email address")
    role: str = Field(..., description="Role: student or teacher")
    class_id: Optional[str] = Field(None, description="Class ID for students")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    must_change_password: bool = Field(True, description="Force password change on first login")


class UserLoginRequest(BaseModel):
    """User login request."""
    username: str = Field(..., description="Username (GR number or employee ID)")
    password: str = Field(..., description="User's password")


class PasswordChangeRequest(BaseModel):
    """Password change request."""
    email: Optional[str] = Field(None, description="Required on first login")
    current_password: str
    new_password: str = Field(..., min_length=6)


class ProfileUpdateRequest(BaseModel):
    """Profile update request."""
    name: Optional[str] = None
    email: Optional[str] = None
    learning_style: Optional[str] = None
    difficulty_preference: Optional[str] = None


class ClassAssignmentRequest(BaseModel):
    """Assign or clear a student's class."""
    class_id: Optional[str] = None


# ============================
# RESPONSE SCHEMAS
# ============================

class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    username: str
    name: str
    role: str
    class_id: Optional[str] = None
    must_change_password: bool = False


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
    username: str
    email: Optional[str] = None
    role: str = "student"
    class_id: Optional[str] = None
    must_change_password: bool = False
    is_active: bool = True
    learning_profile: Optional[LearningProfileResponse] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
