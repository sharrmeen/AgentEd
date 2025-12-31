# backend/app/api/v1/__init__.py

"""
API v1 routes - Direct service calls (legacy).

Exposes all services directly via RESTful endpoints.
"""

from fastapi import APIRouter

from app.api.v1 import auth, subjects, syllabus, planner, sessions, chat, notes, quiz, feedback, dashboard, notifications

router = APIRouter(tags=["v1"])

# Include all v1 routers
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(subjects.router, prefix="/subjects", tags=["subjects"])
router.include_router(syllabus.router, prefix="/syllabus", tags=["syllabus"])
router.include_router(planner.router, prefix="/planner", tags=["planner"])
router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(notes.router, prefix="/notes", tags=["notes"])
router.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
