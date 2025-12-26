from datetime import datetime
from .base import MongoBaseModel, PyObjectId


class Chat(MongoBaseModel):
    user_id: PyObjectId
    session_id: PyObjectId
    subject_id: PyObjectId
    chapter_number: int
    chapter_title: str
    
    created_at: datetime = datetime.utcnow()
