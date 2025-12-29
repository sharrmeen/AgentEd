# backend/app/services/planner_service.py

from datetime import datetime, timedelta
from bson import ObjectId
from typing import Optional, Dict, List

from app.core.database import db
from app.core.models.planner import PlannerState
from app.services.subject_service import SubjectService
from app.services.syllabus_service import SyllabusService


class PlannerService:
    """
    Intelligent Planner service with auto-adjustment.
    
    Features:
    - Objective-based chapter completion
    - Deadline tracking per chapter
    - Auto-replanning when deadlines missed (token-efficient)
    - Progress preservation during replanning
    
    Workflow:
    1. Generate plan with chapter deadlines
    2. Track objective completion
    3. Auto-mark chapter complete when all objectives done
    4. Check deadline: if missed → auto-replan (ONLY after deadline)
    5. Adjust remaining chapters' timeline
    """

    # ============================
    # GENERATE PLAN
    # ============================

    @staticmethod
    async def generate_plan(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        target_days: int,
        daily_hours: float = 2.0,
        preferences: Optional[Dict] = None
    ) -> PlannerState:
        """
        Generate study plan with chapter deadlines.
        
        Sets deadline for each chapter based on estimated hours.
        """
        subjects_col = db.subjects()
        syllabus_col = db.syllabus()
        planner_col = db.planner_state()
        
        # Validate subject has syllabus
        subject = await SubjectService.validate_has_syllabus(
            user_id=user_id,
            subject_id=subject_id
        )
        
        # Check for existing plan
        existing_planner = await planner_col.find_one({
            "user_id": user_id,
            "subject_id": subject_id
        })
        
        if existing_planner:
            raise ValueError(
                "Study plan already exists. "
                "Use regenerate_plan() to create a new one."
            )
        
        # Fetch syllabus text
        syllabus = await syllabus_col.find_one({
            "_id": subject.syllabus_id
        })
        
        # Call Planner Agent Core Function (NOT tool)
        from app.agents.planner_agent import generate_study_plan_core
        
        plan_output = await generate_study_plan_core(
            syllabus_text=syllabus["raw_text"],
            subject_name=subject.subject_name,
            target_days=target_days,
            daily_hours=daily_hours,
            user_preferences=preferences or {}
        )
        
        # Store plan in Subject
        await SubjectService.update_plan(
            user_id=user_id,
            subject_id=subject_id,
            plan=plan_output
        )
        
        # Calculate chapter deadlines
        meta = plan_output["meta"]
        chapters = plan_output["chapters"]
        
        chapter_progress = {}
        current_date = datetime.utcnow()
        
        for chapter in chapters:
            ch_num = chapter["chapter_number"]
            estimated_hours = chapter.get("estimated_hours", 0)
            
            # Calculate days needed for this chapter
            days_needed = estimated_hours / daily_hours if daily_hours > 0 else 1
            
            # Set deadline
            deadline = current_date + timedelta(days=days_needed)
            
            chapter_progress[str(ch_num)] = {
                "completed_objectives": [],
                "total_objectives": len(chapter.get("objectives", [])),
                "is_complete": False,
                "started_at": None,
                "completed_at": None,
                "deadline": deadline.isoformat(),
                "estimated_hours": estimated_hours
            }
            
            # Move current_date forward for next chapter
            current_date = deadline
        
        # Create PlannerState
        first_chapter_title = chapters[0]["title"] if chapters else "Unknown"
        
        planner_doc = {
            "user_id": user_id,
            "subject_id": subject_id,
            
            # Metadata
            "total_chapters": len(chapters),
            "target_days": target_days,
            "daily_hours": daily_hours,
            "estimated_total_hours": meta.get("total_hours", 0),
            
            # Progress
            "current_chapter": 1,
            "completed_chapters": [],
            "completion_percent": 0.0,
            "chapter_progress": chapter_progress,
            
            # Auto-replanning
            "last_replanned_at": None,
            "replan_count": 0,
            "missed_deadlines": [],
            
            # Recommendations
            "next_suggestion": f"Start with Chapter 1: {first_chapter_title}",
            "study_pace": "on_track",
            
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        result = await planner_col.insert_one(planner_doc)
        planner_doc["_id"] = result.inserted_id
        
        return PlannerState(**planner_doc)

    # ============================
    # MARK OBJECTIVE COMPLETE
    # ============================

    @staticmethod
    async def mark_objective_complete(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        chapter_number: int,
        objective: str
    ) -> Dict:
        """
        Mark a single objective as complete.
        
        Auto-completes chapter if all objectives done.
        Auto-replans if deadline missed.
        
        Returns:
        {
            "chapter_completed": bool,
            "replanned": bool,
            "planner_state": PlannerState
        }
        """
        planner_col = db.planner_state()
        subjects_col = db.subjects()
        
        planner = await planner_col.find_one({
            "user_id": user_id,
            "subject_id": subject_id
        })
        
        if not planner:
            raise ValueError("Study plan not found")
        
        ch_key = str(chapter_number)
        chapter_progress = planner["chapter_progress"].get(ch_key, {})
        
        if not chapter_progress:
            raise ValueError(f"Chapter {chapter_number} not found in plan")
        
        # Mark objective complete
        completed = chapter_progress.get("completed_objectives", [])
        
        if objective not in completed:
            completed.append(objective)
        
        # Set started_at if first objective
        if not chapter_progress.get("started_at") and len(completed) == 1:
            chapter_progress["started_at"] = datetime.utcnow().isoformat()
        
        chapter_progress["completed_objectives"] = completed
        
        # Check if all objectives complete
        total_objectives = chapter_progress.get("total_objectives", 0)
        all_complete = len(completed) >= total_objectives and total_objectives > 0
        
        chapter_completed = False
        replanned = False
        
        if all_complete and not chapter_progress.get("is_complete"):
            # AUTO-COMPLETE CHAPTER
            chapter_progress["is_complete"] = True
            chapter_progress["completed_at"] = datetime.utcnow().isoformat()
            chapter_completed = True
            
            # Add to completed chapters list
            completed_chapters = planner.get("completed_chapters", [])
            if chapter_number not in completed_chapters:
                completed_chapters.append(chapter_number)
                completed_chapters.sort()
            
            # Update main planner state
            completion_percent = (len(completed_chapters) / planner["total_chapters"]) * 100
            
            await planner_col.update_one(
                {"_id": planner["_id"]},
                {
                    "$set": {
                        f"chapter_progress.{ch_key}": chapter_progress,
                        "completed_chapters": completed_chapters,
                        "completion_percent": round(completion_percent, 2),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # CHECK DEADLINE
            deadline_str = chapter_progress.get("deadline")
            if deadline_str:
                deadline = datetime.fromisoformat(deadline_str)
                now = datetime.utcnow()
                
                if now > deadline:
                    # DEADLINE MISSED - AUTO-REPLAN
                    print(f"⚠️ Chapter {chapter_number} completed after deadline. Auto-replanning...")
                    
                    await PlannerService._auto_replan(
                        user_id=user_id,
                        subject_id=subject_id,
                        missed_chapter=chapter_number
                    )
                    
                    replanned = True
        else:
            # Just update objective progress
            await planner_col.update_one(
                {"_id": planner["_id"]},
                {
                    "$set": {
                        f"chapter_progress.{ch_key}": chapter_progress,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        
        # Fetch updated planner
        updated_planner = await planner_col.find_one({"_id": planner["_id"]})
        
        return {
            "chapter_completed": chapter_completed,
            "replanned": replanned,
            "planner_state": PlannerState(**updated_planner)
        }

    # ============================
    # AUTO-REPLANNING (Internal)
    # ============================

    @staticmethod
    async def _auto_replan(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        missed_chapter: int
    ) -> None:
        """
        Auto-replan when deadline missed (TOKEN-EFFICIENT).
        
        Only called AFTER deadline passes.
        Adjusts remaining chapters' timeline.
        Preserves completed chapters.
        """
        planner_col = db.planner_state()
        subjects_col = db.subjects()
        syllabus_col = db.syllabus()
        
        planner = await planner_col.find_one({
            "user_id": user_id,
            "subject_id": subject_id
        })
        
        # Track missed deadline
        missed_deadlines = planner.get("missed_deadlines", [])
        if missed_chapter not in missed_deadlines:
            missed_deadlines.append(missed_chapter)
        
        # Calculate remaining chapters
        completed = planner.get("completed_chapters", [])
        total_chapters = planner.get("total_chapters", 0)
        remaining_chapters = total_chapters - len(completed)
        
        if remaining_chapters <= 0:
            # All done, no need to replan
            return
        
        # Calculate remaining days
        original_target_days = planner.get("target_days", 30)
        days_elapsed = (datetime.utcnow() - planner["created_at"]).days
        remaining_days = max(original_target_days - days_elapsed, 1)  # At least 1 day
        
        # Fetch subject and syllabus
        subject = await subjects_col.find_one({"_id": subject_id})
        syllabus = await syllabus_col.find_one({"_id": subject["syllabus_id"]})
        
        # Call Planner Agent Core Function (NOT tool)
        from app.agents.planner_agent import generate_study_plan_core
        
        print(f"🔄 Replanning with {remaining_days} days for {remaining_chapters} chapters...")
        
        new_plan_output = await generate_study_plan_core(
            syllabus_text=syllabus["raw_text"],
            subject_name=subject["subject_name"],
            target_days=remaining_days,
            daily_hours=planner.get("daily_hours", 2.0),
            user_preferences={}
        )
        
        # Update Subject plan
        await SubjectService.update_plan(
            user_id=user_id,
            subject_id=subject_id,
            plan=new_plan_output
        )
        
        # Recalculate chapter deadlines for REMAINING chapters
        new_chapters = new_plan_output["chapters"]
        chapter_progress = planner.get("chapter_progress", {})
        
        current_date = datetime.utcnow()
        daily_hours = planner.get("daily_hours", 2.0)
        
        for chapter in new_chapters:
            ch_num = chapter["chapter_number"]
            
            # Skip completed chapters
            if ch_num in completed:
                continue
            
            ch_key = str(ch_num)
            estimated_hours = chapter.get("estimated_hours", 0)
            days_needed = estimated_hours / daily_hours if daily_hours > 0 else 1
            
            new_deadline = current_date + timedelta(days=days_needed)
            
            # Preserve existing progress if chapter was started
            if ch_key in chapter_progress:
                chapter_progress[ch_key]["deadline"] = new_deadline.isoformat()
                chapter_progress[ch_key]["estimated_hours"] = estimated_hours
                chapter_progress[ch_key]["total_objectives"] = len(chapter.get("objectives", []))
            else:
                chapter_progress[ch_key] = {
                    "completed_objectives": [],
                    "total_objectives": len(chapter.get("objectives", [])),
                    "is_complete": False,
                    "started_at": None,
                    "completed_at": None,
                    "deadline": new_deadline.isoformat(),
                    "estimated_hours": estimated_hours
                }
            
            current_date = new_deadline
        
        # Update planner state
        await planner_col.update_one(
            {"_id": planner["_id"]},
            {
                "$set": {
                    "chapter_progress": chapter_progress,
                    "missed_deadlines": missed_deadlines,
                    "last_replanned_at": datetime.utcnow(),
                    "study_pace": "behind",
                    "next_suggestion": f"⚠️ Plan adjusted. Focus on remaining {remaining_chapters} chapters.",
                    "updated_at": datetime.utcnow()
                },
                "$inc": {
                    "replan_count": 1
                }
            }
        )
        
        print(f"✅ Replan complete. New deadlines set for remaining chapters.")

    # ============================
    # GET CHAPTER PROGRESS
    # ============================

    @staticmethod
    async def get_chapter_progress(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        chapter_number: int
    ) -> Dict:
        """
        Get detailed progress for a specific chapter.
        
        Returns:
        {
            "chapter_number": 1,
            "completed_objectives": ["Understand cells", ...],
            "total_objectives": 5,
            "progress_percent": 40.0,
            "is_complete": false,
            "deadline": "2025-01-15T00:00:00",
            "days_remaining": 3,
            "is_overdue": false
        }
        """
        planner_col = db.planner_state()
        
        planner = await planner_col.find_one({
            "user_id": user_id,
            "subject_id": subject_id
        })
        
        if not planner:
            raise ValueError("Study plan not found")
        
        ch_key = str(chapter_number)
        chapter_progress = planner["chapter_progress"].get(ch_key, {})
        
        if not chapter_progress:
            raise ValueError(f"Chapter {chapter_number} not found")
        
        completed = len(chapter_progress.get("completed_objectives", []))
        total = chapter_progress.get("total_objectives", 0)
        progress_percent = (completed / total * 100) if total > 0 else 0
        
        deadline_str = chapter_progress.get("deadline")
        deadline = datetime.fromisoformat(deadline_str) if deadline_str else None
        
        days_remaining = None
        is_overdue = False
        
        if deadline:
            delta = deadline - datetime.utcnow()
            days_remaining = delta.days
            is_overdue = days_remaining < 0
        
        return {
            "chapter_number": chapter_number,
            "completed_objectives": chapter_progress.get("completed_objectives", []),
            "total_objectives": total,
            "progress_percent": round(progress_percent, 2),
            "is_complete": chapter_progress.get("is_complete", False),
            "deadline": deadline.isoformat() if deadline else None,
            "days_remaining": days_remaining,
            "is_overdue": is_overdue,
            "started_at": chapter_progress.get("started_at"),
            "completed_at": chapter_progress.get("completed_at")
        }

    # ============================
    # MANUAL CHAPTER COMPLETION
    # ============================

    @staticmethod
    async def mark_chapter_complete(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        chapter_number: int
    ) -> PlannerState:
        """
        Manually mark chapter as complete (bypasses objective tracking).
        
        Use case: User wants to skip objectives and just mark done.
        """
        planner_col = db.planner_state()
        
        planner = await planner_col.find_one({
            "user_id": user_id,
            "subject_id": subject_id
        })
        
        if not planner:
            raise ValueError("Study plan not found")
        
        ch_key = str(chapter_number)
        chapter_progress = planner.get("chapter_progress", {}).get(ch_key, {})
        
        if chapter_progress.get("is_complete"):
            raise ValueError(f"Chapter {chapter_number} already marked complete")
        
        # Mark complete
        chapter_progress["is_complete"] = True
        chapter_progress["completed_at"] = datetime.utcnow().isoformat()
        
        # Add to completed list
        completed_chapters = planner.get("completed_chapters", [])
        if chapter_number not in completed_chapters:
            completed_chapters.append(chapter_number)
            completed_chapters.sort()
        
        # Update
        completion_percent = (len(completed_chapters) / planner["total_chapters"]) * 100
        
        await planner_col.update_one(
            {"_id": planner["_id"]},
            {
                "$set": {
                    f"chapter_progress.{ch_key}": chapter_progress,
                    "completed_chapters": completed_chapters,
                    "completion_percent": round(completion_percent, 2),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        updated = await planner_col.find_one({"_id": planner["_id"]})
        return PlannerState(**updated)

    # ============================
    # GET PLANNER STATE
    # ============================

    @staticmethod
    async def get_planner_state(
        *,
        user_id: ObjectId,
        subject_id: ObjectId
    ) -> Optional[PlannerState]:
        """Retrieve planner state."""
        planner_col = db.planner_state()
        
        doc = await planner_col.find_one({
            "user_id": user_id,
            "subject_id": subject_id
        })
        
        return PlannerState(**doc) if doc else None

    # ============================
    # MANUAL REGENERATE
    # ============================

    @staticmethod
    async def regenerate_plan(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        target_days: int,
        daily_hours: float = 2.0,
        preferences: Optional[Dict] = None
    ) -> PlannerState:
        """
        Manually regenerate plan (preserves progress).
        """
        planner_col = db.planner_state()
        
        old_planner = await planner_col.find_one({
            "user_id": user_id,
            "subject_id": subject_id
        })
        
        if not old_planner:
            raise ValueError("No existing plan found")
        
        # Delete old plan
        await planner_col.delete_one({"_id": old_planner["_id"]})
        
        # Generate new plan
        return await PlannerService.generate_plan(
            user_id=user_id,
            subject_id=subject_id,
            target_days=target_days,
            daily_hours=daily_hours,
            preferences=preferences
        )
    