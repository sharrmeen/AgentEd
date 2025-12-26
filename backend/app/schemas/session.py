# backend/app/schemas/session.py

"""
Study session schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================
# REQUEST SCHEMAS
# ============================

class SessionCreateRequest(BaseModel):
    """Create study session request."""
    subject_id: str = Field(..., description="Subject ID")
    chapter_number: int = Field(..., ge=1, description="Chapter number to study")


class SessionUpdateRequest(BaseModel):
    """Update session request."""
    status: Optional[str] = Field(
        None, 
        pattern="^(active|paused|completed)$",
        description="Session status"
    )


# ============================
# RESPONSE SCHEMAS
# ============================

class SessionResponse(BaseModel):
    """Study session response."""
    id: str
    subject_id: str
    chapter_number: int
    chapter_title: str
    chat_id: Optional[str] = None
    notes_uploaded: bool = False
    status: str = "active"
    last_active: Optional[datetime] = None
    created_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """List of sessions response."""
    sessions: List[SessionResponse]
    total: int


class SessionEndResponse(BaseModel):
    """Session end response."""
    message: str = "Session ended successfully"
    session_id: str
    duration_minutes: float
