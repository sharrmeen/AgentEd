# backend/app/schemas/syllabus.py

"""
Syllabus schemas for upload and retrieval.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ============================
# RESPONSE SCHEMAS
# ============================

class SyllabusUploadResponse(BaseModel):
    """Syllabus upload response."""
    syllabus_id: str
    subject_id: str
    text_preview: str  # First 500 chars
    file_type: str
    source_file: str
    created_at: datetime


class SyllabusResponse(BaseModel):
    """Full syllabus response."""
    id: str
    subject_id: str
    raw_text: str
    source_file: str
    file_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SyllabusDeleteResponse(BaseModel):
    """Syllabus deletion response."""
    message: str = "Syllabus deleted successfully"
    syllabus_id: str
