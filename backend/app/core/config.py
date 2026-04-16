# backend/app/core/config.py

"""
Application configuration using Pydantic Settings.

Loads environment variables from .env file.
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ============================
    # APPLICATION
    # ============================
    APP_NAME: str = "AgentEd"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    APP_URL_BASE: str = "https://app.agented.example"
    
    # ============================
    # API
    # ============================
    API_V1_PREFIX: str = "/api/v1"
    API_V2_PREFIX: str = "/api/v2"
    
    # ============================
    # CORS
    # ============================
    CORS_ORIGINS: List[str] = []
    ALLOWED_HOSTS: List[str] = []
    
    # ============================
    # MONGODB
    # ============================
    MONGODB_URI: str
    DB_NAME: str = "agented_db"

    # ============================
    # MULTI-TENANT / RBAC
    # ============================
    ENABLE_CLASS_BASED_ACCESS: bool = True
    
    # ============================
    # JWT AUTHENTICATION
    # ============================
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin"
    
    # ============================
    # API KEYS (set these in .env)
    # ============================
    TAVILY_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"

    # ============================
    # VECTOR DATABASE
    # ============================
    VECTOR_DB_PROVIDER: str = "pinecone"
    MAX_CHUNK_SIZE: int = 1200

    # Pinecone configuration
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_INDEX: Optional[str] = None
    PINECONE_NAMESPACE: str = "default"

    # ============================
    # FILE UPLOADS
    # ============================
    STORAGE_PROVIDER: str = "s3"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "png", "jpg", "jpeg"]

    # S3-compatible object storage (Backblaze B2, R2, MinIO, etc.)
    S3_KEY: Optional[str] = None
    S3_SECRET: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    S3_ENDPOINT: Optional[str] = None
    S3_REGION: Optional[str] = None
    S3_FORCE_PATH_STYLE: bool = True
    S3_PRESIGNED_URL_EXPIRE_SECONDS: int = 900
    
    # ============================
    # EMAIL / SMTP
    # ============================
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: str = "noreply@agented.com"
    FROM_NAME: str = "AgentED"
    
    
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
