# backend/app/services/email_service.py

"""
EmailService - Email notifications and reminders.

Responsibilities:
- Send study reminders
- Send streak notifications
- Send quiz completion summaries
- Send weekly progress reports
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from bson import ObjectId
from jinja2 import Template

from app.core.database import db
from app.core.config import get_settings

settings = get_settings()


class EmailService:
    """Email notification service."""
    
    # Email configuration from settings
    SMTP_HOST = settings.SMTP_HOST
    SMTP_PORT = settings.SMTP_PORT
    SMTP_USER = settings.SMTP_USER
    SMTP_PASSWORD = settings.SMTP_PASSWORD
    FROM_EMAIL = settings.FROM_EMAIL
    FROM_NAME = settings.FROM_NAME
    
    # ============================
    # EMAIL TEMPLATES
    # ============================
    
    STUDY_REMINDER_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }
            .btn { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin-top: 20px; }
            .stats { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .stat-item { display: inline-block; width: 30%; text-align: center; }
            .stat-value { font-size: 24px; font-weight: bold; color: #667eea; }
            .stat-label { font-size: 12px; color: #666; }
            .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📚 Time to Study!</h1>
            </div>
            <div class="content">
                <p>Hi {{ user_name }},</p>
                <p>{{ message }}</p>
                
                {% if subjects %}
                <div class="stats">
                    <h3>Your Active Subjects:</h3>
                    <ul>
                    {% for subject in subjects %}
                        <li><strong>{{ subject.name }}</strong> - {{ subject.progress }}% complete</li>
                    {% endfor %}
                    </ul>
                </div>
                {% endif %}
                
                {% if streak > 0 %}
                <p>🔥 You're on a <strong>{{ streak }}-day streak!</strong> Keep it going!</p>
                {% endif %}
                
                <a href="{{ app_url }}" class="btn">Start Studying</a>
            </div>
            <div class="footer">
                <p>You're receiving this because you enabled study reminders.</p>
                <p>AgentED - Your AI Study Assistant</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    STREAK_ALERT_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }
            .btn { display: inline-block; background: #f5576c; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin-top: 20px; }
            .emoji { font-size: 48px; }
            .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <p class="emoji">🔥</p>
                <h1>Don't Break Your Streak!</h1>
            </div>
            <div class="content">
                <p>Hi {{ user_name }},</p>
                <p>You have a <strong>{{ streak }}-day study streak</strong> going! Don't let it slip away.</p>
                <p>Just a quick 10-minute session can keep your streak alive and your learning on track.</p>
                
                <a href="{{ app_url }}" class="btn">Study Now</a>
            </div>
            <div class="footer">
                <p>You're receiving this because you enabled streak alerts.</p>
                <p>AgentED - Your AI Study Assistant</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    WEEKLY_SUMMARY_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }
            .stats { display: flex; justify-content: space-around; background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .stat-item { text-align: center; }
            .stat-value { font-size: 28px; font-weight: bold; color: #11998e; }
            .stat-label { font-size: 12px; color: #666; }
            .btn { display: inline-block; background: #11998e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin-top: 20px; }
            .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Your Weekly Progress</h1>
                <p>Week of {{ week_start }} - {{ week_end }}</p>
            </div>
            <div class="content">
                <p>Hi {{ user_name }},</p>
                <p>Here's your learning summary for this week:</p>
                
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-value">{{ study_hours }}h</div>
                        <div class="stat-label">Study Hours</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ quizzes_completed }}</div>
                        <div class="stat-label">Quizzes Taken</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ avg_score }}%</div>
                        <div class="stat-label">Avg Score</div>
                    </div>
                </div>
                
                {% if achievements %}
                <h3>🏆 Achievements This Week:</h3>
                <ul>
                {% for achievement in achievements %}
                    <li>{{ achievement }}</li>
                {% endfor %}
                </ul>
                {% endif %}
                
                <p>Keep up the great work! Consistency is key to mastering any subject.</p>
                
                <a href="{{ app_url }}" class="btn">Continue Learning</a>
            </div>
            <div class="footer">
                <p>You're receiving this because you enabled weekly summaries.</p>
                <p>AgentED - Your AI Study Assistant</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # ============================
    # CORE EMAIL METHODS
    # ============================
    
    @staticmethod
    def _send_email(to_email: str, subject: str, html_content: str) -> bool:
        """Send email via SMTP."""
        if not EmailService.SMTP_USER or not EmailService.SMTP_PASSWORD:
            print("⚠️ Email not configured. Set SMTP_USER and SMTP_PASSWORD in .env")
            return False
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{EmailService.FROM_NAME} <{EmailService.FROM_EMAIL}>"
            message["To"] = to_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Create secure connection
            context = ssl.create_default_context()
            
            with smtplib.SMTP(EmailService.SMTP_HOST, EmailService.SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(EmailService.SMTP_USER, EmailService.SMTP_PASSWORD)
                server.sendmail(EmailService.FROM_EMAIL, to_email, message.as_string())
            
            print(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def _render_template(template_str: str, **kwargs) -> str:
        """Render Jinja2 template with variables."""
        template = Template(template_str)
        return template.render(**kwargs)
    
    # ============================
    # NOTIFICATION METHODS
    # ============================
    
    @staticmethod
    async def send_study_reminder(
        user_id: ObjectId,
        custom_message: Optional[str] = None
    ) -> bool:
        """Send study reminder email to user."""
        users_col = db.users()
        user = await users_col.find_one({"_id": user_id})
        
        if not user:
            return False
        
        # Check if notifications enabled
        prefs = user.get("preferences", {})
        notification_prefs = prefs.get("notifications", {})
        
        if not notification_prefs.get("email_enabled", True):
            return False
        
        if not notification_prefs.get("study_reminders", True):
            return False
        
        # Get user's subjects
        subjects_col = db.subjects()
        user_subjects = await subjects_col.find({"user_id": user_id}).to_list(10)
        
        subjects_data = []
        for s in user_subjects:
            # Calculate progress (simplified)
            progress = 0
            if s.get("status") == "planned":
                progress = 50  # Has a plan
            subjects_data.append({
                "name": s.get("subject_name", "Unknown"),
                "progress": progress
            })
        
        # Get streak
        streak = user.get("learning_profile", {}).get("current_streak", 0)
        
        # Render template
        message = custom_message or "It's time for your daily study session! Your goals are waiting for you."
        
        html_content = EmailService._render_template(
            EmailService.STUDY_REMINDER_TEMPLATE,
            user_name=user.get("name", "Student"),
            message=message,
            subjects=subjects_data[:5],  # Max 5 subjects
            streak=streak,
            app_url="http://localhost:3000/dashboard"
        )
        
        return EmailService._send_email(
            to_email=user.get("email"),
            subject="📚 AgentED: Time to Study!",
            html_content=html_content
        )
    
    @staticmethod
    async def send_streak_alert(user_id: ObjectId) -> bool:
        """Send streak at risk alert."""
        users_col = db.users()
        user = await users_col.find_one({"_id": user_id})
        
        if not user:
            return False
        
        # Check if notifications enabled
        prefs = user.get("preferences", {})
        notification_prefs = prefs.get("notifications", {})
        
        if not notification_prefs.get("email_enabled", True):
            return False
        
        if not notification_prefs.get("streak_alerts", True):
            return False
        
        streak = user.get("learning_profile", {}).get("current_streak", 0)
        
        if streak < 1:
            return False  # No streak to protect
        
        html_content = EmailService._render_template(
            EmailService.STREAK_ALERT_TEMPLATE,
            user_name=user.get("name", "Student"),
            streak=streak,
            app_url="http://localhost:3000/dashboard"
        )
        
        return EmailService._send_email(
            to_email=user.get("email"),
            subject=f"🔥 AgentED: Your {streak}-day streak is at risk!",
            html_content=html_content
        )
    
    @staticmethod
    async def send_weekly_summary(user_id: ObjectId) -> bool:
        """Send weekly progress summary email."""
        users_col = db.users()
        user = await users_col.find_one({"_id": user_id})
        
        if not user:
            return False
        
        # Check if notifications enabled
        prefs = user.get("preferences", {})
        notification_prefs = prefs.get("notifications", {})
        
        if not notification_prefs.get("email_enabled", True):
            return False
        
        if not notification_prefs.get("weekly_summary", True):
            return False
        
        # Calculate week dates
        today = datetime.utcnow()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Get study hours for the week
        sessions_col = db.sessions()
        week_sessions = await sessions_col.find({
            "user_id": user_id,
            "created_at": {"$gte": week_start}
        }).to_list(100)
        
        total_hours = 0
        for session in week_sessions:
            if session.get("ended_at"):
                duration = (session["ended_at"] - session["created_at"]).total_seconds() / 3600
                total_hours += min(duration, 12)  # Cap at 12 hours
        
        # Get quizzes for the week
        quiz_col = db.quizzes()
        week_quizzes = await quiz_col.find({
            "user_id": user_id,
            "created_at": {"$gte": week_start}
        }).to_list(100)
        
        # Calculate average score
        scores = [q.get("score", 0) for q in week_quizzes if q.get("score") is not None]
        avg_score = round(sum(scores) / len(scores)) if scores else 0
        
        # Generate achievements
        achievements = []
        if total_hours >= 10:
            achievements.append("📖 Studied for 10+ hours this week!")
        if len(week_quizzes) >= 5:
            achievements.append("🎯 Completed 5+ quizzes!")
        if avg_score >= 80:
            achievements.append("🌟 Averaged 80%+ on quizzes!")
        
        html_content = EmailService._render_template(
            EmailService.WEEKLY_SUMMARY_TEMPLATE,
            user_name=user.get("name", "Student"),
            week_start=week_start.strftime("%b %d"),
            week_end=week_end.strftime("%b %d"),
            study_hours=round(total_hours, 1),
            quizzes_completed=len(week_quizzes),
            avg_score=avg_score,
            achievements=achievements,
            app_url="http://localhost:3000/analytics"
        )
        
        return EmailService._send_email(
            to_email=user.get("email"),
            subject="📊 AgentED: Your Weekly Learning Summary",
            html_content=html_content
        )
    
    # ============================
    # SCHEDULER METHODS
    # ============================
    
    @staticmethod
    async def process_daily_reminders():
        """
        Process and send daily study reminders.
        Call this from a scheduler (cron job, Celery, APScheduler, etc.)
        """
        users_col = db.users()
        
        # Find users with reminders enabled and reminder time set
        users = await users_col.find({
            "preferences.notifications.email_enabled": True,
            "preferences.notifications.study_reminders": True
        }).to_list(1000)
        
        current_hour = datetime.utcnow().hour
        sent_count = 0
        
        for user in users:
            prefs = user.get("preferences", {}).get("notifications", {})
            reminder_hour = prefs.get("reminder_hour", 9)  # Default 9 AM
            
            # Only send if it's the user's reminder hour
            if current_hour == reminder_hour:
                success = await EmailService.send_study_reminder(user["_id"])
                if success:
                    sent_count += 1
        
        print(f"📧 Sent {sent_count} daily reminders")
        return sent_count
    
    @staticmethod
    async def process_streak_alerts():
        """
        Check for users who haven't studied today but have streaks.
        Send alerts in the evening.
        """
        users_col = db.users()
        sessions_col = db.sessions()
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Find users with streaks
        users = await users_col.find({
            "learning_profile.current_streak": {"$gt": 0},
            "preferences.notifications.streak_alerts": True
        }).to_list(1000)
        
        sent_count = 0
        
        for user in users:
            # Check if user studied today
            today_session = await sessions_col.find_one({
                "user_id": user["_id"],
                "created_at": {"$gte": today_start}
            })
            
            if not today_session:
                # User hasn't studied today - send alert
                success = await EmailService.send_streak_alert(user["_id"])
                if success:
                    sent_count += 1
        
        print(f"🔥 Sent {sent_count} streak alerts")
        return sent_count
    
    @staticmethod
    async def process_weekly_summaries():
        """
        Send weekly summaries on Sundays.
        """
        if datetime.utcnow().weekday() != 6:  # Sunday = 6
            return 0
        
        users_col = db.users()
        
        users = await users_col.find({
            "preferences.notifications.weekly_summary": True
        }).to_list(1000)
        
        sent_count = 0
        
        for user in users:
            success = await EmailService.send_weekly_summary(user["_id"])
            if success:
                sent_count += 1
        
        print(f"📊 Sent {sent_count} weekly summaries")
        return sent_count
