# backend/app/api/v1/feedback.py

"""
Feedback endpoints - Learning insights and performance analysis.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from typing import Optional
from datetime import datetime

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
            id=str(feedback.id) if hasattr(feedback, 'id') else str(feedback.get("_id")),
            quiz_result_id=str(feedback.quiz_result_id) if hasattr(feedback, 'quiz_result_id') else "",
            quiz_id=str(feedback.quiz_id) if hasattr(feedback, 'quiz_id') else "",
            subject_id=str(feedback.subject_id) if hasattr(feedback, 'subject_id') else "",
            session_id=str(feedback.session_id) if hasattr(feedback, 'session_id') and feedback.session_id else None,
            assessment_type=feedback.assessment_type if hasattr(feedback, 'assessment_type') else "quiz",
            score=feedback.score if hasattr(feedback, 'score') else 0.0,
            max_score=feedback.max_score if hasattr(feedback, 'max_score') else 100.0,
            percentage=feedback.percentage if hasattr(feedback, 'percentage') else 0.0,
            performance_level=feedback.performance_level if hasattr(feedback, 'performance_level') else "needs_improvement",
            performance_summary=feedback.performance_summary if hasattr(feedback, 'performance_summary') else "",
            strengths=feedback.strengths if hasattr(feedback, 'strengths') else [],
            strength_details=feedback.strength_details if hasattr(feedback, 'strength_details') else [],
            weak_areas=feedback.weak_areas if hasattr(feedback, 'weak_areas') else [],
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
            created_at=feedback.created_at if hasattr(feedback, 'created_at') else datetime.utcnow()
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
                "id": str(f.id) if hasattr(f, 'id') else str(f.get("_id", "")),
                "quiz_result_id": str(f.quiz_result_id) if hasattr(f, 'quiz_result_id') else "",
                "quiz_title": f.quiz_title if hasattr(f, 'quiz_title') else "Quiz",
                "score": f.score if hasattr(f, 'score') else 0.0,
                "percentage": f.percentage if hasattr(f, 'percentage') else 0.0,
                "performance_level": f.performance_level if hasattr(f, 'performance_level') else "needs_improvement",
                "created_at": f.created_at if hasattr(f, 'created_at') else datetime.utcnow()
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
