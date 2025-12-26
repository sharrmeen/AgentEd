# backend/app/api/v1/syllabus.py

"""
Syllabus management endpoints - Upload and manage syllabi.
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from bson import ObjectId

from app.services.syllabus_service import SyllabusService
from app.services.upload_service import UploadService
from app.schemas.syllabus import (
    SyllabusResponse,
    SyllabusUploadResponse,
    SyllabusDeleteResponse
)
from app.api.deps import get_user_id

router = APIRouter()


@router.post("/{subject_id}/upload", response_model=SyllabusUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_syllabus(
    subject_id: str,
    file: UploadFile = File(...),
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Upload a syllabus file for a subject.
    
    Supported formats:
    - PDF (text-based and scanned)
    - DOCX (Word documents)
    - Images (PNG, JPG - OCR applied)
    
    Args:
        subject_id: Subject to attach syllabus to
        file: Syllabus file (PDF, DOCX, or image)
        
    Returns:
        Upload confirmation with preview
    """
    try:
        subject_obj_id = ObjectId(subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        # Upload file
        upload_result = await UploadService.upload_syllabus(
            user_id=user_id,
            subject=subject_id,
            file=file
        )
        
        # Create syllabus document
        syllabus = await SyllabusService.create_syllabus(
            user_id=user_id,
            subject_id=subject_obj_id,
            file_path=upload_result["file_path"],
            file_type=upload_result["file_type"]
        )
        
        # Get text preview (first 500 chars)
        text_preview = syllabus.raw_text[:500] if syllabus.raw_text else ""
        
        return SyllabusUploadResponse(
            syllabus_id=str(syllabus.id),
            subject_id=subject_id,
            text_preview=text_preview,
            file_type=syllabus.file_type,
            source_file=syllabus.source_file,
            created_at=syllabus.created_at
        )
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process syllabus: {str(e)}"
        )


@router.get("/{subject_id}", response_model=SyllabusResponse)
async def get_syllabus(
    subject_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Get syllabus for a subject.
    
    Args:
        subject_id: Subject ID
        
    Returns:
        Full syllabus content
    """
    try:
        subject_obj_id = ObjectId(subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        syllabus = await SyllabusService.get_by_subject_id(
            user_id=user_id,
            subject_id=subject_obj_id
        )
        
        if not syllabus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Syllabus not found for this subject"
            )
        
        return SyllabusResponse(
            id=str(syllabus.id),
            subject_id=str(syllabus.subject_id),
            raw_text=syllabus.raw_text,
            source_file=syllabus.source_file,
            file_type=syllabus.file_type,
            created_at=syllabus.created_at,
            updated_at=syllabus.updated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{subject_id}", response_model=SyllabusDeleteResponse)
async def delete_syllabus(
    subject_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Delete syllabus for a subject.
    
    Args:
        subject_id: Subject ID
        
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
        await SyllabusService.delete_syllabus(
            user_id=user_id,
            subject_id=subject_obj_id
        )
        
        return SyllabusDeleteResponse(syllabus_id=subject_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
