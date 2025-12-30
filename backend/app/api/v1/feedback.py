# backend/app/api/v1/feedback.py

"""
Feedback endpoints - Learning insights and performance analysis.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from typing import Optional
from datetime import datetime

from app.services.feedback_service import FeedbackService
from app.services.quiz_service import QuizService
from app.schemas.feedback import (
    FeedbackResponse,
    FeedbackListResponse,
    ConceptAnalysisResponse,
    RevisionItemResponse,
    LearningInsightResponse
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
        
        # Convert nested objects to response schemas
        strength_details = []
        if hasattr(feedback, 'strength_details') and feedback.strength_details:
            for detail in feedback.strength_details:
                strength_details.append(ConceptAnalysisResponse(
                    concept=detail.concept if hasattr(detail, 'concept') else "",
                    questions_on_concept=detail.questions_on_concept if hasattr(detail, 'questions_on_concept') else 0,
                    correct_answers=detail.correct_answers if hasattr(detail, 'correct_answers') else 0,
                    accuracy_percentage=detail.accuracy_percentage if hasattr(detail, 'accuracy_percentage') else 0.0,
                    mastery_level=detail.mastery_level if hasattr(detail, 'mastery_level') else "needs_attention",
                    needs_revision=detail.needs_revision if hasattr(detail, 'needs_revision') else True,
                    suggestion=detail.suggestion if hasattr(detail, 'suggestion') else ""
                ))
        
        weakness_details = []
        if hasattr(feedback, 'weakness_details') and feedback.weakness_details:
            for detail in feedback.weakness_details:
                weakness_details.append(ConceptAnalysisResponse(
                    concept=detail.concept if hasattr(detail, 'concept') else "",
                    questions_on_concept=detail.questions_on_concept if hasattr(detail, 'questions_on_concept') else 0,
                    correct_answers=detail.correct_answers if hasattr(detail, 'correct_answers') else 0,
                    accuracy_percentage=detail.accuracy_percentage if hasattr(detail, 'accuracy_percentage') else 0.0,
                    mastery_level=detail.mastery_level if hasattr(detail, 'mastery_level') else "needs_attention",
                    needs_revision=detail.needs_revision if hasattr(detail, 'needs_revision') else True,
                    suggestion=detail.suggestion if hasattr(detail, 'suggestion') else ""
                ))
        
        revision_items = []
        if hasattr(feedback, 'revision_items') and feedback.revision_items:
            for item in feedback.revision_items:
                revision_items.append(RevisionItemResponse(
                    concept=item.concept if hasattr(item, 'concept') else "",
                    reason=item.reason if hasattr(item, 'reason') else "",
                    priority=item.priority if hasattr(item, 'priority') else "medium",
                    source_file=item.source_file if hasattr(item, 'source_file') else None,
                    chapter_number=item.chapter_number if hasattr(item, 'chapter_number') else None,
                    section=item.section if hasattr(item, 'section') else None,
                    estimated_time=item.estimated_time if hasattr(item, 'estimated_time') else None,
                    recommended_approach=item.recommended_approach if hasattr(item, 'recommended_approach') else None
                ))
        
        insights = []
        if hasattr(feedback, 'insights') and feedback.insights:
            for insight in feedback.insights:
                insights.append(LearningInsightResponse(
                    insight_type=insight.insight_type if hasattr(insight, 'insight_type') else "recommendation",
                    title=insight.title if hasattr(insight, 'title') else "",
                    description=insight.description if hasattr(insight, 'description') else "",
                    action_items=insight.action_items if hasattr(insight, 'action_items') else []
                ))
        
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
            strength_details=strength_details,
            weak_areas=feedback.weak_areas if hasattr(feedback, 'weak_areas') else [],
            weakness_details=weakness_details,
            revision_tips=feedback.revision_tips if hasattr(feedback, 'revision_tips') else [],
            revision_items=revision_items,
            estimated_revision_time=feedback.estimated_revision_time if hasattr(feedback, 'estimated_revision_time') else 0.0,
            recommended_resources=feedback.recommended_resources if hasattr(feedback, 'recommended_resources') else [],
            recommended_chapters=feedback.recommended_chapters if hasattr(feedback, 'recommended_chapters') else [],
            insights=insights,
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
        
        feedback_items = []
        for f in feedback_reports:
            # Fetch quiz to get title
            quiz_title = "Quiz"
            try:
                quiz = await QuizService.get_quiz_by_id(
                    user_id=user_id,
                    quiz_id=f.quiz_id
                )
                if quiz:
                    quiz_title = quiz.title if hasattr(quiz, 'title') else "Quiz"
            except:
                pass  # Use default if quiz not found
            
            feedback_items.append({
                "id": str(f.id) if hasattr(f, 'id') else str(f.get("_id", "")),
                "quiz_result_id": str(f.quiz_result_id) if hasattr(f, 'quiz_result_id') else "",
                "quiz_title": quiz_title,
                "score": f.score if hasattr(f, 'score') else 0.0,
                "percentage": f.percentage if hasattr(f, 'percentage') else 0.0,
                "performance_level": f.performance_level if hasattr(f, 'performance_level') else "needs_improvement",
                "created_at": f.created_at if hasattr(f, 'created_at') else datetime.utcnow()
            })
        
        return FeedbackListResponse(
            feedback_reports=feedback_items,
            total=len(feedback_items)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
