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
        # 5️⃣ Create or Update Session (Atomically)
        # Using upsert to handle concurrent requests
        # This prevents E11000 duplicate key errors
        # -----------------------------
        filter_query = {
            "user_id": user_id,
            "subject_id": subject_id,
            "chapter_number": chapter_number
        }
        
        # Check if session already exists
        existing_session = await sessions_col.find_one(filter_query)
        
        if existing_session:
            # Session exists - just return it
            session_id = existing_session["_id"]
        else:
            # Create new session
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
            
            try:
                session_result = await sessions_col.insert_one(session_doc)
                session_id = session_result.inserted_id
            except Exception as e:
                # Handle race condition - another request created it
                if "duplicate" in str(e).lower():
                    existing_session = await sessions_col.find_one(filter_query)
                    if existing_session:
                        session_id = existing_session["_id"]
                    else:
                        raise
                else:
                    raise
        
        # If session doesn't have a chat yet, create one
        session_record = await sessions_col.find_one({"_id": session_id})
        
        print(f"📋 Session record after creation: {session_record}", flush=True)
        print(f"   Has chat_id: {bool(session_record.get('chat_id'))}", flush=True)
        
        if not session_record.get("chat_id"):
            print(f"🔍 Checking for existing chat with session_id: {session_id}", flush=True)
            # Check if chat already exists for this session
            existing_chat = await chats_col.find_one({"session_id": session_id})
            
            if existing_chat:
                # Use existing chat
                chat_id = existing_chat["_id"]
                print(f"   ♻️ Reusing existing chat: {chat_id}", flush=True)
            else:
                # Create new Chat Container
                chat_doc = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "subject_id": subject_id,
                    "chapter_number": chapter_number,
                    "chapter_title": chapter_title,
                    "created_at": datetime.utcnow()
                }
                
                print(f"📝 Creating new chat with doc: {chat_doc}", flush=True)
                try:
                    chat_result = await chats_col.insert_one(chat_doc)
                    chat_id = chat_result.inserted_id
                    print(f"✅ Created chat: {chat_id}", flush=True)
                except Exception as e:
                    print(f"❌ Error creating chat: {e}", flush=True)
                    raise
            
            # Link chat to session (whether new or existing)
            try:
                update_result = await sessions_col.update_one(
                    {"_id": session_id},
                    {"$set": {"chat_id": chat_id}}
                )
                print(f"   ✅ Updated session with chat_id: {chat_id} ({update_result.modified_count} documents modified)", flush=True)
            except Exception as e:
                print(f"❌ Error updating session with chat_id: {e}", flush=True)
                raise
        
        # Fetch final session record (with all fields including chat_id)
        final_session = await sessions_col.find_one({"_id": session_id})
        print(f"📋 Final session: {final_session}", flush=True)
        print(f"   Final chat_id: {final_session.get('chat_id')}", flush=True)
        
        # Update Subject Status
        await SubjectService.mark_in_progress(
            user_id=user_id,
            subject_id=subject_id
        )
        
        return StudySession(**final_session)
    
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