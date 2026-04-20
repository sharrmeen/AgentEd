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
import re
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError

from app.core.database import db
from app.core.config import settings
from app.core.models.user import (
    UserCreate, UserInDB, UserPublic, UserUpdate,
    LearningProfile, SubjectProfile
)


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """User management service."""

    @staticmethod
    async def _validate_class_exists(class_id: str) -> None:
        """Ensure provided class_id points to an existing class document."""
        normalized_class_id = class_id.strip()
        if not ObjectId.is_valid(normalized_class_id):
            raise ValueError("Invalid class ID format")

        class_doc = await db.classes().find_one({"_id": ObjectId(normalized_class_id)})
        if not class_doc:
            raise ValueError("Class not found")
    
    # ============================
    # AUTHENTICATION
    # ============================
    
    @staticmethod
    async def create_user(user_data: UserCreate) -> UserInDB:
        """Create user account."""
        users_col = db.users()
        
        # Check if username exists
        existing = await users_col.find_one({"username": user_data.username})
        if existing:
            raise ValueError("Username already exists")

        normalized_email = user_data.email.strip() if user_data.email else None

        # Check email uniqueness only when provided
        if normalized_email:
            email_existing = await users_col.find_one({"email": normalized_email})
            if email_existing:
                raise ValueError("Email already registered")

        normalized_role = (user_data.role or "student").strip().lower()
        if normalized_role not in {"student", "teacher", "admin"}:
            raise ValueError("Invalid role")

        normalized_class_id = user_data.class_id.strip() if user_data.class_id else None

        if normalized_role == "teacher":
            normalized_class_id = None
        elif normalized_role == "student" and not normalized_class_id:
            normalized_class_id = None

        if normalized_role == "student" and normalized_class_id:
            await UserService._validate_class_exists(normalized_class_id)
        
        # Hash password
        password_hash = pwd_context.hash(user_data.password)
        
        # Create user document
        user_doc = {
            "name": user_data.name,
            "username": user_data.username,
            "password_hash": password_hash,
            "must_change_password": user_data.must_change_password,
            "role": normalized_role,
            "class_id": normalized_class_id,
            "is_active": True,
            "learning_profile": LearningProfile().model_dump(),
            "preferences": {},
            "created_at": datetime.utcnow(),
            "last_login": None,
            "updated_at": datetime.utcnow()
        }

        if normalized_email:
            user_doc["email"] = normalized_email
        
        try:
            result = await users_col.insert_one(user_doc)
        except DuplicateKeyError as exc:
            if "username" in str(exc):
                raise ValueError("Username already exists")
            if "email" in str(exc):
                raise ValueError("Email already registered")
            raise
        user_doc["_id"] = result.inserted_id
        
        return UserInDB(**user_doc)
    
    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    async def get_user_by_username(username: str) -> Optional[UserInDB]:
        """Get user by username."""
        users_col = db.users()
        doc = await users_col.find_one({"username": username})
        return UserInDB(**doc) if doc else None

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

    @staticmethod
    async def ensure_default_admin() -> UserInDB:
        """Ensure a default admin account exists."""
        existing_admin = await UserService.get_user_by_username(settings.DEFAULT_ADMIN_USERNAME)
        if existing_admin:
            return existing_admin

        return await UserService.create_user(
            UserCreate(
                name="Administrator",
                username=settings.DEFAULT_ADMIN_USERNAME,
                email=None,
                role="admin",
                password=settings.DEFAULT_ADMIN_PASSWORD,
                must_change_password=True,
            )
        )

    @staticmethod
    async def create_user_by_admin(
        *,
        name: str,
        username: str,
        password: str,
        role: str,
        class_id: Optional[str] = None,
        email: Optional[str] = None,
        must_change_password: bool = True,
    ) -> UserInDB:
        """Create student/teacher user from admin endpoint."""
        normalized_role = (role or "").strip().lower()
        if normalized_role not in {"student", "teacher"}:
            raise ValueError("Admin can only create student or teacher accounts")

        return await UserService.create_user(
            UserCreate(
                name=name,
                username=username,
                email=email,
                role=normalized_role,
                class_id=class_id,
                password=password,
                must_change_password=must_change_password,
            )
        )

    @staticmethod
    async def update_password(
        *,
        user_id: ObjectId,
        current_password: str,
        new_password: str,
        email: Optional[str] = None,
    ) -> None:
        """Change current user's password and clear first-login requirement.

        If user must change password on first login, email is mandatory.
        """
        users_col = db.users()
        user = await UserService.get_user_by_id(user_id)

        if not user:
            raise ValueError("User not found")

        if not await UserService.verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        normalized_email = email.strip() if email else None

        if user.must_change_password and not normalized_email:
            raise ValueError("Email is required on first login")

        if normalized_email:
            existing_email_owner = await users_col.find_one({
                "email": normalized_email,
                "_id": {"$ne": user_id}
            })
            if existing_email_owner:
                raise ValueError("Email already registered")

        new_password_hash = pwd_context.hash(new_password)
        update_set = {
            "password_hash": new_password_hash,
            "must_change_password": False,
            "updated_at": datetime.utcnow(),
        }

        if normalized_email:
            update_set["email"] = normalized_email

        await users_col.update_one(
            {"_id": user_id},
            {
                "$set": update_set
            },
        )

    @staticmethod
    async def update_profile(
        *,
        user_id: ObjectId,
        name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> UserInDB:
        """Update current user's basic profile fields."""
        users_col = db.users()
        existing_user = await UserService.get_user_by_id(user_id)
        if not existing_user:
            raise ValueError("User not found")

        updates: dict = {"updated_at": datetime.utcnow()}

        if name is not None:
            normalized_name = name.strip()
            if len(normalized_name) < 2:
                raise ValueError("Name must be at least 2 characters")
            updates["name"] = normalized_name

        if email is not None:
            normalized_email = email.strip()
            if normalized_email:
                email_owner = await users_col.find_one({
                    "email": normalized_email,
                    "_id": {"$ne": user_id},
                })
                if email_owner:
                    raise ValueError("Email already registered")
                updates["email"] = normalized_email
            else:
                pass

        if len(updates) == 1 and email is None:
            return existing_user

        update_query = {"$set": updates}
        if email is not None and not email.strip():
            update_query["$unset"] = {"email": ""}

        await users_col.update_one(
            {"_id": user_id},
            update_query,
        )

        updated_user = await UserService.get_user_by_id(user_id)
        return updated_user

    @staticmethod
    async def mark_last_login(user_id: ObjectId) -> None:
        """Update last login timestamp."""
        users_col = db.users()
        await users_col.update_one(
            {"_id": user_id},
            {"$set": {"last_login": datetime.utcnow(), "updated_at": datetime.utcnow()}},
        )

    @staticmethod
    async def assign_class_to_student(*, user_id: ObjectId, class_id: Optional[str]) -> UserInDB:
        """Assign or clear class_id for a student user."""
        users_col = db.users()

        user = await UserService.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if user.role != "student":
            raise ValueError("Class assignment is only allowed for students")

        normalized_class_id = class_id.strip() if class_id else None

        if normalized_class_id:
            await UserService._validate_class_exists(normalized_class_id)

        await users_col.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "class_id": normalized_class_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        updated_user = await UserService.get_user_by_id(user_id)
        return updated_user

    @staticmethod
    async def list_users(
        *,
        skip: int = 0,
        limit: int = 20,
        role: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[list[UserInDB], int]:
        """List users for admin views with optional filtering."""
        users_col = db.users()

        query: dict = {}
        if role:
            query["role"] = role.strip().lower()

        if search:
            search_regex = re.escape(search.strip())
            query["$or"] = [
                {"name": {"$regex": search_regex, "$options": "i"}},
                {"username": {"$regex": search_regex, "$options": "i"}},
                {"email": {"$regex": search_regex, "$options": "i"}},
            ]

        total = await users_col.count_documents(query)
        cursor = users_col.find(query).sort("created_at", -1).skip(max(skip, 0)).limit(min(max(limit, 1), 200))
        docs = await cursor.to_list(None)

        return [UserInDB(**doc) for doc in docs], total
    
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
                    **{
                        f"learning_profile.{key}": value
                        for key, value in profile_update.items()
                    },
                    "updated_at": datetime.utcnow(),
                },
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