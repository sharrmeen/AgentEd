# backend/app/api/v1/subjects.py

"""
Subject management endpoints - CRUD operations for subjects.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from typing import Optional

from app.services.class_service import ClassService
from app.services.subject_service import SubjectService
from app.schemas.subject import (
    SubjectCreate,
    SubjectResponse,
    SubjectListResponse,
    SubjectDeleteResponse
)
from app.api.deps import get_current_user, get_user_id, normalize_role

router = APIRouter()


@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    request: SubjectCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new subject.
    
    Args:
        request: Subject creation data
        
    Returns:
        Created subject
    """
    user_id = ObjectId(current_user["id"])
    role = normalize_role(current_user.get("role"))

    if role == "teacher":
        if not request.class_ids:
            # Let it be empty, teachers can create subject before assigning to class
            pass
        else:
            for cid in request.class_ids:
                if not ObjectId.is_valid(cid):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid class ID format: {cid}",
                    )

                class_doc = await ClassService.get_class_by_id(ObjectId(cid))
                if not class_doc:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Class not found: {cid}",
                    )

                if class_doc.get("teacher_id") != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only assign subjects to your own classes",
                    )

    try:
        subject = await SubjectService.create_subject(
            user_id=user_id,
            subject_name=request.subject_name,
            class_ids=request.class_ids,
        )
        
        return SubjectResponse(
            id=str(subject.id),
            class_ids=[str(cid) for cid in subject.class_ids],
            subject_name=subject.subject_name,
            syllabus_id=str(subject.syllabus_id) if subject.syllabus_id else None,
            status=subject.status,
            created_at=subject.created_at,
            updated_at=subject.updated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=SubjectListResponse)
async def list_subjects(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    List all user's subjects with optional status filter.
    
    Query Parameters:
        status_filter: Filter by subject status (created, syllabus_uploaded, planned, in_progress, completed)
        
    Returns:
        List of subjects
    """
    user_id = ObjectId(current_user["id"])
    subjects = await SubjectService.list_user_subjects(
        user_id=user_id,
        status=status_filter,
        requester_role=current_user.get("role"),
        requester_class_id=current_user.get("class_id"),
    )
    
    subject_responses = [
        SubjectResponse(
            id=str(s.id),
            class_ids=[str(cid) for cid in getattr(s, "class_ids", [])],
            subject_name=s.subject_name,
            syllabus_id=str(s.syllabus_id) if s.syllabus_id else None,
            status=s.status,
            created_at=s.created_at,
            updated_at=s.updated_at
        )
        for s in subjects
    ]
    
    return SubjectListResponse(
        subjects=subject_responses,
        total=len(subject_responses)
    )


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific subject by ID.
    
    Args:
        subject_id: Subject ID
        
    Returns:
        Subject details
    """
    try:
        subject_obj_id = ObjectId(subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    user_id = ObjectId(current_user["id"])
    subject = await SubjectService.get_subject_by_id(
        user_id=user_id,
        subject_id=subject_obj_id,
        requester_role=current_user.get("role"),
        requester_class_id=current_user.get("class_id"),
    )
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    return SubjectResponse(
        id=str(subject.id),
        class_ids=[str(cid) for cid in getattr(subject, "class_ids", [])],
        subject_name=subject.subject_name,
        syllabus_id=str(subject.syllabus_id) if subject.syllabus_id else None,
        status=subject.status,
        created_at=subject.created_at,
        updated_at=subject.updated_at
    )


@router.delete("/{subject_id}", response_model=SubjectDeleteResponse)
async def delete_subject(
    subject_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Delete a subject.
    
    Args:
        subject_id: Subject ID to delete
        
    Returns:
        Confirmation message
    """
    try:
        subject_obj_id = ObjectId(subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        deleted = await SubjectService.delete_subject(
            user_id=user_id,
            subject_id=subject_obj_id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        return SubjectDeleteResponse(subject_id=subject_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
