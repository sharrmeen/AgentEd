# backend/app/api/__init__.py

"""
API Router Layer - Exposes services via RESTful endpoints.

Structure:
- /api/v1/* → Direct service calls (legacy)
- /api/v2/* → Agent workflows (intelligent)
"""

from fastapi import APIRouter

from app.api.v1 import router as v1_router
from app.api.v2 import router as v2_router


# Main API router
api_router = APIRouter()

# Include versioned routers
api_router.include_router(v1_router, prefix="/v1")
api_router.include_router(v2_router, prefix="/v2")
