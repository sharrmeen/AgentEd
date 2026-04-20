# backend/app/services/subject_service.py

from datetime import datetime
from bson import ObjectId
from typing import Optional, List, Dict, Tuple

from app.core.database import db
from app.core.models.subject import Subject


class SubjectService:
    """
    Subject service layer.
    
    Subject is the root container for:
    - Syllabus
    - Study Plan
    - Study Sessions
    - Progress Tracking
    
    Workflow:
    1. Create empty subject
    2. Upload syllabus (linked via SyllabusService)
    3. Generate plan (via PlannerService)
    4. Start studying (via StudySessionService)
    """

    # ============================
    # CREATE SUBJECT
    # ============================

    @staticmethod
    async def create_subject(
        *,
        user_id: ObjectId,
        subject_name: str,
        class_ids: Optional[List[str]] = None,
    ) -> Subject:
        """
        Step 1: Create empty subject.
        Syllabus can be uploaded later.
        
        Args:
            user_id: Owner
            subject_name: Display name (e.g., "Biology")
            class_ids: Optional list of class IDs assigned to
            
        Returns:
            Subject with status="created"
            
        Raises:
            ValueError: If subject name already exists for user
        """
        subjects_col = db.subjects()
        class_ids = class_ids or []
        
        # Validate unique subject name per user
        class_obj_ids = []
        for cid in class_ids:
            if not ObjectId.is_valid(cid):
                raise ValueError(f"Invalid class ID format: {cid}")
            class_obj_ids.append(ObjectId(cid))

        existing_query = {
            "user_id": user_id,
            "subject_name": subject_name,
        }

        existing = await subjects_col.find_one(existing_query)
        
        if existing:
            raise ValueError(
                f"Subject '{subject_name}' already exists. "
                "Choose a different name."
            )
        
        # Create subject
        subject_doc = {
            "user_id": user_id,
            "class_ids": class_obj_ids,
            "subject_name": subject_name,
            "syllabus_id": None,  # Empty until upload
            "status": "created",  # Lifecycle tracking
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        result = await subjects_col.insert_one(subject_doc)
        subject_doc["_id"] = result.inserted_id
        
        return Subject(**subject_doc)

    # ============================
    # LINK SYLLABUS (Internal)
    # ============================

    @staticmethod
    async def link_syllabus(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        syllabus_id: ObjectId,
    ) -> Subject:
        """
        Step 2: Link syllabus after upload.
        Called internally by SyllabusService.
        
        Updates:
        - subject.syllabus_id = syllabus_id
        - subject.status = "syllabus_uploaded"
        """
        subjects_col = db.subjects()
        
        result = await subjects_col.update_one(
            {
                "_id": subject_id,
                "user_id": user_id
            },
            {
                "$set": {
                    "syllabus_id": syllabus_id,
                    "status": "syllabus_uploaded",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise ValueError("Subject not found or unauthorized")
        
        updated = await subjects_col.find_one({"_id": subject_id})
        return Subject(**updated)



    # ============================
    # MARK AS IN PROGRESS
    # ============================

    @staticmethod
    async def mark_in_progress(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
    ) -> Subject:
        """
        Step 4: Mark subject as in_progress when first session starts.
        Called by StudySessionService.
        """
        subjects_col = db.subjects()
        
        result = await subjects_col.update_one(
            {
                "_id": subject_id,
                "user_id": user_id,
                "status": "planned"  # Only transition from planned
            },
            {
                "$set": {
                    "status": "in_progress",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            # Already in_progress or invalid state
            pass
        
        updated = await subjects_col.find_one({"_id": subject_id})
        return Subject(**updated)

    # ============================
    # GET SUBJECT
    # ============================

    @staticmethod
    async def _resolve_requester_context(
        *,
        user_id: ObjectId,
        requester_role: Optional[str] = None,
        requester_class_id: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Resolve requester role/class when not explicitly provided."""
        if requester_role is not None or requester_class_id is not None:
            normalized_role = requester_role.strip().lower() if isinstance(requester_role, str) else None
            normalized_class_id = requester_class_id.strip() if isinstance(requester_class_id, str) else requester_class_id
            return normalized_role, normalized_class_id

        user_doc = await db.users().find_one(
            {"_id": user_id},
            {"role": 1, "class_id": 1},
        )
        if not user_doc:
            return None, None

        resolved_role = user_doc.get("role")
        if isinstance(resolved_role, str):
            resolved_role = resolved_role.strip().lower()
        resolved_class_id = user_doc.get("class_id")
        if isinstance(resolved_class_id, str):
            resolved_class_id = resolved_class_id.strip()

        return resolved_role, resolved_class_id

    @staticmethod
    async def _resolve_class_teacher_id(class_id: Optional[str]) -> Optional[ObjectId]:
        """Resolve the teacher owner for a given class id."""
        if not class_id or not ObjectId.is_valid(class_id):
            return None

        class_doc = await db.classes().find_one(
            {"_id": ObjectId(class_id), "is_active": True},
            {"teacher_id": 1},
        )
        teacher_id = class_doc.get("teacher_id") if class_doc else None
        return teacher_id if isinstance(teacher_id, ObjectId) else None

    @staticmethod
    async def get_subject_by_id(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        requester_role: Optional[str] = None,
        requester_class_id: Optional[str] = None,
    ) -> Optional[Subject]:
        """
        Retrieve subject by ID.

        Access rules:
        - owner can always access
        - student can access subjects owned by their class teacher
        """
        subjects_col = db.subjects()

        role, class_id = await SubjectService._resolve_requester_context(
            user_id=user_id,
            requester_role=requester_role,
            requester_class_id=requester_class_id,
        )

        query: dict = {"_id": subject_id}
        if role == "student":
            class_obj_id = None
            if class_id and ObjectId.is_valid(class_id):
                class_obj_id = ObjectId(class_id)

            allowed_filters = [{"user_id": user_id}]
            if class_obj_id:
                allowed_filters.append({"class_ids": class_obj_id})

            query["$or"] = allowed_filters
        else:
            query["user_id"] = user_id

        doc = await subjects_col.find_one(query)
        
        return Subject(**doc) if doc else None

    @staticmethod
    async def get_subject_by_name(
        *,
        user_id: ObjectId,
        subject_name: str,
    ) -> Optional[Subject]:
        """
        Retrieve subject by name (ownership enforced).
        """
        subjects_col = db.subjects()
        
        doc = await subjects_col.find_one({
            "user_id": user_id,
            "subject_name": subject_name
        })
        
        return Subject(**doc) if doc else None

    # ============================
    # LIST SUBJECTS
    # ============================

    @staticmethod
    async def list_user_subjects(
        *,
        user_id: ObjectId,
        status: Optional[str] = None,
        requester_role: Optional[str] = None,
        requester_class_id: Optional[str] = None,
    ) -> List[Subject]:
        """
        List subjects visible to a user.

        Access rules:
        - owner always sees own subjects
        - student also sees subjects owned by their class teacher
        
        Args:
            user_id: User ID
            status: Filter by status (created, syllabus_uploaded, planned, in_progress, completed)
        """
        subjects_col = db.subjects()

        role, class_id = await SubjectService._resolve_requester_context(
            user_id=user_id,
            requester_role=requester_role,
            requester_class_id=requester_class_id,
        )

        query: dict = {}
        if role == "student":
            class_obj_id = None
            if class_id and ObjectId.is_valid(class_id):
                class_obj_id = ObjectId(class_id)

            allowed_filters = [{"user_id": user_id}]
            if class_obj_id:
                allowed_filters.append({"class_ids": class_obj_id})

            query["$or"] = allowed_filters
        else:
            query["user_id"] = user_id

        if status:
            query["status"] = status
        
        cursor = subjects_col.find(query).sort("created_at", -1)
        docs = await cursor.to_list(None)
        
        return [Subject(**doc) for doc in docs]

    # ============================
    # VALIDATION HELPERS
    # ============================

    @staticmethod
    async def validate_has_syllabus(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
    ) -> Subject:
        """
        Ensure subject has syllabus uploaded.
        
        Used by:
        - PlannerService (before generating plan)
        - StudySessionService (before creating session)
        
        Raises:
            ValueError: If syllabus not uploaded
        """
        subject = await SubjectService.get_subject_by_id(
            user_id=user_id,
            subject_id=subject_id
        )
        
        if not subject:
            raise ValueError("Subject not found")
        
        if not subject.syllabus_id:
            raise ValueError(
                "❌ Syllabus not uploaded. "
                "Upload syllabus before proceeding."
            )
        
        return subject

    @staticmethod
    async def validate_has_plan(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
    ) -> Subject:
        """
        Ensure subject has study plan generated.
        
        Used by:
        - StudySessionService (before creating session)
        
        Raises:
            ValueError: If plan not generated
        """
        subject = await SubjectService.get_subject_by_id(
            user_id=user_id,
            subject_id=subject_id
        )
        
        if not subject:
            raise ValueError("Subject not found")
        
        planner_doc = await db.planner_state().find_one(
            {"user_id": user_id, "subject_id": subject_id},
            {"_id": 1}
        )

        if not planner_doc:
            raise ValueError(
                "❌ Study plan not generated. "
                "Click 'Generate Plan' first."
            )
        
        return subject

    # ============================
    # STATUS MANAGEMENT
    # ============================

    @staticmethod
    async def update_status(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        status: str,
    ) -> Subject:
        """
        Manually update subject status.
        
        Valid statuses:
        - created
        - syllabus_uploaded
        - planned
        - in_progress
        - completed
        - archived
        """
        VALID_STATUSES = {
            "created", "syllabus_uploaded", "planned",
            "in_progress", "completed", "archived"
        }
        
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {VALID_STATUSES}")
        
        subjects_col = db.subjects()
        
        result = await subjects_col.update_one(
            {
                "_id": subject_id,
                "user_id": user_id
            },
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise ValueError("Subject not found or unauthorized")
        
        updated = await subjects_col.find_one({"_id": subject_id})
        return Subject(**updated)

    # ============================
    # DELETE (Cascading)
    # ============================

    @staticmethod
    async def delete_subject(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
    ) -> bool:
        """
        Delete subject and ALL related data.
        
        Cascading deletes:
        - Syllabus
        - PlannerState
        - StudySessions
        - Chats
        - ChatMemory
        - Notes metadata (files remain)
        
        Returns:
            True if deleted, False if not found
        """
        subjects_col = db.subjects()
        syllabus_col = db.syllabus()
        planner_col = db.planner_state()
        sessions_col = db.study_sessions()
        chats_col = db.chats()
        memory_col = db.chat_memory()
        notes_col = db.notes()
        
        # Verify ownership
        subject = await subjects_col.find_one({
            "_id": subject_id,
            "user_id": user_id
        })
        
        if not subject:
            return False
        
        # 1. Delete syllabus
        if subject.get("syllabus_id"):
            await syllabus_col.delete_one({"_id": subject["syllabus_id"]})
        
        # 2. Delete planner state
        await planner_col.delete_many({"subject_id": subject_id})
        
        # 3. Get all sessions
        sessions = await sessions_col.find({"subject_id": subject_id}).to_list(None)
        session_ids = [s["_id"] for s in sessions]
        
        # 4. Delete chats and memory
        if session_ids:
            await chats_col.delete_many({"session_id": {"$in": session_ids}})
            await memory_col.delete_many({"session_id": {"$in": session_ids}})
        
        # 5. Delete sessions
        await sessions_col.delete_many({"subject_id": subject_id})
        
        # 6. Delete notes metadata
        await notes_col.delete_many({"subject_id": subject_id})
        
        # 7. Finally, delete subject
        result = await subjects_col.delete_one({"_id": subject_id})
        
        return result.deleted_count > 0