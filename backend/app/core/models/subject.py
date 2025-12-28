"""Subject collection models.
Represents a subject-level learning space.
Planner Agent operates at this level.
"""

from datetime import datetime
from typing import List, Dict, Optional
from .base import MongoBaseModel, PyObjectId


class Subject(MongoBaseModel):
    user_id: PyObjectId

    subject_name: str                 # "Biology"
    syllabus_id: Optional[PyObjectId] = None  # FK → syllabus._id

    plan: Optional[Dict] = None       # Planner output (chapters, order, etc.)

    status: str = "created"  # created | syllabus_uploaded | planned | in_progress | completed | archived


    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
