import os
import shutil
import uuid
import tempfile
from fastapi import UploadFile
from bson import ObjectId

from app.core.config import settings
from app.services.object_storage_service import ObjectStorageService

ALLOWED_EXTENSIONS = {"pdf", "docx", "png", "jpg", "jpeg"}


class UploadService:
    """
    Handles physical file uploads only (multi-user safe).
    No DB logic.
    """

    storage = ObjectStorageService()

    @staticmethod
    def _normalize(value: str) -> str:
        """
        Normalize text for safe filesystem usage.
        Removes/replaces invalid Windows filename characters: colon, angle brackets, quotes, slash, backslash, pipe, question mark, asterisk.
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
    def _unique_filename(original: str) -> str:
        name, ext = os.path.splitext(original)
        uid = uuid.uuid4().hex[:8]
        return f"{name}_{uid}{ext}"

    @staticmethod
    def _write_to_temp_file(file: UploadFile, suffix: str) -> str:
        file.file.seek(0)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            return tmp.name

    # ========================
    # Syllabus Upload
    # ========================

    @staticmethod
    async def upload_syllabus(
        *,
        user_id: ObjectId,
        subject: str,
        file: UploadFile,
        class_id: str | None = None,
        teacher_id: str | None = None,
    ) -> dict:
        ext = UploadService._validate_file(file)
        subject_norm = UploadService._normalize(subject)

        filename = f"{subject_norm}.{ext}"
        file_path = UploadService._write_to_temp_file(file, f".{ext}")

        object_key = UploadService._build_object_key(
            class_id=class_id,
            owner_id=str(user_id),
            file_type="syllabus",
            subject=subject_norm,
            chapter="root",
            file_name=filename,
            teacher_id=teacher_id,
        )
        storage_meta = UploadService.storage.upload_file(
            file_path=file_path,
            object_key=object_key,
        )

        return {
            "file_path": file_path,
            "file_type": ext,
            "source_file": filename,
            **storage_meta,
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
        class_id: str | None = None,
        teacher_id: str | None = None,
    ) -> dict:
        ext = UploadService._validate_file(file)

        subject_norm = UploadService._normalize(subject)
        chapter_norm = UploadService._normalize(chapter)

        safe_filename = UploadService._unique_filename(
            UploadService._normalize(file.filename)
        )

        file_path = UploadService._write_to_temp_file(file, f".{ext}")

        object_key = UploadService._build_object_key(
            class_id=class_id,
            owner_id=str(user_id),
            file_type="notes",
            subject=subject_norm,
            chapter=chapter_norm,
            file_name=safe_filename,
            teacher_id=teacher_id,
        )
        storage_meta = UploadService.storage.upload_file(
            file_path=file_path,
            object_key=object_key,
        )

        return {
            "file_path": file_path,
            "file_type": ext,
            "source_file": safe_filename,
            **storage_meta,
        }

    @staticmethod
    def _build_object_key(
        *,
        class_id: str | None,
        owner_id: str,
        file_type: str,
        subject: str,
        chapter: str,
        file_name: str,
        teacher_id: str | None,
    ) -> str:
        """Build deterministic object keys for class-aware cloud storage."""
        owner_scope = f"classes/{class_id}" if class_id else f"users/{owner_id}"
        teacher_scope = f"teacher_{teacher_id}/" if teacher_id else ""
        return f"{owner_scope}/{teacher_scope}{file_type}/{subject}/{chapter}/{file_name}"
