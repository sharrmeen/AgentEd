# backend/app/services/user_service.py

"""
UserService - User management and learning profile.

Responsibilities:
- User registration and authentication
- Learning profile management
- Performance tracking
- Preference management
"""

from datetime import datetime
from bson import ObjectId
from typing import Optional
from passlib.context import CryptContext

from app.core.database import db
from app.core.models.user import (
    UserCreate, UserInDB, UserPublic, UserUpdate,
    LearningProfile, SubjectProfile
)


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """User management service."""
    
    # ============================
    # AUTHENTICATION
    # ============================
    
    @staticmethod
    async def create_user(user_data: UserCreate) -> UserInDB:
        """Register new user."""
        users_col = db.users()
        
        # Check if email exists
        existing = await users_col.find_one({"email": user_data.email})
        if existing:
            raise ValueError("Email already registered")
        
        # Hash password
        password_hash = pwd_context.hash(user_data.password)
        
        # Create user document
        user_doc = {
            "name": user_data.name,
            "email": user_data.email,
            "password_hash": password_hash,
            "role": "student",
            "is_active": True,
            "learning_profile": LearningProfile().model_dump(),
            "preferences": {},
            "created_at": datetime.utcnow(),
            "last_login": None,
            "updated_at": datetime.utcnow()
        }
        
        result = await users_col.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        
        return UserInDB(**user_doc)
    
    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[UserInDB]:
        """Get user by email."""
        users_col = db.users()
        doc = await users_col.find_one({"email": email})
        return UserInDB(**doc) if doc else None
    
    @staticmethod
    async def get_user_by_id(user_id: ObjectId) -> Optional[UserInDB]:
        """Get user by ID."""
        users_col = db.users()
        doc = await users_col.find_one({"_id": user_id})
        return UserInDB(**doc) if doc else None
    
    # ============================
    # LEARNING PROFILE
    # ============================
    
    @staticmethod
    async def get_learning_profile(user_id: ObjectId) -> LearningProfile:
        """Get user's learning profile."""
        user = await UserService.get_user_by_id(user_id)
        return user.learning_profile if user else LearningProfile()
    
    @staticmethod
    async def update_learning_profile(
        *,
        user_id: ObjectId,
        profile_update: dict
    ):
        """Update learning profile."""
        users_col = db.users()
        
        await users_col.update_one(
            {"_id": user_id},
            {
                "$set": {
                    f"learning_profile.{key}": value
                    for key, value in profile_update.items()
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    
    # ============================
    # SUBJECT PROFILE
    # ============================
    
    @staticmethod
    async def update_subject_profile(
        *,
        user_id: ObjectId,
        subject_id: str,
        updates: dict
    ):
        """
        Update per-subject learning profile.
        
        Called by FeedbackService after quiz completion.
        """
        users_col = db.users()
        
        await users_col.update_one(
            {"_id": user_id},
            {
                "$set": {
                    f"learning_profile.subjects.{subject_id}.{key}": value
                    for key, value in updates.items()
                }
            }
        )