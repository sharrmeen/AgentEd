import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING

# ========================
# MongoDB Configuration
# ========================

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "agented_db")


# ========================
# Motor Client (Async, Singleton)
# ========================

class Database:
    """
    Async MongoDB client manager using Motor.

    Collection Ownership:
    - Subject Agent: subjects, syllabus
    - Planner Agent: planner_state
    - Study Agent: study_sessions, chats
    - Resource Agent: chat_memory
    - Feedback Agent: feedback_reports
    - Quiz Agent: quizzes
    """

    client: AsyncIOMotorClient = None
    db = None

    async def connect(self):
        # Skip if already connected (e.g., by test fixtures)
        if self.db is not None:
            print("✅ MongoDB already connected (skipping)")
            return
        try:
            self.client = AsyncIOMotorClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[DB_NAME]
            await self.client.admin.command("ping")
            print("Connected to MongoDB")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise

    async def close(self):
        if self.client:
            self.client.close()
            print("❌ MongoDB connection closed")

    def get_db(self):
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db

    # ========================
    # Collection Handles
    # ========================

    def users(self):
        return self.db["users"]

    def subjects(self):
        return self.db["subjects"]

    def syllabus(self):
        return self.db["syllabus"]

    def study_sessions(self):
        return self.db["study_sessions"]

    def chats(self):
        return self.db["chats"]

    def chat_memory(self):
        return self.db["chat_memory"]

    def planner_state(self):
        return self.db["planner_state"]

    def feedback_reports(self):
        return self.db["feedback_reports"]

    def quizzes(self):
        return self.db["quizzes"]
    
    def notes(self):
        """Collection for note metadata."""
        return self.db["notes"]
    
    def quiz_results(self):
        """Collection for quiz attempt results."""
        return self.db["quiz_results"]

    async def init_indexes(self):
        """
        Create indexes for performance and data integrity.
        Call once on application startup.
        """
        # Skip if database not connected
        if self.db is None:
            print("⚠️ Database not connected, skipping index initialization")
            return
        await init_indexes()


db = Database()


# ========================
# Index Initialization
# ========================

# Add this to database.py init_indexes() function

async def init_indexes():
    """
    Create indexes for performance and data integrity.
    Call once on application startup.
    """
    dbi = db.get_db()

    # ---------- users ----------
    await dbi["users"].create_index(
        [("email", ASCENDING)],
        unique=True,
        name="unique_user_email"
    )

    # ---------- subjects ----------
    await dbi["subjects"].create_index(
        [("user_id", ASCENDING), ("subject_name", ASCENDING)],
        unique=True,
        name="unique_user_subject"
    )

    await dbi["subjects"].create_index(
        [("status", ASCENDING)],
        name="subject_status"
    )

    # ---------- syllabus ----------
    # CHANGED: Index on subject_id instead of subject_name
    await dbi["syllabus"].create_index(
        [("subject_id", ASCENDING)],
        unique=True,
        name="one_syllabus_per_subject"
    )
    
    await dbi["syllabus"].create_index(
        [("user_id", ASCENDING)],
        name="syllabus_user_lookup"
    )

    # ---------- study_sessions ----------
    await dbi["study_sessions"].create_index(
        [
            ("user_id", ASCENDING),
            ("subject_id", ASCENDING),
            ("chapter_number", ASCENDING),
        ],
        unique=True,
        name="unique_chapter_session"
    )

    await dbi["study_sessions"].create_index(
        [("user_id", ASCENDING), ("status", ASCENDING)],
        name="user_session_status"
    )
    
    await dbi["study_sessions"].create_index(
        [("subject_id", ASCENDING)],
        name="sessions_by_subject"
    )

    # ---------- chats ----------
    await dbi["chats"].create_index(
        [("session_id", ASCENDING)],
        unique=True,
        name="one_chat_per_session"
    )
    
    await dbi["chats"].create_index(
        [("subject_id", ASCENDING)],
        name="chats_by_subject"
    )

    # ---------- chat_memory ----------
    await dbi["chat_memory"].create_index(
        [
            ("session_id", ASCENDING),
            ("question_hash", ASCENDING)
        ],
        name="session_question_cache"
    )

    await dbi["chat_memory"].create_index(
        [
            ("subject_id", ASCENDING),
            ("intent_tag", ASCENDING)
        ],
        name="subject_intent_cache"
    )

    await dbi["chat_memory"].create_index(
        [("created_at", DESCENDING)],
        name="recent_memory"
    )

    # ---------- planner_state ----------
    await dbi["planner_state"].create_index(
        [("subject_id", ASCENDING)],
        unique=True,
        name="one_planner_state_per_subject"
    )

    await dbi["planner_state"].create_index(
        [("user_id", ASCENDING)],
        name="planner_user_lookup"
    )

    # ---------- notes ----------
    await dbi["notes"].create_index(
        [("user_id", ASCENDING), ("subject_id", ASCENDING)],
        name="notes_by_subject"
    )
    
    await dbi["notes"].create_index(
        [("user_id", ASCENDING), ("subject_id", ASCENDING), ("chapter", ASCENDING)],
        name="notes_by_chapter"
    )

    await dbi["notes"].create_index(
    [("subject_id", ASCENDING), ("chapter", ASCENDING)],
    name="notes_by_subject_chapter"
    )
    # ---------- feedback_reports ----------
    await dbi["feedback_reports"].create_index(
        [("session_id", ASCENDING)],
        name="feedback_by_session"
    )

    await dbi["feedback_reports"].create_index(
        [("created_at", DESCENDING)],
        name="recent_feedback"
    )

    # ---------- quizzes ----------
    await dbi["quizzes"].create_index(
        [("session_id", ASCENDING)],
        name="quiz_by_session"
    )

    await dbi["quizzes"].create_index(
        [("quiz_type", ASCENDING)],
        name="quiz_type_filter"
    )
    
    # ---------- quiz_results ----------
    await dbi["quiz_results"].create_index(
        [("user_id", ASCENDING), ("subject_id", ASCENDING)],
        name="quiz_results_by_subject"
    )
    
    await dbi["quiz_results"].create_index(
        [("user_id", ASCENDING), ("quiz_id", ASCENDING)],
        name="quiz_results_by_quiz"
    )
    
    await dbi["quiz_results"].create_index(
        [("completed_at", DESCENDING)],
        name="quiz_results_recent"
    )

    print("MongoDB indexes initialized successfully")


# ========================
# Health Check
# ========================

async def mongo_health_check() -> bool:
    if not db.client:
        return False
    try:
        await db.client.admin.command("ping")
        return True
    except Exception:
        return False