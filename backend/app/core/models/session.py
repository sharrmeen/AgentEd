

from datetime import datetime
from .base import MongoBaseModel, PyObjectId


class StudySession(MongoBaseModel):
    user_id: PyObjectId
    subject_id: PyObjectId            # FK → subjects._id

    chapter_number: int
    chapter_title: str

    chat_id: PyObjectId | None = None
    notes_uploaded: bool = False

    status: str = "active"
    last_active: datetime | None = None

    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    ended_at: datetime | None = None