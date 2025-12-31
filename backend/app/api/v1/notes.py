# backend/app/api/v1/notes.py

"""
Notes management endpoints - Upload and manage study notes.
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from bson import ObjectId
from typing import Optional

from app.services.notes_service import NotesService
from app.services.upload_service import UploadService
from app.services.subject_service import SubjectService
from app.schemas.notes import (
    NotesResponse,
    NotesUploadResponse,
    NotesListResponse,
    NotesDeleteResponse
)
from app.api.deps import get_user_id

router = APIRouter()


@router.post("/{subject_id}/upload", response_model=NotesUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_notes(
    subject_id: str,
    chapter: str,
    file: UploadFile = File(...),
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Upload study notes for a chapter.
    
    Supported formats:
    - PDF
    - DOCX
    - Images (PNG, JPG - OCR applied)
    
    Automatically ingests content into ChromaDB for RAG.
    
    Args:
        subject_id: Subject ID
        chapter: Chapter name or number
        file: Notes file
        
    Returns:
        Upload confirmation
    """
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
            subject=subject_id,
            chapter=chapter,
            file=file
        )
        
        # Create notes and ingest
        notes = await NotesService.create_and_ingest_note(
            user_id=user_id,
            subject_id=subject_obj_id,
            subject=subject_name,
            chapter=chapter,
            source_file=file.filename,
            file_path=upload_result["file_path"],
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
    user_id: ObjectId = Depends(get_user_id)
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
    
    try:
        notes = await NotesService.list_subject_notes(
            user_id=user_id,
            subject_id=subject_obj_id,
            chapter=chapter
        )
        
        note_responses = [
            NotesResponse(
                id=str(n.id),
                subject_id=str(n.subject_id),
                subject=n.subject,
                chapter=n.chapter,
                source_file=n.source_file,
                file_path=n.file_path,
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
    user_id: ObjectId = Depends(get_user_id)
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
    
    try:
        note = await NotesService.get_note_by_id(
            user_id=user_id,
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
            subject=note.subject,
            chapter=note.chapter,
            source_file=note.source_file,
            file_path=note.file_path,
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
    user_id: ObjectId = Depends(get_user_id)
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
    
    try:
        await NotesService.delete_note(
            user_id=user_id,
            note_id=note_obj_id
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
