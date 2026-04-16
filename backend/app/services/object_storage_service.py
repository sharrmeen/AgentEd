"""Object storage abstraction for cloud runtime.

Supports only S3-compatible storage (Backblaze B2, Cloudflare R2, MinIO, etc.).
"""

import os
from typing import Optional

from app.core.config import settings


class ObjectStorageService:
    def __init__(self):
        self.provider = settings.STORAGE_PROVIDER.lower().strip()
        if self.provider != "s3":
            raise ValueError("STORAGE_PROVIDER must be 's3' for cloud runtime")

    @staticmethod
    def _guess_content_type(file_name: str) -> str:
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        mapping = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
        }
        return mapping.get(ext, "application/octet-stream")

    def _get_s3_client(self):
        if not settings.S3_ENDPOINT:
            raise ValueError("S3_ENDPOINT is required when STORAGE_PROVIDER=s3")
        if not settings.S3_KEY or not settings.S3_SECRET:
            raise ValueError("S3_KEY and S3_SECRET are required when STORAGE_PROVIDER=s3")
        if not settings.S3_BUCKET:
            raise ValueError("S3_BUCKET is required when STORAGE_PROVIDER=s3")

        try:
            import boto3
        except ImportError as exc:
            raise ImportError("boto3 package is not installed") from exc

        return boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_KEY,
            aws_secret_access_key=settings.S3_SECRET,
            region_name=settings.S3_REGION,
        )

    def generate_presigned_download_url(
        self,
        *,
        object_key: str,
        file_name: Optional[str] = None,
        expires_in: Optional[int] = None,
    ) -> str:
        """Generate a time-limited download URL for private objects in S3-compatible storage."""
        if self.provider != "s3":
            raise ValueError("Presigned URL generation is only available for STORAGE_PROVIDER=s3")

        client = self._get_s3_client()
        effective_expires = expires_in or settings.S3_PRESIGNED_URL_EXPIRE_SECONDS

        params = {
            "Bucket": settings.S3_BUCKET,
            "Key": object_key,
        }
        if file_name:
            params["ResponseContentDisposition"] = f'attachment; filename="{file_name}"'

        return client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=effective_expires,
        )

    def upload_bytes(
        self,
        *,
        file_bytes: bytes,
        object_key: str,
        content_type: Optional[str] = None,
    ) -> dict:
        """Upload bytes to the configured provider.

        Returns a normalized metadata dictionary with storage information.
        """
        client = self._get_s3_client()
        content_type = content_type or "application/octet-stream"

        client.put_object(
            Bucket=settings.S3_BUCKET,
            Key=object_key,
            Body=file_bytes,
            ContentType=content_type,
        )

        object_url = f"{settings.S3_ENDPOINT.rstrip('/')}/{settings.S3_BUCKET}/{object_key}"
        return {
            "storage_type": "s3",
            "object_key": object_key,
            "object_url": object_url,
        }

    def upload_file(self, *, file_path: str, object_key: str) -> dict:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        content_type = self._guess_content_type(os.path.basename(file_path))
        return self.upload_bytes(
            file_bytes=file_bytes,
            object_key=object_key,
            content_type=content_type,
        )
