# backend/app/schemas/agent.py

"""
Agent schemas for intelligent workflow endpoints.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ============================
# REQUEST SCHEMAS
# ============================

class AgentQueryRequest(BaseModel):
    """Main agent query request."""
    query: str = Field(
        ..., 
        min_length=1, 
        max_length=2000,
        description="Natural language query for the agent"
    )
    subject_id: Optional[str] = Field(None, description="Subject context")
    chapter_number: Optional[int] = Field(None, ge=1, description="Chapter context")
    session_id: Optional[str] = Field(None, description="Session for caching")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for the agent"
    )
    constraints: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Planning constraints (target_days, daily_hours, etc.)"
    )


class AgentChatRequest(BaseModel):
    """Agent conversational chat request."""
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_number: Optional[int] = None
    include_history: bool = Field(
        default=True,
        description="Include chat history for context"
    )


class AgentFeedbackRequest(BaseModel):
    """Request feedback analysis from agent."""
    quiz_result_id: str
    include_revision_plan: bool = True


# ============================
# RESPONSE SCHEMAS
# ============================

class AgentMessage(BaseModel):
    """Agent response message."""
    role: str  # "assistant" | "system"
    content: str
    timestamp: datetime = datetime.utcnow()


class AgentQueryResponse(BaseModel):
    """Agent query response."""
    messages: List[str]
    data: Dict[str, Any] = {}
    workflow_id: str
    agents_involved: List[str] = []
    status: str = "completed"
    
    # Optional data fields
    study_plan: Optional[Dict[str, Any]] = None
    quiz: Optional[Dict[str, Any]] = None
    feedback: Optional[Dict[str, Any]] = None
    content: Optional[str] = None


class AgentChatResponse(BaseModel):
    """Agent chat response."""
    response: str
    session_id: Optional[str] = None
    chat_id: Optional[str] = None
    source: str = "agent"  # "agent" | "cache"
    context: Dict[str, Any] = {}
    suggestions: List[str] = []


class AgentStatusResponse(BaseModel):
    """Agent workflow status."""
    workflow_id: str
    status: str  # "running" | "completed" | "failed"
    current_agent: Optional[str] = None
    progress: float = 0.0
    messages: List[AgentMessage] = []
