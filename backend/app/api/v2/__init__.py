# backend/app/api/v2/__init__.py

"""
API v2 routes - Intelligent agent workflows.

Exposes LangGraph agent orchestration via endpoints.
Supports multi-agent workflows for complex queries.
"""

from fastapi import APIRouter

from app.api.v2 import agent, chat

router = APIRouter(tags=["v2"])

# Include v2 routers
router.include_router(agent.router, prefix="/agent", tags=["agent"])
router.include_router(chat.router, prefix="/chat", tags=["agent-chat"])
