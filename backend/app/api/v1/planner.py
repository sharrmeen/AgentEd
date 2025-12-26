# backend/app/api/v1/planner.py

"""
Study planner endpoints - Generate and manage study plans.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from typing import Optional

from app.services.planner_service import PlannerService
from app.services.subject_service import SubjectService
from app.schemas.planner import (
    PlanGenerateRequest,
    PlanResponse,
    PlannerStateResponse,
    ObjectiveCompleteRequest,
    ObjectiveCompleteResponse,
    ChapterProgressResponse
)
from app.api.deps import get_user_id

router = APIRouter()


@router.post("/{subject_id}/generate", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def generate_plan(
    subject_id: str,
    request: PlanGenerateRequest,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Generate a study plan for a subject.
    
    Prerequisites:
    - Subject must exist
    - Syllabus must be uploaded
    
    Args:
        subject_id: Subject to plan
        request: Plan generation parameters (target_days, daily_hours)
        
    Returns:
        Generated study plan with chapter deadlines
    """
    try:
        subject_obj_id = ObjectId(subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        planner_state = await PlannerService.generate_plan(
            user_id=user_id,
            subject_id=subject_obj_id,
            target_days=request.target_days,
            daily_hours=request.daily_hours,
            preferences=request.preferences
        )
        
        # Fetch full subject to get plan
        subject = await SubjectService.get_subject_by_id(
            user_id=user_id,
            subject_id=subject_obj_id
        )
        
        return PlanResponse(
            planner_state=PlannerStateResponse(**planner_state.dict()),
            study_plan=subject.plan if subject else {}
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{subject_id}", response_model=PlannerStateResponse)
async def get_plan(
    subject_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Get current study plan for a subject.
    
    Args:
        subject_id: Subject ID
        
    Returns:
        Current planner state with progress
    """
    try:
        subject_obj_id = ObjectId(subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        planner_state = await PlannerService.get_planner_state(
            user_id=user_id,
            subject_id=subject_obj_id
        )
        
        if not planner_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study plan not found. Please generate a plan first."
            )
        
        return PlannerStateResponse(**planner_state.dict())
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/objective/complete", response_model=ObjectiveCompleteResponse)
async def mark_objective_complete(
    request: ObjectiveCompleteRequest,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Mark an objective as complete.
    
    Auto-completes chapter when all objectives are done.
    Auto-replans if deadline is missed.
    
    Args:
        request: Objective completion data
        
    Returns:
        Updated planner state with completion status
    """
    try:
        subject_obj_id = ObjectId(request.subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        result = await PlannerService.mark_objective_complete(
            user_id=user_id,
            subject_id=subject_obj_id,
            chapter_number=request.chapter_number,
            objective=request.objective
        )
        
        return ObjectiveCompleteResponse(
            chapter_completed=result.get("chapter_completed", False),
            replanned=result.get("replanned", False),
            message=result.get("message", "Objective marked complete"),
            planner_state=PlannerStateResponse(**result["planner_state"].dict())
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{subject_id}/chapter/{chapter_number}", response_model=ChapterProgressResponse)
async def get_chapter_progress(
    subject_id: str,
    chapter_number: int,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Get progress for a specific chapter.
    
    Args:
        subject_id: Subject ID
        chapter_number: Chapter number
        
    Returns:
        Chapter progress with objectives
    """
    try:
        subject_obj_id = ObjectId(subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        progress = await PlannerService.get_chapter_progress(
            user_id=user_id,
            subject_id=subject_obj_id,
            chapter_number=chapter_number
        )
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter progress not found"
            )
        
        return ChapterProgressResponse(**progress)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
