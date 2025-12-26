# backend/app/api/v1/sessions.py

"""
Study session endpoints - Create and manage study sessions.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId

from app.services.study_session_service import StudySessionService
from app.schemas.session import (
    SessionCreateRequest,
    SessionResponse,
    SessionListResponse,
    SessionEndResponse
)
from app.api.deps import get_user_id

router = APIRouter()


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Create a new study session for a chapter.
    
    Prerequisites:
    - Subject must exist
    - Syllabus must be uploaded
    - Study plan must be generated
    
    Args:
        request: Session creation data (subject_id, chapter_number)
        
    Returns:
        Created study session
    """
    try:
        subject_obj_id = ObjectId(request.subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        session = await StudySessionService.create_study_session(
            user_id=user_id,
            subject_id=subject_obj_id,
            chapter_number=request.chapter_number
        )
        
        return SessionResponse(
            id=str(session.id),
            subject_id=str(session.subject_id),
            chapter_number=session.chapter_number,
            chapter_title=session.chapter_title,
            chat_id=str(session.chat_id) if session.chat_id else None,
            notes_uploaded=session.notes_uploaded,
            status=session.status,
            last_active=session.last_active,
            created_at=session.created_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to subject"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Get a specific study session.
    
    Args:
        session_id: Session ID
        
    Returns:
        Session details
    """
    try:
        session_obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    
    session = await StudySessionService.get_session_by_id(
        user_id=user_id,
        session_id=session_obj_id
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return SessionResponse(
        id=str(session.id),
        subject_id=str(session.subject_id),
        chapter_number=session.chapter_number,
        chapter_title=session.chapter_title,
        chat_id=str(session.chat_id) if session.chat_id else None,
        notes_uploaded=session.notes_uploaded,
        status=session.status,
        last_active=session.last_active,
        created_at=session.created_at
    )


@router.get("/subject/{subject_id}", response_model=SessionListResponse)
async def list_subject_sessions(
    subject_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    List all study sessions for a subject.
    
    Args:
        subject_id: Subject ID
        
    Returns:
        List of sessions for the subject
    """
    try:
        subject_obj_id = ObjectId(subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    sessions = await StudySessionService.list_subject_sessions(
        user_id=user_id,
        subject_id=subject_obj_id
    )
    
    session_responses = [
        SessionResponse(
            id=str(s.id),
            subject_id=str(s.subject_id),
            chapter_number=s.chapter_number,
            chapter_title=s.chapter_title,
            chat_id=str(s.chat_id) if s.chat_id else None,
            notes_uploaded=s.notes_uploaded,
            status=s.status,
            last_active=s.last_active,
            created_at=s.created_at
        )
        for s in sessions
    ]
    
    return SessionListResponse(
        sessions=session_responses,
        total=len(session_responses)
    )


@router.post("/{session_id}/end", response_model=SessionEndResponse)
async def end_session(
    session_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    End a study session.
    
    Args:
        session_id: Session ID
        
    Returns:
        Session completion confirmation
    """
    try:
        session_obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    
    try:
        result = await StudySessionService.end_session(
            user_id=user_id,
            session_id=session_obj_id
        )
        
        return SessionEndResponse(
            session_id=session_id,
            duration_minutes=result.get("duration_minutes", 0)
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
