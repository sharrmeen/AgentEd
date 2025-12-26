# backend/app/api/v1/feedback.py

"""
Feedback endpoints - Learning insights and performance analysis.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from typing import Optional

from app.services.feedback_service import FeedbackService
from app.schemas.feedback import (
    FeedbackResponse,
    FeedbackListResponse
)
from app.api.deps import get_user_id

router = APIRouter()


@router.get("/{result_id}", response_model=FeedbackResponse)
async def get_feedback(
    result_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Get comprehensive feedback for a quiz result.
    
    Includes:
    - Performance analysis
    - Strengths and weaknesses
    - Revision recommendations
    - Next steps
    
    Args:
        result_id: Quiz result ID
        
    Returns:
        Detailed feedback report
    """
    try:
        result_obj_id = ObjectId(result_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid result ID format"
        )
    
    try:
        feedback = await FeedbackService.get_feedback_by_result(
            user_id=user_id,
            result_id=result_obj_id
        )
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        return FeedbackResponse(
            id=str(feedback.id),
            quiz_result_id=str(feedback.quiz_result_id),
            quiz_id=str(feedback.quiz_id),
            subject_id=str(feedback.subject_id),
            session_id=str(feedback.session_id) if feedback.session_id else None,
            assessment_type=feedback.assessment_type,
            score=feedback.score,
            max_score=feedback.max_score,
            percentage=feedback.percentage,
            performance_level=feedback.performance_level,
            performance_summary=feedback.performance_summary if hasattr(feedback, 'performance_summary') else "",
            strengths=feedback.strengths,
            strength_details=feedback.strength_details if hasattr(feedback, 'strength_details') else [],
            weak_areas=feedback.weak_areas,
            weakness_details=feedback.weakness_details if hasattr(feedback, 'weakness_details') else [],
            revision_tips=feedback.revision_tips if hasattr(feedback, 'revision_tips') else [],
            revision_items=feedback.revision_items if hasattr(feedback, 'revision_items') else [],
            estimated_revision_time=feedback.estimated_revision_time if hasattr(feedback, 'estimated_revision_time') else 0.0,
            recommended_resources=feedback.recommended_resources if hasattr(feedback, 'recommended_resources') else [],
            recommended_chapters=feedback.recommended_chapters if hasattr(feedback, 'recommended_chapters') else [],
            insights=feedback.insights if hasattr(feedback, 'insights') else [],
            motivational_message=feedback.motivational_message if hasattr(feedback, 'motivational_message') else "",
            encouragement=feedback.encouragement if hasattr(feedback, 'encouragement') else "",
            next_steps=feedback.next_steps if hasattr(feedback, 'next_steps') else [],
            created_at=feedback.created_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    subject_id: Optional[str] = None,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    List all feedback reports for the user.
    
    Query Parameters:
        subject_id: Filter by subject (optional)
        
    Returns:
        List of feedback reports
    """
    try:
        subject_obj_id = ObjectId(subject_id) if subject_id else None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        feedback_reports = await FeedbackService.list_feedback_reports(
            user_id=user_id,
            subject_id=subject_obj_id
        )
        
        feedback_items = [
            {
                "id": str(f.id),
                "quiz_result_id": str(f.quiz_result_id),
                "quiz_title": f.quiz_title if hasattr(f, 'quiz_title') else "Quiz",
                "score": f.score,
                "percentage": f.percentage,
                "performance_level": f.performance_level,
                "created_at": f.created_at
            }
            for f in feedback_reports
        ]
        
        return FeedbackListResponse(
            feedback_reports=feedback_items,
            total=len(feedback_items)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
