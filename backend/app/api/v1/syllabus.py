# backend/app/api/v1/syllabus.py

"""
Syllabus management endpoints - Upload and manage syllabi.
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from bson import ObjectId

from app.services.syllabus_service import SyllabusService
from app.services.class_service import ClassService
from app.services.upload_service import UploadService
from app.services.ingestion import IngestionService
from app.services.subject_service import SubjectService
from app.schemas.syllabus import (
    SyllabusResponse,
    SyllabusUploadResponse,
    SyllabusDeleteResponse
)
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/{subject_id}/upload", response_model=SyllabusUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_syllabus(
    subject_id: str,
    class_id: str | None = None,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
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
    
    temp_file_path: str | None = None
    upload_result: dict = {}

    try:
        user_id = ObjectId(current_user["id"])
        role = current_user.get("role", "student")
        requester_class_id = current_user.get("class_id")

        if role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not allowed to upload syllabus",
            )

        effective_class_id = class_id or requester_class_id

        subject = await SubjectService.get_subject_by_id(
            user_id=user_id,
            subject_id=subject_obj_id
        )

        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )

        subject_class_ids = [str(cid) for cid in getattr(subject, "class_ids", [])]
        if not subject_class_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assign at least one class to this subject before uploading content",
            )

        if not effective_class_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="class_id is required for uploads",
            )

        if not ObjectId.is_valid(effective_class_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid class ID format",
            )

        class_doc = await ClassService.get_class_by_id(ObjectId(effective_class_id))
        if not class_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found",
            )

        if role == "teacher" and class_doc.get("teacher_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload content to your own classes",
            )

        if effective_class_id not in subject_class_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected class is not assigned to this subject",
            )

        # Upload file
        upload_result = await UploadService.upload_syllabus(
            user_id=user_id,
            subject=subject.subject_name,
            file=file,
            class_id=effective_class_id,
            teacher_id=str(user_id),
        )
        temp_file_path = upload_result.get("file_path")
        
        # Create syllabus document
        syllabus = await SyllabusService.create_syllabus(
            user_id=user_id,
            subject_id=subject_obj_id,
            file_path=upload_result["file_path"],
            file_type=upload_result["file_type"],
            source_file=upload_result.get("source_file") or file.filename,
        )
        
        # Index syllabus content into vector store for RAG
        try:
            subject_service = await SubjectService.get_subject_by_id(
                user_id=user_id,
                subject_id=subject_obj_id
            )
            subject_name = subject_service.subject_name if subject_service else "Unknown"
            
            ingestion = IngestionService(
                subject=subject_name,
                user_id=user_id,
                class_id=effective_class_id,
                teacher_id=user_id,
                subject_id=subject_obj_id,
                role=role,
            )
            ingest_result = ingestion.ingest(upload_result["file_path"])
            print(f"✅ Syllabus indexed into vector store: {ingest_result}")
        except Exception as e:
            print(f"⚠️ Warning: Failed to index syllabus into vector store: {str(e)}")
            # Don't fail the upload if indexing fails - user can still use the syllabus
        
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
    finally:
        if upload_result.get("storage_type") == "s3" and temp_file_path:
            import os
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except OSError:
                pass


@router.get("/{subject_id}", response_model=SyllabusResponse)
async def get_syllabus(
    subject_id: str,
    current_user: dict = Depends(get_current_user)
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
        user_id = ObjectId(current_user["id"])
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
    current_user: dict = Depends(get_current_user)
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
        user_id = ObjectId(current_user["id"])
        syllabus = await SyllabusService.get_by_subject_id(
            user_id=user_id,
            subject_id=subject_obj_id,
        )
        if not syllabus:
            raise ValueError("Syllabus not found for this subject")

        deleted = await SyllabusService.delete_syllabus(
            user_id=user_id,
            syllabus_id=ObjectId(syllabus.id),
        )
        if not deleted:
            raise ValueError("Failed to delete syllabus")
        
        return SyllabusDeleteResponse(syllabus_id=subject_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
