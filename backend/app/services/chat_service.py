# backend/app/services/chat_service.py

from datetime import datetime
from bson import ObjectId
from typing import Optional

from app.core.database import db
from app.core.models.chat import Chat
from app.core.models.session import StudySession


class ChatService:
    """
    Chat service layer.

    One chat per study session.
    Acts as the conversation container.
    """

    # ============================
    # Get or Create Chat
    # ============================

    @staticmethod
    async def get_or_create_chat(
        *,
        session: StudySession,
    ) -> Chat:
        """
        Fetch existing chat or create one for a study session.
        """
        chats_col = db.chats()
        sessions_col = db.study_sessions()

        # 1️⃣ Return existing chat if already linked
        if session.chat_id:
            existing = await chats_col.find_one(
                {"_id": session.chat_id}
            )
            if existing:
                return Chat(**existing)

        # 2️⃣ Create new chat
        chat_doc = {
            "user_id": session.user_id,
            "session_id": session.id,
            "subject_id": session.subject_id,  # ← FIXED
            "chapter_number": session.chapter_number,  # ← FIXED
            "chapter_title": session.chapter_title,  # ← ADDED
            "created_at": datetime.utcnow(),
        }

        result = await chats_col.insert_one(chat_doc)
        chat_id = result.inserted_id

        # 3️⃣ Link chat to session
        await sessions_col.update_one(
            {"_id": session.id},
            {
                "$set": {
                    "chat_id": chat_id,
                    "last_active": datetime.utcnow()
                }
            }
        )

        chat_doc["_id"] = chat_id
        return Chat(**chat_doc)

    # ============================
    # Fetch Chat
    # ============================

    @staticmethod
    async def get_chat_by_session(
        *,
        user_id: ObjectId,
        session_id: ObjectId,
    ) -> Optional[Chat]:
        """
        Retrieve chat by session (ownership enforced).
        """
        chats_col = db.chats()

        doc = await chats_col.find_one({
            "session_id": session_id,
            "user_id": user_id
        })

        return Chat(**doc) if doc else None
    
    @staticmethod
    async def get_chat_by_id(
        *,
        user_id: ObjectId,
        chat_id: ObjectId,
    ) -> Optional[Chat]:
        """
        Retrieve chat by ID (ownership enforced).
        """
        chats_col = db.chats()

        doc = await chats_col.find_one({
            "_id": chat_id,
            "user_id": user_id
        })

        return Chat(**doc) if doc else None

    # ============================
    # Activity Tracking
    # ============================

    @staticmethod
    async def touch_chat(
        *,
        chat_id: ObjectId,
    ) -> None:
        """
        Update last_active timestamp on session.
        """
        chats_col = db.chats()
        sessions_col = db.study_sessions()

        chat = await chats_col.find_one({"_id": chat_id})
        if not chat:
            return

        await sessions_col.update_one(
            {"_id": chat["session_id"]},
            {"$set": {"last_active": datetime.utcnow()}}
        )

    # ============================
    # Ownership Validation
    # ============================

    @staticmethod
    async def validate_chat_ownership(
        *,
        user_id: ObjectId,
        chat_id: ObjectId,
    ) -> Chat:
        """
        Ensure chat belongs to user.
        """
        chats_col = db.chats()

        chat = await chats_col.find_one({
            "_id": chat_id,
            "user_id": user_id
        })

        if not chat:
            raise PermissionError("Unauthorized chat access")

        return Chat(**chat)