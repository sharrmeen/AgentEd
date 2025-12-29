# backend/app/api/v2/agent.py

"""
Agent workflow endpoints - Intelligent multi-agent orchestration.

Routes queries to appropriate agents:
- Study Plan Agent (planning & progress)
- Resource Agent (content retrieval)
- Quiz Agent (assessment generation)
- Feedback Agent (performance analysis)
"""

from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from typing import Optional
import uuid

from app.agents.orchestration.workflow import run_workflow
from app.schemas.agent import (
    AgentQueryRequest,
    AgentQueryResponse,
    AgentFeedbackRequest
)
from app.api.deps import get_user_id

router = APIRouter()


@router.post("/query", response_model=AgentQueryResponse)
async def agent_query(
    request: AgentQueryRequest,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Submit a query to the intelligent agent system.
    
    The agent router automatically routes to appropriate agents based on intent:
    - "plan", "schedule" → Study Plan Agent
    - "question", "explain" → Resource Agent (RAG)
    - "quiz", "test" → Quiz Agent
    - "feedback", "performance" → Feedback Agent
    
    Args:
        request: Query with optional subject/chapter context
        
    Returns:
        Agent response with data and workflow info
    """
    try:
        # Generate workflow ID for tracking
        workflow_id = str(uuid.uuid4())
        
        # Run workflow
        result = await run_workflow(
            user_id=str(user_id),
            user_query=request.query,
            subject_id=request.subject_id,
            chapter_number=request.chapter_number,
            session_id=request.session_id,
            constraints=request.constraints,
            workflow_id=workflow_id
        )
        
        # Extract messages and data
        messages = result.get("messages", [])
        if isinstance(messages, str):
            messages = [messages]
        
        # Build response
        response_data = {}
        
        # Extract specific data if available
        if "study_plan" in result:
            response_data["study_plan"] = result["study_plan"]
        if "quiz" in result:
            response_data["quiz"] = result["quiz"]
        if "feedback" in result:
            response_data["feedback"] = result["feedback"]
        if "content" in result:
            response_data["content"] = result["content"]
        
        # Get agents involved
        agents_involved = result.get("agents_involved", [])
        
        return AgentQueryResponse(
            messages=messages,
            data=response_data,
            workflow_id=workflow_id,
            agents_involved=agents_involved,
            status="completed"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow failed: {str(e)}"
        )


@router.post("/plan")
async def generate_study_plan(
    subject_id: str,
    target_days: int,
    daily_hours: float = 2.0,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Generate study plan via Study Plan Agent.
    
    Shortcut endpoint for common task.
    
    Args:
        subject_id: Subject to plan
        target_days: Days to complete
        daily_hours: Hours per day
        
    Returns:
        Study plan
    """
    request = AgentQueryRequest(
        query=f"Generate a clear and realistic {target_days}-day study plan with {daily_hours} hours per day for this subject.\n",
        subject_id=subject_id,
        constraints={
            "target_days": target_days,
            "daily_hours": daily_hours
        }
    )
    
    return await agent_query(request, user_id)


@router.post("/quiz")
async def generate_quiz(
    subject_id: str,
    chapter_number: Optional[int] = None,
    num_questions: int = 10,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Generate quiz via Quiz Agent.
    
    Shortcut endpoint for common task.
    
    Args:
        subject_id: Subject
        chapter_number: Chapter to quiz on
        num_questions: Number of questions
        
    Returns:
        Generated quiz
    """
    chapter_ref = f" on Chapter {chapter_number}" if chapter_number else ""
    request = AgentQueryRequest(
        query=f"Generate a {num_questions}-question quiz for this subject suitable for school and college students.Include a mix of easy, medium, and challenging questions.{chapter_ref}",
        subject_id=subject_id,
        chapter_number=chapter_number,
        constraints={
            "num_questions": num_questions
        }
    )
    
    return await agent_query(request, user_id)
