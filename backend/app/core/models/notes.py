from datetime import datetime
from typing import Optional
from .base import MongoBaseModel, PyObjectId


class Notes(MongoBaseModel):
    user_id: PyObjectId
    subject_id: PyObjectId

    subject: str           
    chapter: str         
    
    source_file: str
    file_path: str
    file_type: str  # pdf | docx | image
    
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
