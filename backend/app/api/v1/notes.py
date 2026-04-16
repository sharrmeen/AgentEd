# backend/app/api/v1/notes.py

"""
Notes management endpoints - Upload and manage study notes.
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import FileResponse
from bson import ObjectId
from typing import Optional
import os

from app.services.notes_service import NotesService
from app.services.upload_service import UploadService
from app.services.object_storage_service import ObjectStorageService
from app.services.subject_service import SubjectService
from app.core.config import settings
from app.schemas.notes import (
    NotesResponse,
    NotesUploadResponse,
    NotesListResponse,
    NotesDeleteResponse,
    NotesDownloadUrlResponse,
)
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/user/all", response_model=NotesListResponse)
async def list_all_user_notes(
    current_user: dict = Depends(get_current_user)
):
    """
    List ALL notes uploaded by the current user across all subjects.
    
    Returns:
        List of all notes for the user
    """
    try:
        user_id = ObjectId(current_user["id"])
        role = current_user.get("role", "student")
        class_id = current_user.get("class_id")
        notes = await NotesService.list_user_all_notes(
            requester_id=user_id,
            requester_role=role,
            requester_class_id=class_id,
        )
        
        note_responses = [
            NotesResponse(
                id=str(n.id),
                subject_id=str(n.subject_id),
                class_id=n.class_id,
                teacher_id=str(n.teacher_id) if n.teacher_id else None,
                role=n.role,
                subject=n.subject,
                chapter=n.chapter,
                source_file=n.source_file,
                file_path=n.file_path,
                storage_type=n.storage_type,
                object_key=n.object_key,
                object_url=n.object_url,
                file_type=n.file_type,
                created_at=n.created_at,
                updated_at=n.updated_at
            )
            for n in notes
        ]
        
        return NotesListResponse(
            notes=note_responses,
            total=len(note_responses)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{subject_id}/upload", response_model=NotesUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_notes(
    subject_id: str,
    chapter: str,
    class_id: Optional[str] = None,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload study notes for a chapter.
    
    Supported formats:
    - PDF
    - DOCX
    - Images (PNG, JPG - OCR applied)
    
    Automatically ingests content into vector store for RAG.
    
    Args:
        subject_id: Subject ID
        chapter: Chapter name or number
        file: Notes file
        
    Returns:
        Upload confirmation
    """
    user_id = ObjectId(current_user["id"])
    role = current_user.get("role", "student")
    requester_class_id = current_user.get("class_id")

    if role == "teacher" and not class_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teachers must provide class_id when uploading notes",
        )

    if role == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students are not allowed to upload class notes",
        )

    effective_class_id = class_id or requester_class_id

    try:
        subject_obj_id = ObjectId(subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        # Get subject details to get the subject name
        subject = await SubjectService.get_subject_by_id(
            user_id=user_id,
            subject_id=subject_obj_id
        )
        
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        subject_name = subject.subject_name
        
        # Get file type from content type
        file_type = "image"
        if file.content_type:
            if "pdf" in file.content_type:
                file_type = "pdf"
            elif "word" in file.content_type or "docx" in file.content_type:
                file_type = "docx"
            elif "image" in file.content_type:
                file_type = "image"
        
        # Upload file
        upload_result = await UploadService.upload_notes(
            user_id=user_id,
            subject=subject_name,
            chapter=chapter,
            class_id=effective_class_id,
            teacher_id=str(user_id),
            file=file
        )
        
        # Create notes and ingest
        notes = await NotesService.create_and_ingest_note(
            user_id=user_id,
            subject_id=subject_obj_id,
            class_id=effective_class_id,
            teacher_id=user_id,
            role=role,
            subject=subject_name,
            chapter=chapter,
            source_file=file.filename,
            file_path=upload_result["file_path"],
            storage_type=upload_result.get("storage_type", "s3"),
            object_key=upload_result.get("object_key"),
            object_url=upload_result.get("object_url"),
            file_type=file_type
        )
        
        return NotesUploadResponse(
            note_id=str(notes.id),
            file_path=notes.file_path,
            ingestion_status=notes.ingestion_status if hasattr(notes, 'ingestion_status') else "completed"
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
        print(f"❌ Notes upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload notes: {str(e)}"
        )


@router.get("/{subject_id}", response_model=NotesListResponse)
async def list_notes(
    subject_id: str,
    chapter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    List all notes for a subject.
    
    Query Parameters:
        chapter: Filter by chapter name
        
    Args:
        subject_id: Subject ID
        
    Returns:
        List of notes
    """
    try:
        subject_obj_id = ObjectId(subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    user_id = ObjectId(current_user["id"])
    role = current_user.get("role", "student")
    class_id = current_user.get("class_id")

    try:
        notes = await NotesService.list_subject_notes(
            requester_id=user_id,
            requester_role=role,
            requester_class_id=class_id,
            subject_id=subject_obj_id,
            chapter=chapter
        )
        
        note_responses = [
            NotesResponse(
                id=str(n.id),
                subject_id=str(n.subject_id),
                class_id=n.class_id,
                teacher_id=str(n.teacher_id) if n.teacher_id else None,
                role=n.role,
                subject=n.subject,
                chapter=n.chapter,
                source_file=n.source_file,
                file_path=n.file_path,
                storage_type=n.storage_type,
                object_key=n.object_key,
                object_url=n.object_url,
                file_type=n.file_type,
                created_at=n.created_at,
                updated_at=n.updated_at
            )
            for n in notes
        ]
        
        return NotesListResponse(
            notes=note_responses,
            total=len(note_responses)
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


@router.get("/{note_id}/detail", response_model=NotesResponse)
async def get_note(
    note_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get details of a specific note.
    
    Args:
        note_id: Note ID
        
    Returns:
        Note metadata
    """
    try:
        note_obj_id = ObjectId(note_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format"
        )
    
    user_id = ObjectId(current_user["id"])
    role = current_user.get("role", "student")
    class_id = current_user.get("class_id")

    try:
        note = await NotesService.get_note_by_id(
            requester_id=user_id,
            requester_role=role,
            requester_class_id=class_id,
            note_id=note_obj_id
        )
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        return NotesResponse(
            id=str(note.id),
            subject_id=str(note.subject_id),
            class_id=note.class_id,
            teacher_id=str(note.teacher_id) if note.teacher_id else None,
            role=note.role,
            subject=note.subject,
            chapter=note.chapter,
            source_file=note.source_file,
            file_path=note.file_path,
            storage_type=note.storage_type,
            object_key=note.object_key,
            object_url=note.object_url,
            file_type=note.file_type,
            created_at=note.created_at,
            updated_at=note.updated_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{note_id}", response_model=NotesDeleteResponse)
async def delete_note(
    note_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a note.
    
    Args:
        note_id: Note ID to delete
        
    Returns:
        Confirmation message
    """
    try:
        note_obj_id = ObjectId(note_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format"
        )
    
    user_id = ObjectId(current_user["id"])
    role = current_user.get("role", "student")

    try:
        deleted = await NotesService.delete_note(
            requester_id=user_id,
            requester_role=role,
            note_id=note_obj_id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found or unauthorized"
            )
        
        return NotesDeleteResponse(note_id=note_id)
    
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


@router.get("/{note_id}/download-url", response_model=NotesDownloadUrlResponse)
async def get_note_download_url(
    note_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Return a secure download target for the requested note."""
    try:
        note_obj_id = ObjectId(note_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format"
        )

    user_id = ObjectId(current_user["id"])
    role = current_user.get("role", "student")
    class_id = current_user.get("class_id")

    note = await NotesService.get_note_by_id(
        requester_id=user_id,
        requester_role=role,
        requester_class_id=class_id,
        note_id=note_obj_id,
    )

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    if note.storage_type == "s3" and note.object_key:
        try:
            signed_url = ObjectStorageService().generate_presigned_download_url(
                object_key=note.object_key,
                file_name=note.source_file,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate signed URL: {str(e)}"
            )

        return NotesDownloadUrlResponse(
            download_url=signed_url,
            requires_auth=False,
            expires_in=settings.S3_PRESIGNED_URL_EXPIRE_SECONDS,
        )

    return NotesDownloadUrlResponse(
        download_url=f"/api/v1/notes/{note_id}/download-file",
        requires_auth=True,
        expires_in=None,
    )


@router.get("/{note_id}/download-file")
async def download_note_file(
    note_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Download note content through an authenticated endpoint."""
    try:
        note_obj_id = ObjectId(note_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format"
        )

    user_id = ObjectId(current_user["id"])
    role = current_user.get("role", "student")
    class_id = current_user.get("class_id")

    note = await NotesService.get_note_by_id(
        requester_id=user_id,
        requester_role=role,
        requester_class_id=class_id,
        note_id=note_obj_id,
    )

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    if not os.path.exists(note.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileResponse(
        path=note.file_path,
        filename=note.source_file,
        media_type="application/octet-stream",
    )
