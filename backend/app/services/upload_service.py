import os
import shutil
import uuid
from datetime import datetime
from fastapi import UploadFile
from bson import ObjectId

BASE_DATA_DIR = "backend/data/users"
ALLOWED_EXTENSIONS = {"pdf", "docx", "png", "jpg", "jpeg"}


class UploadService:
    """
    Handles physical file uploads only (multi-user safe).
    No DB logic.
    """

    @staticmethod
    def _normalize(value: str) -> str:
        """
        Normalize text for safe filesystem usage.
        Removes/replaces invalid Windows filename characters: : < > " / \ | ? *
        """
        import re
        # Remove invalid Windows filename characters
        invalid_chars = r'[:\<\>"/\\|?*]'
        cleaned = re.sub(invalid_chars, '', value)
        # Replace spaces with underscores
        cleaned = cleaned.replace(" ", "_")
        return cleaned.strip().lower()

    @staticmethod
    def _validate_file(file: UploadFile) -> str:
        if not file.filename or "." not in file.filename:
            raise ValueError("Invalid filename")

        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")
        return ext

    @staticmethod
    def _user_root(user_id: ObjectId) -> str:
        path = os.path.join(BASE_DATA_DIR, str(user_id))
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def _unique_filename(original: str) -> str:
        name, ext = os.path.splitext(original)
        uid = uuid.uuid4().hex[:8]
        return f"{name}_{uid}{ext}"

    # ========================
    # Syllabus Upload
    # ========================

    @staticmethod
    async def upload_syllabus(
        *,
        user_id: ObjectId,
        subject: str,
        file: UploadFile,
    ) -> dict:
        ext = UploadService._validate_file(file)
        subject_norm = UploadService._normalize(subject)

        syllabus_dir = os.path.join(
            UploadService._user_root(user_id),
            "Syllabus",
        )
        os.makedirs(syllabus_dir, exist_ok=True)

        filename = f"{subject_norm}.{ext}"
        file_path = os.path.join(syllabus_dir, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "file_path": file_path,
            "file_type": ext,
            "source_file": filename,
        }

    # ========================
    # Notes Upload
    # ========================

    @staticmethod
    async def upload_notes(
        *,
        user_id: ObjectId,
        subject: str,
        chapter: str,
        file: UploadFile,
    ) -> dict:
        ext = UploadService._validate_file(file)

        subject_norm = UploadService._normalize(subject)
        chapter_norm = UploadService._normalize(chapter)

        notes_dir = os.path.join(
            UploadService._user_root(user_id),
            "Notes",
            subject_norm,
            chapter_norm,
        )
        os.makedirs(notes_dir, exist_ok=True)

        safe_filename = UploadService._unique_filename(
            UploadService._normalize(file.filename)
        )

        file_path = os.path.join(notes_dir, safe_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "file_path": file_path,
            "file_type": ext,
            "source_file": safe_filename,
        }
