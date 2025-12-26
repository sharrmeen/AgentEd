# backend/app/schemas/common.py

"""
Common schemas used across all endpoints.
Provides standardized response formats.
"""

from typing import Any, Optional, List, Generic, TypeVar
from pydantic import BaseModel
from datetime import datetime


T = TypeVar('T')


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str = "Operation successful"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    message: str
    detail: Optional[str] = None
    code: Optional[str] = None


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int
    page: int
    per_page: int
    total_pages: int


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    success: bool = True
    data: List[Any]
    pagination: PaginationMeta


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    database: str = "connected"
    timestamp: datetime = datetime.utcnow()
