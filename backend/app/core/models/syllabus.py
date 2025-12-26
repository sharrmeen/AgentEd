from datetime import datetime
from .base import MongoBaseModel, PyObjectId


class Syllabus(MongoBaseModel):
    user_id: PyObjectId
    subject_id: PyObjectId         # FK → subject._id
    
    raw_text: str
    source_file: str
    file_type: str  # pdf | docx | image
    
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()