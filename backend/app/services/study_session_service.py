# backend/app/services/study_session_service.py

from datetime import datetime
from bson import ObjectId
from typing import Optional

from app.core.database import db
from app.core.models.session import StudySession
from app.services.subject_service import SubjectService


class StudySessionService:
    """
    Handles chapter-level study sessions.
    
    STRICT VALIDATION:
    - Subject must exist
    - Syllabus must be uploaded
    - Study plan must be generated
    
    One session = one chapter.
    """

    @staticmethod
    async def create_study_session(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        chapter_number: int,
    ) -> StudySession:
        """
        Create or retrieve study session for a chapter.
        
        Preconditions (ENFORCED):
        1. ✅ Subject exists
        2. ✅ Syllabus uploaded
        3. ✅ Study plan generated
        
        Args:
            user_id: Owner
            subject_id: Parent subject
            chapter_number: Chapter to study (1-indexed)
            
        Returns:
            StudySession (new or existing)
            
        Raises:
            ValueError: If preconditions not met
        """
        sessions_col = db.study_sessions()
        chats_col = db.chats()
        planner_col = db.planner_state()
        
        # -----------------------------
        # 1️⃣ Validate Subject Exists
        # -----------------------------
        subject = await SubjectService.get_subject_by_id(
            user_id=user_id,
            subject_id=subject_id
        )
        
        if not subject:
            raise ValueError("Subject not found")
        
        # -----------------------------
        # 2️⃣ CRITICAL: Validate Syllabus
        # -----------------------------
        if not subject.syllabus_id:
            raise ValueError(
                "❌ Cannot start studying without syllabus.\n"
                "Please upload syllabus first."
            )
        
        # -----------------------------
        # 3️⃣ CRITICAL: Validate Plan
        # -----------------------------
        planner = await planner_col.find_one({
            "user_id": user_id,
            "subject_id": subject_id
        })
        
        if not planner:
            raise ValueError(
                "❌ Study plan not generated.\n"
                "Click 'Generate Plan' before starting."
            )
        
        # -----------------------------
        # 4️⃣ Validate Chapter Number
        # -----------------------------
        total_chapters = planner.get("total_chapters", 0)
        
        if chapter_number < 1 or chapter_number > total_chapters:
            raise ValueError(
                f"Invalid chapter number. Plan has {total_chapters} chapters."
            )
        
        # Get chapter title from plan
        chapters = subject.plan.get("chapters", [])
        chapter_info = next(
            (ch for ch in chapters if ch.get("chapter_number") == chapter_number),
            None
        )
        
        if not chapter_info:
            raise ValueError(f"Chapter {chapter_number} not found in study plan")
        
        chapter_title = chapter_info.get("chapter_title", f"Chapter {chapter_number}")
        
        # -----------------------------
        # 5️⃣ Check Existing Session
        # -----------------------------
        existing = await sessions_col.find_one({
            "user_id": user_id,
            "subject_id": subject_id,
            "chapter_number": chapter_number
        })
        
        if existing:
            return StudySession(**existing)
        
        # -----------------------------
        # 6️⃣ Create Study Session
        # -----------------------------
        session_doc = {
            "user_id": user_id,
            "subject_id": subject_id,
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "notes_uploaded": False,
            "status": "active",
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow(),
        }
        
        session_result = await sessions_col.insert_one(session_doc)
        session_id = session_result.inserted_id
        
        # -----------------------------
        # 7️⃣ Create Chat Container
        # -----------------------------
        chat_doc = {
            "user_id": user_id,
            "session_id": session_id,
            "subject_id": subject_id,
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "created_at": datetime.utcnow()
        }
        
        chat_result = await chats_col.insert_one(chat_doc)
        chat_id = chat_result.inserted_id
        
        # Link chat to session
        await sessions_col.update_one(
            {"_id": session_id},
            {"$set": {"chat_id": chat_id}}
        )
        
        # -----------------------------
        # 8️⃣ Update Subject Status
        # -----------------------------
        await SubjectService.mark_in_progress(
            user_id=user_id,
            subject_id=subject_id
        )
        
        session_doc["_id"] = session_id
        session_doc["chat_id"] = chat_id
        
        return StudySession(**session_doc)
    
    # ============================
    # GET SESSION
    # ============================
    
    @staticmethod
    async def get_session_by_id(
        *,
        user_id: ObjectId,
        session_id: ObjectId
    ) -> Optional[StudySession]:
        """
        Retrieve session by ID (ownership enforced).
        """
        sessions_col = db.study_sessions()
        
        doc = await sessions_col.find_one({
            "_id": session_id,
            "user_id": user_id
        })
        
        return StudySession(**doc) if doc else None
    
    @staticmethod
    async def list_subject_sessions(
        *,
        user_id: ObjectId,
        subject_id: ObjectId
    ) -> list[StudySession]:
        """
        List all sessions for a subject (ordered by chapter).
        """
        sessions_col = db.study_sessions()
        
        cursor = sessions_col.find({
            "user_id": user_id,
            "subject_id": subject_id
        }).sort("chapter_number", 1)
        
        docs = await cursor.to_list(None)
        return [StudySession(**doc) for doc in docs]
    
    # ============================
    # UPDATE SESSION
    # ============================
    
    @staticmethod
    async def mark_notes_uploaded(
        *,
        user_id: ObjectId,
        session_id: ObjectId
    ) -> StudySession:
        """
        Mark that notes have been uploaded for this session.
        """
        sessions_col = db.study_sessions()
        
        result = await sessions_col.update_one(
            {
                "_id": session_id,
                "user_id": user_id
            },
            {
                "$set": {
                    "notes_uploaded": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise ValueError("Session not found")
        
        updated = await sessions_col.find_one({"_id": session_id})
        return StudySession(**updated)
    
    @staticmethod
    async def end_session(
        *,
        user_id: ObjectId,
        session_id: ObjectId
    ) -> StudySession:
        """
        Mark session as completed.
        """
        sessions_col = db.study_sessions()
        
        result = await sessions_col.update_one(
            {
                "_id": session_id,
                "user_id": user_id
            },
            {
                "$set": {
                    "status": "completed",
                    "ended_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise ValueError("Session not found")
        
        updated = await sessions_col.find_one({"_id": session_id})
        return StudySession(**updated)