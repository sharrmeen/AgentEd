# backend/app/schemas/chat.py

"""
Chat schemas for Q&A and conversation history.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================
# REQUEST SCHEMAS
# ============================

class ChatMessageRequest(BaseModel):
    """Send chat message request."""
    question: str = Field(..., min_length=1, max_length=2000, description="User's question")
    intent_tag: Optional[str] = Field(
        default="Answer",
        pattern="^(Explain|Answer|Reexplain|Summarize|Example)$",
        description="Type of response expected"
    )


# ============================
# RESPONSE SCHEMAS
# ============================

class ChatMessageResponse(BaseModel):
    """Chat message response."""
    answer: str
    source: str  # "CACHE" | "LLM"
    cached: bool = False
    confidence_score: Optional[float] = None
    session_id: Optional[str] = None
    chat_id: Optional[str] = None


class ChatHistoryItem(BaseModel):
    """Single chat history item."""
    id: str
    question: str
    answer: str
    intent_tag: str
    source: str
    confidence_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Chat history response."""
    chat_id: str
    session_id: str
    subject_id: str
    chapter_number: int
    chapter_title: str
    messages: List[ChatHistoryItem]
    total: int


class ChatResponse(BaseModel):
    """Chat container response."""
    id: str
    session_id: str
    subject_id: str
    chapter_number: int
    chapter_title: str
    created_at: datetime

    class Config:
        from_attributes = True
