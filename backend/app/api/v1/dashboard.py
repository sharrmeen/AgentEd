# backend/app/api/v1/dashboard.py

"""
Dashboard statistics endpoints - Calculate real stats from database.
"""

from fastapi import APIRouter, Depends
from bson import ObjectId
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.database import db
from app.api.deps import get_user_id

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    user_id: ObjectId = Depends(get_user_id)
) -> Dict[str, Any]:
    """
    Get real-time dashboard statistics calculated from actual data.
    
    Returns:
        total_study_hours: float - Total hours from study sessions
        quizzes_completed: int - Count of quiz results
        current_streak: int - Consecutive days with activity
        average_score: float - Average quiz percentage
    """
    
    # Get collections
    sessions_col = db.study_sessions()
    results_col = db.quiz_results()
    
    # 1. Calculate total study hours from sessions
    sessions_cursor = sessions_col.find({
        "user_id": user_id
    })
    sessions = await sessions_cursor.to_list(None)
    
    total_minutes = 0.0
    for session in sessions:
        created_at = session.get("created_at")
        ended_at = session.get("ended_at") or session.get("last_active") or datetime.utcnow()
        
        if created_at and ended_at:
            # Ensure both are datetime objects
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            if isinstance(ended_at, str):
                ended_at = datetime.fromisoformat(ended_at.replace('Z', '+00:00'))
            
            # Remove timezone info for comparison if needed
            if hasattr(created_at, 'tzinfo') and created_at.tzinfo:
                created_at = created_at.replace(tzinfo=None)
            if hasattr(ended_at, 'tzinfo') and ended_at.tzinfo:
                ended_at = ended_at.replace(tzinfo=None)
            
            duration = (ended_at - created_at).total_seconds() / 60  # minutes
            # Cap session duration at 8 hours max (to avoid unrealistic values)
            total_minutes += min(duration, 480)
    
    total_study_hours = round(total_minutes / 60, 1)
    
    # 2. Count completed quizzes
    quiz_results_cursor = results_col.find({
        "user_id": user_id
    })
    quiz_results = await quiz_results_cursor.to_list(None)
    quizzes_completed = len(quiz_results)
    
    # 3. Calculate average score
    average_score = 0.0
    if quiz_results:
        total_percentage = sum(r.get("percentage", 0) for r in quiz_results)
        average_score = round(total_percentage / len(quiz_results), 1)
    
    # 4. Calculate current streak (days with activity)
    current_streak = await _calculate_streak(user_id, sessions, quiz_results)
    
    return {
        "total_study_hours": total_study_hours,
        "quizzes_completed": quizzes_completed,
        "current_streak": current_streak,
        "average_score": average_score
    }


async def _calculate_streak(
    user_id: ObjectId,
    sessions: list,
    quiz_results: list
) -> int:
    """
    Calculate consecutive days streak.
    
    A day counts if there was:
    - A study session
    - A quiz taken
    - An objective completed
    """
    # Collect all activity dates
    activity_dates = set()
    
    # From sessions
    for session in sessions:
        created = session.get("created_at")
        if created:
            if isinstance(created, str):
                created = datetime.fromisoformat(created.replace('Z', '+00:00'))
            activity_dates.add(created.date())
    
    # From quiz results
    for result in quiz_results:
        completed = result.get("completed_at")
        if completed:
            if isinstance(completed, str):
                completed = datetime.fromisoformat(completed.replace('Z', '+00:00'))
            activity_dates.add(completed.date())
    
    # Also check planner activity (objectives completed)
    planner_col = db.planner_state()
    planners = await planner_col.find({"user_id": user_id}).to_list(None)
    
    for planner in planners:
        chapter_progress = planner.get("chapter_progress", {})
        for ch_data in chapter_progress.values():
            started = ch_data.get("started_at")
            completed = ch_data.get("completed_at")
            if started:
                if isinstance(started, str):
                    started = datetime.fromisoformat(started.replace('Z', '+00:00'))
                activity_dates.add(started.date())
            if completed:
                if isinstance(completed, str):
                    completed = datetime.fromisoformat(completed.replace('Z', '+00:00'))
                activity_dates.add(completed.date())
    
    if not activity_dates:
        return 0
    
    # Calculate streak from today going backwards
    today = datetime.utcnow().date()
    streak = 0
    current_date = today
    
    while current_date in activity_dates:
        streak += 1
        current_date -= timedelta(days=1)
    
    # If no activity today, check if yesterday counts (grace period)
    if streak == 0:
        yesterday = today - timedelta(days=1)
        current_date = yesterday
        while current_date in activity_dates:
            streak += 1
            current_date -= timedelta(days=1)
    
    return streak
