from datetime import datetime
from typing import Optional
from .base import MongoBaseModel, PyObjectId


class Notes(MongoBaseModel):
    user_id: PyObjectId
    subject_id: PyObjectId
    class_id: Optional[str] = None
    teacher_id: Optional[PyObjectId] = None
    role: str = "student"

    subject: str           
    chapter: str         
    
    source_file: str
    file_path: str
    storage_type: str = "s3"
    object_key: Optional[str] = None
    object_url: Optional[str] = None
    file_type: str  # pdf | docx | image
    
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
