# backend/app/api/v1/notifications.py

"""
Notification endpoints - Manage email notification preferences.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional

from app.core.database import db
from app.api.deps import get_user_id
from app.services.email_service import EmailService

router = APIRouter()


# ============================
# SCHEMAS
# ============================

class NotificationPreferences(BaseModel):
    """Notification preference settings."""
    email_enabled: bool = True
    study_reminders: bool = True
    reminder_hour: int = 9  # Hour in UTC (0-23)
    streak_alerts: bool = True
    weekly_summary: bool = True
    quiz_results: bool = True


class NotificationPreferencesResponse(BaseModel):
    """Response with current notification preferences."""
    email_enabled: bool
    study_reminders: bool
    reminder_hour: int
    streak_alerts: bool
    weekly_summary: bool
    quiz_results: bool


class SendTestEmailRequest(BaseModel):
    """Request to send a test email."""
    email_type: str = "study_reminder"  # study_reminder | streak_alert | weekly_summary


# ============================
# ENDPOINTS
# ============================

@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Get current notification preferences.
    
    Returns:
        Current notification settings
    """
    users_col = db.users()
    user = await users_col.find_one({"_id": user_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    prefs = user.get("preferences", {})
    notification_prefs = prefs.get("notifications", {})
    
    return NotificationPreferencesResponse(
        email_enabled=notification_prefs.get("email_enabled", True),
        study_reminders=notification_prefs.get("study_reminders", True),
        reminder_hour=notification_prefs.get("reminder_hour", 9),
        streak_alerts=notification_prefs.get("streak_alerts", True),
        weekly_summary=notification_prefs.get("weekly_summary", True),
        quiz_results=notification_prefs.get("quiz_results", True)
    )


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Update notification preferences.
    
    Args:
        preferences: New notification settings
        
    Returns:
        Updated notification settings
    """
    users_col = db.users()
    
    # Validate reminder hour
    if preferences.reminder_hour < 0 or preferences.reminder_hour > 23:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reminder_hour must be between 0 and 23"
        )
    
    # Update user preferences
    result = await users_col.update_one(
        {"_id": user_id},
        {
            "$set": {
                "preferences.notifications": {
                    "email_enabled": preferences.email_enabled,
                    "study_reminders": preferences.study_reminders,
                    "reminder_hour": preferences.reminder_hour,
                    "streak_alerts": preferences.streak_alerts,
                    "weekly_summary": preferences.weekly_summary,
                    "quiz_results": preferences.quiz_results
                }
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return NotificationPreferencesResponse(
        email_enabled=preferences.email_enabled,
        study_reminders=preferences.study_reminders,
        reminder_hour=preferences.reminder_hour,
        streak_alerts=preferences.streak_alerts,
        weekly_summary=preferences.weekly_summary,
        quiz_results=preferences.quiz_results
    )


@router.post("/test")
async def send_test_notification(
    request: SendTestEmailRequest,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Send a test notification email.
    
    Args:
        request: Type of email to send
        
    Returns:
        Success status
    """
    if request.email_type == "study_reminder":
        success = await EmailService.send_study_reminder(
            user_id, 
            custom_message="This is a test reminder email. Your actual reminders will include your current subjects and progress."
        )
    elif request.email_type == "streak_alert":
        success = await EmailService.send_streak_alert(user_id)
    elif request.email_type == "weekly_summary":
        success = await EmailService.send_weekly_summary(user_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email_type. Use: study_reminder, streak_alert, or weekly_summary"
        )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email. Check SMTP configuration."
        )
    
    return {"message": f"Test {request.email_type} email sent successfully"}


@router.post("/trigger/daily-reminders")
async def trigger_daily_reminders(
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Manually trigger daily reminders (admin/testing only).
    In production, this would be called by a scheduler.
    """
    count = await EmailService.process_daily_reminders()
    return {"message": f"Processed daily reminders", "sent_count": count}


@router.post("/trigger/streak-alerts")
async def trigger_streak_alerts(
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Manually trigger streak alerts (admin/testing only).
    In production, this would be called by a scheduler.
    """
    count = await EmailService.process_streak_alerts()
    return {"message": f"Processed streak alerts", "sent_count": count}


@router.post("/trigger/weekly-summaries")
async def trigger_weekly_summaries(
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Manually trigger weekly summaries (admin/testing only).
    In production, this would be called by a scheduler.
    """
    count = await EmailService.process_weekly_summaries()
    return {"message": f"Processed weekly summaries", "sent_count": count}
