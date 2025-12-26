"""Chat memory collection models.
Individual Q&A turns with cache metadata.
"""

from typing import List
from datetime import datetime
from .base import MongoBaseModel, PyObjectId


class ChatMemory(MongoBaseModel):
    user_id: PyObjectId
    subject_id: PyObjectId            # FK → subjects._id
    session_id: PyObjectId
    chat_id: PyObjectId

    question: str
    question_hash: str
    intent_tag: str  #Explain|Answer|Reexplain

    answer: str
    embedding: List[float]

    confidence_score: float
    source: str                       # CACHE | LLM

    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    