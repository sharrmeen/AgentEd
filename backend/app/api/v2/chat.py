# backend/app/api/v2/chat.py

"""
Agent conversational chat endpoints - Natural conversation with agents.

Uses agent orchestration for contextual responses with memory.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId

from app.agents.orchestration.workflow import run_workflow
from app.services.chat_memory_service import ChatMemoryService
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse
)
from app.api.deps import get_user_id

router = APIRouter()


@router.post("/", response_model=AgentChatResponse)
async def agent_chat(
    request: AgentChatRequest,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Send a conversational message to the agent system.
    
    Features:
    - Natural language Q&A
    - Session-based context memory
    - Multi-turn conversations
    - Automatic agent routing
    
    Args:
        request: Chat message with optional session context
        
    Returns:
        Agent response with context
    """
    try:
        # Run workflow for this query
        result = await run_workflow(
            user_id=str(user_id),
            user_query=request.query,
            subject_id=request.subject_id,
            chapter_number=request.chapter_number,
            session_id=request.session_id
        )
        
        # Extract response
        response_text = result.get("response", "")
        if isinstance(response_text, list):
            response_text = " ".join(result.get("messages", []))
        
        # Build context
        context = {
            "subject_id": request.subject_id,
            "chapter_number": request.chapter_number,
            "session_id": request.session_id
        }
        
        # Get suggestions if available
        suggestions = result.get("suggestions", [])
        
        return AgentChatResponse(
            response=response_text,
            session_id=request.session_id,
            chat_id=result.get("chat_id"),
            source="agent",
            context=context,
            suggestions=suggestions
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent chat failed: {str(e)}"
        )


@router.post("/explain")
async def explain_concept(
    concept: str,
    subject_id: str,
    chapter_number: int,
    session_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Ask agent to explain a concept.
    
    Shortcut endpoint with specific intent.
    
    Args:
        concept: Concept to explain
        subject_id: Subject context
        chapter_number: Chapter context
        session_id: Session for memory
        
    Returns:
        Explanation
    """
    request = AgentChatRequest(
        query=f"Explain {concept}",
        subject_id=subject_id,
        chapter_number=chapter_number,
        session_id=session_id,
        include_history=True
    )
    
    return await agent_chat(request, user_id)


@router.post("/summarize")
async def summarize_content(
    topic: str,
    subject_id: str,
    chapter_number: int,
    session_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Ask agent to summarize a topic.
    
    Shortcut endpoint with specific intent.
    
    Args:
        topic: Topic to summarize
        subject_id: Subject context
        chapter_number: Chapter context
        session_id: Session for memory
        
    Returns:
        Summary
    """
    request = AgentChatRequest(
        query=f"Summarize {topic}",
        subject_id=subject_id,
        chapter_number=chapter_number,
        session_id=session_id,
        include_history=True
    )
    
    return await agent_chat(request, user_id)


@router.post("/practice")
async def get_practice_tips(
    topic: str,
    subject_id: str,
    chapter_number: int,
    session_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Ask agent for practice tips on a topic.
    
    Shortcut endpoint with specific intent.
    
    Args:
        topic: Topic to practice
        subject_id: Subject context
        chapter_number: Chapter context
        session_id: Session for memory
        
    Returns:
        Practice suggestions
    """
    request = AgentChatRequest(
        query=f"Give me practice tips for {topic}",
        subject_id=subject_id,
        chapter_number=chapter_number,
        session_id=session_id,
        include_history=True
    )
    
    return await agent_chat(request, user_id)
