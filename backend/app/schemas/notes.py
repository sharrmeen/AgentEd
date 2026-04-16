# backend/app/schemas/notes.py

"""
Notes schemas for upload and retrieval.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================
# REQUEST SCHEMAS
# ============================

class NotesUploadRequest(BaseModel):
    """Notes upload metadata (file sent separately)."""
    chapter: str = Field(..., description="Chapter name or number")


# ============================
# RESPONSE SCHEMAS
# ============================

class NotesResponse(BaseModel):
    """Notes response."""
    id: str
    subject_id: str
    class_id: Optional[str] = None
    teacher_id: Optional[str] = None
    role: str = "student"
    subject: str
    chapter: str
    source_file: str
    file_path: str
    storage_type: str = "local"
    object_key: Optional[str] = None
    object_url: Optional[str] = None
    file_type: str
    ingestion_status: str = "completed"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotesUploadResponse(BaseModel):
    """Notes upload response."""
    note_id: str
    file_path: str
    ingestion_status: str
    message: str = "Notes uploaded and ingested successfully"


class NotesListResponse(BaseModel):
    """List of notes response."""
    notes: List[NotesResponse]
    total: int


class NotesDeleteResponse(BaseModel):
    """Notes deletion response."""
    message: str = "Notes deleted successfully"
    note_id: str


class NotesDownloadUrlResponse(BaseModel):
    """Temporary or authenticated download entrypoint for a note file."""
    download_url: str
    requires_auth: bool
    expires_in: Optional[int] = None
