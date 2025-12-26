# backend/app/services/syllabus_service.py

"""Syllabus service layer.
Links syllabus to existing Subject.

Workflow:
1. Subject must exist first
2. Upload syllabus file
3. Extract text (OCR/parser)
4. Link syllabus → subject
5. Update subject.status
"""

import os
from datetime import datetime
from typing import Optional
from bson import ObjectId

from app.core.database import db
from app.core.models.syllabus import Syllabus
from app.services.ocr_service import extract_text_preprocessed
from app.services.subject_service import SubjectService


class SyllabusService:
    
    @staticmethod
    async def create_syllabus(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        file_path: str,
        file_type: str,
    ) -> Syllabus:
        """
        Upload syllabus for existing subject.
        
        Steps:
        1. Validate subject exists
        2. Validate no existing syllabus
        3. Extract text from file
        4. Create syllabus document
        5. Link back to subject
        6. Update subject.status = "syllabus_uploaded"
        
        Args:
            user_id: Owner
            subject_id: Parent subject (must exist)
            file_path: Path to uploaded file
            file_type: "pdf" | "docx" | "image"
            
        Returns:
            Syllabus document
            
        Raises:
            ValueError: If subject not found or already has syllabus
        """
        subjects_col = db.subjects()
        syllabus_col = db.syllabus()
        
        # -------------------------
        # 1️⃣ Validate Subject
        # -------------------------
        subject = await subjects_col.find_one({
            "_id": subject_id,
            "user_id": user_id
        })
        
        if not subject:
            raise ValueError("Subject not found or unauthorized")
        
        # -------------------------
        # 2️⃣ Check Duplicate
        # -------------------------
        if subject.get("syllabus_id"):
            raise ValueError(
                f"Subject '{subject['subject_name']}' already has a syllabus. "
                "Delete the old one first if you want to replace it."
            )
        
        # -------------------------
        # 3️⃣ Validate File
        # -------------------------
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Syllabus file not found: {file_path}")
        
        ALLOWED_TYPES = {"pdf", "docx", "image"}
        if file_type not in ALLOWED_TYPES:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # -------------------------
        # 4️⃣ Extract Text
        # -------------------------
        raw_text = await SyllabusService._extract_text(file_path, file_type)
        
        if not raw_text or raw_text.strip() == "":
            raise ValueError("Failed to extract text from syllabus file.")
        
        # -------------------------
        # 5️⃣ Create Syllabus
        # -------------------------
        syllabus_doc = {
            "user_id": user_id,
            "subject_id": subject_id,
            "raw_text": raw_text,
            "source_file": os.path.basename(file_path),
            "file_type": file_type,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        result = await syllabus_col.insert_one(syllabus_doc)
        syllabus_id = result.inserted_id
        syllabus_doc["_id"] = syllabus_id
        
        # -------------------------
        # 6️⃣ Link to Subject
        # -------------------------
        await SubjectService.link_syllabus(
            user_id=user_id,
            subject_id=subject_id,
            syllabus_id=syllabus_id
        )
        
        return Syllabus(**syllabus_doc)
    
    # ============================
    # TEXT EXTRACTION
    # ============================
    
    @staticmethod
    async def _extract_text(file_path: str, file_type: str) -> str:
        """
        Extract text from file based on type.
        
        Supports:
        - PDF (text-based and scanned)
        - DOCX
        - Images (PNG, JPG, etc.)
        """
        if file_type == "image":
            # Use OCR
            return extract_text_preprocessed(file_path)
        
        elif file_type == "pdf":
            # Import PDF loader
            from langchain_community.document_loaders import UnstructuredPDFLoader
            
            try:
                loader = UnstructuredPDFLoader(file_path)
                documents = loader.load()
                
                if not documents:
                    # Fallback to OCR for scanned PDFs
                    return extract_text_preprocessed(file_path)
                
                # Combine all pages
                return "\n\n".join([doc.page_content for doc in documents])
            
            except Exception as e:
                print(f"PDF text extraction failed, trying OCR: {e}")
                return extract_text_preprocessed(file_path)
        
        elif file_type == "docx":
            # Import DOCX loader
            from langchain_community.document_loaders import UnstructuredWordDocumentLoader
            
            loader = UnstructuredWordDocumentLoader(file_path)
            documents = loader.load()
            
            if not documents:
                raise ValueError("No content in DOCX file")
            
            return "\n\n".join([doc.page_content for doc in documents])
        
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    # ============================
    # GET SYLLABUS
    # ============================
    
    @staticmethod
    async def get_by_subject_id(
        *,
        user_id: ObjectId,
        subject_id: ObjectId
    ) -> Optional[Syllabus]:
        """
        Retrieve syllabus for a subject.
        """
        syllabus_col = db.syllabus()
        
        doc = await syllabus_col.find_one({
            "subject_id": subject_id,
            "user_id": user_id
        })
        
        return Syllabus(**doc) if doc else None
    
    @staticmethod
    async def get_by_id(
        *,
        user_id: ObjectId,
        syllabus_id: ObjectId
    ) -> Optional[Syllabus]:
        """
        Retrieve syllabus by ID (ownership enforced).
        """
        syllabus_col = db.syllabus()
        
        doc = await syllabus_col.find_one({
            "_id": syllabus_id,
            "user_id": user_id
        })
        
        return Syllabus(**doc) if doc else None
    
    # ============================
    # DELETE
    # ============================
    
    @staticmethod
    async def delete_syllabus(
        *,
        user_id: ObjectId,
        syllabus_id: ObjectId
    ) -> bool:
        """
        Delete syllabus and unlink from subject.
        
        WARNING: This will prevent plan generation until new syllabus uploaded.
        
        Returns:
            True if deleted, False if not found
        """
        subjects_col = db.subjects()
        syllabus_col = db.syllabus()
        
        # Verify ownership
        syllabus = await syllabus_col.find_one({
            "_id": syllabus_id,
            "user_id": user_id
        })
        
        if not syllabus:
            return False
        
        # Unlink from subject
        await subjects_col.update_one(
            {
                "_id": syllabus["subject_id"],
                "user_id": user_id
            },
            {
                "$set": {
                    "syllabus_id": None,
                    "status": "created",  # Revert to created
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Delete syllabus
        result = await syllabus_col.delete_one({"_id": syllabus_id})
        
        return result.deleted_count > 0