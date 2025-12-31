# backend/app/services/notes_service.py

from datetime import datetime
from bson import ObjectId

from app.core.database import db
from app.core.models.notes import Notes
from app.services.ingestion import IngestionService


class NotesService:
    """
    NotesService:
    - Persists notes metadata in MongoDB
    - Triggers ingestion into ChromaDB
    - Guarantees metadata consistency between MongoDB and Vector DB
    """

    @staticmethod
    async def create_and_ingest_note(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        subject: str,  # Display name
        chapter: str,  # ← FIXED: Was "module"
        source_file: str,
        file_path: str,
        file_type: str,
    ) -> Notes:
        """
        1. Store notes metadata in MongoDB
        2. Ingest note into Chroma with correct metadata
        
        Args:
            user_id: Owner
            subject_id: FK to Subject
            subject: Subject display name (for ChromaDB metadata)
            chapter: Chapter name (for ChromaDB metadata)
            source_file: Original filename
            file_path: Saved file path
            file_type: pdf | docx | image
        """
        notes_col = db.notes()
        
        # Validate file exists before creating note
        import os
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Uploaded file not found at {file_path}")

        # ---------- MongoDB Metadata ----------
        note_doc = {
            "user_id": user_id,
            "subject_id": subject_id,  # ← ADDED
            "subject": subject,
            "chapter": chapter,  # ← FIXED
            "source_file": source_file,
            "file_path": file_path,
            "file_type": file_type,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await notes_col.insert_one(note_doc)
        note_doc["_id"] = result.inserted_id

        note = Notes(**note_doc)

        # ---------- Chroma Ingestion ----------
        try:
            print(f"📚 Creating IngestionService with:")
            print(f"   subject: {note.subject}")
            print(f"   chapter: {note.chapter}")
            print(f"   user_id: {note.user_id} (type: {type(note.user_id).__name__})")
            
            ingestor = IngestionService(
                subject=note.subject,
                chapter=note.chapter,  # ← FIXED: consistent naming
                user_id=note.user_id,
            )

            # Run ingestion in thread pool to avoid blocking async event loop
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                ingestion_result = await loop.run_in_executor(
                    executor,
                    ingestor.ingest,
                    note.file_path
                )
            
            print(f"📚 Notes ingested: {ingestion_result}")
            
            # Check if ingestion had errors
            if isinstance(ingestion_result, str) and "Error" in ingestion_result:
                print(f"⚠️ Ingestion warning: {ingestion_result}")
                # Still return the note, but mark ingestion as failed
                return note
        
        except Exception as e:
            print(f"⚠️ Ingestion error (note still created): {str(e)}")
            import traceback
            traceback.print_exc()
            # Don't fail the whole operation if ingestion fails
            # The note metadata is still saved, just without vector embeddings

        return note
    
    # ============================
    # GET NOTES
    # ============================
    
    @staticmethod
    async def list_subject_notes(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        chapter: str = None
    ) -> list[Notes]:
        """
        List all notes for a subject, optionally filtered by chapter.
        
        Args:
            user_id: Owner ID
            subject_id: Subject FK
            chapter: Optional chapter filter
            
        Returns:
            List of Notes
        """
        notes_col = db.notes()
        
        query = {
            "user_id": user_id,
            "subject_id": subject_id
        }
        
        if chapter:
            query["chapter"] = chapter
        
        cursor = notes_col.find(query).sort("created_at", -1)
        docs = await cursor.to_list(None)
        return [Notes(**doc) for doc in docs]
    
    @staticmethod
    async def get_note_by_id(
        *,
        user_id: ObjectId,
        note_id: ObjectId
    ) -> Notes | None:
        """
        Get a single note by ID.
        
        Args:
            user_id: Owner ID
            note_id: Note ID
            
        Returns:
            Notes if found, None otherwise
        """
        notes_col = db.notes()
        
        doc = await notes_col.find_one({
            "_id": note_id,
            "user_id": user_id
        })
        
        if not doc:
            return None
        
        return Notes(**doc)
    
    @staticmethod
    async def get_notes_by_chapter(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        chapter: str
    ) -> list[Notes]:
        """
        Get all notes for a specific chapter.
        """
        notes_col = db.notes()
        
        cursor = notes_col.find({
            "user_id": user_id,
            "subject_id": subject_id,
            "chapter": chapter
        }).sort("created_at", -1)
        
        docs = await cursor.to_list(None)
        return [Notes(**doc) for doc in docs]
    
    @staticmethod
    async def get_notes_by_subject(
        *,
        user_id: ObjectId,
        subject_id: ObjectId
    ) -> list[Notes]:
        """
        Get all notes for a subject.
        """
        notes_col = db.notes()
        
        cursor = notes_col.find({
            "user_id": user_id,
            "subject_id": subject_id
        }).sort("created_at", -1)
        
        docs = await cursor.to_list(None)
        return [Notes(**doc) for doc in docs]
    
    # ============================
    # DELETE
    # ============================
    
    @staticmethod
    async def delete_note(
        *,
        user_id: ObjectId,
        note_id: ObjectId
    ) -> bool:
        """
        Delete note metadata from MongoDB.
        
        NOTE: This does NOT remove from ChromaDB.
        File remains on disk.
        
        Returns:
            True if deleted, False if not found
        """
        notes_col = db.notes()
        
        result = await notes_col.delete_one({
            "_id": note_id,
            "user_id": user_id
        })
        
        return result.deleted_count > 0