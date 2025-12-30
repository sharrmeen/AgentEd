# backend/app/api/__init__.py

"""
API Router Layer - Exposes services via RESTful endpoints.

Structure:
- /api/v1/* → User-facing API (chat, notes, quiz, etc.)
"""

from fastapi import APIRouter

from app.api.v1 import router as v1_router


# Main API router
api_router = APIRouter()

# Include versioned routers
api_router.include_router(v1_router, prefix="/v1")
