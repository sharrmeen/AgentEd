# backend/app/core/config.py

"""
Application configuration using Pydantic Settings.

Loads environment variables from .env file.
"""

import os
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
    
    # ============================
    # API
    # ============================
    API_V1_PREFIX: str = "/api/v1"
    API_V2_PREFIX: str = "/api/v2"
    
    # ============================
    # CORS
    # ============================
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "*"]
    
    # ============================
    # MONGODB
    # ============================
    MONGODB_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "agented_db"
    
    # ============================
    # JWT AUTHENTICATION
    # ============================
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # ============================
    # API KEYS (set these in .env)
    # ============================
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4"
    TAVILY_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # ============================
    # CHROMADB
    # ============================
    CHROMA_PERSIST_DIRECTORY: str = "backend/chroma_db"
    MAX_CHUNK_SIZE: int = 1200

    # ============================
    # FILE UPLOADS
    # ============================
    UPLOAD_DIR: str = "backend/data/users"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "png", "jpg", "jpeg"]
    # (Removed CHROMA_DB_DIRECTORY: use CHROMA_PERSIST_DIRECTORY only)
    
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
