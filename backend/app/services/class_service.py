"""
Class management service.
"""

from datetime import datetime
from typing import Optional, List, Tuple
from bson import ObjectId

from app.core.database import db
from app.services.user_service import UserService


class ClassService:
    @staticmethod
    async def create_class(
        *,
        name: str,
        created_by: ObjectId,
        section: Optional[str] = None,
        teacher_id: Optional[str] = None,
    ) -> dict:
        classes_col = db.classes()

        teacher_obj_id = None
        if teacher_id:
            if not ObjectId.is_valid(teacher_id):
                raise ValueError("Invalid teacher ID format")
            teacher_obj_id = ObjectId(teacher_id)
            teacher = await UserService.get_user_by_id(teacher_obj_id)
            if not teacher or teacher.role != "teacher":
                raise ValueError("Teacher not found")

        now = datetime.utcnow()
        class_doc = {
            "name": name.strip(),
            "section": section.strip() if section else None,
            "teacher_id": teacher_obj_id,
            "created_by": created_by,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

        result = await classes_col.insert_one(class_doc)
        class_doc["_id"] = result.inserted_id
        return class_doc

    @staticmethod
    async def list_classes(
        *,
        skip: int = 0,
        limit: int = 50,
        teacher_id: Optional[ObjectId] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[dict], int]:
        classes_col = db.classes()
        users_col = db.users()

        query: dict = {}
        if teacher_id is not None:
            query["teacher_id"] = teacher_id
        if is_active is not None:
            query["is_active"] = is_active

        total = await classes_col.count_documents(query)
        docs = await classes_col.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(None)

        enriched = []
        for item in docs:
            teacher_name = None
            if item.get("teacher_id"):
                teacher = await users_col.find_one({"_id": item["teacher_id"]})
                teacher_name = teacher.get("name") if teacher else None

            class_id = str(item["_id"])
            student_count = await users_col.count_documents({"role": "student", "class_id": class_id})

            enriched.append({
                **item,
                "teacher_name": teacher_name,
                "student_count": student_count,
            })

        return enriched, total

    @staticmethod
    async def get_class_by_id(class_id: ObjectId) -> Optional[dict]:
        return await db.classes().find_one({"_id": class_id})

    @staticmethod
    async def update_class(
        *,
        class_id: ObjectId,
        name: Optional[str] = None,
        section: Optional[str] = None,
        teacher_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> dict:
        classes_col = db.classes()

        existing = await classes_col.find_one({"_id": class_id})
        if not existing:
            raise ValueError("Class not found")

        update_set: dict = {"updated_at": datetime.utcnow()}

        if name is not None:
            update_set["name"] = name.strip()
        if section is not None:
            update_set["section"] = section.strip() if section else None
        if is_active is not None:
            update_set["is_active"] = is_active

        if teacher_id is not None:
            if teacher_id == "":
                update_set["teacher_id"] = None
            else:
                if not ObjectId.is_valid(teacher_id):
                    raise ValueError("Invalid teacher ID format")
                teacher_obj_id = ObjectId(teacher_id)
                teacher = await UserService.get_user_by_id(teacher_obj_id)
                if not teacher or teacher.role != "teacher":
                    raise ValueError("Teacher not found")
                update_set["teacher_id"] = teacher_obj_id

        await classes_col.update_one({"_id": class_id}, {"$set": update_set})
        updated = await classes_col.find_one({"_id": class_id})
        return updated

    @staticmethod
    async def list_students_for_class(class_id: str) -> List[dict]:
        users_col = db.users()
        students = await users_col.find({"role": "student", "class_id": class_id}).sort("name", 1).to_list(None)
        return students

    @staticmethod
    async def assign_students(*, class_id: str, student_ids: List[str]) -> int:
        users_col = db.users()

        if not ObjectId.is_valid(class_id):
            raise ValueError("Invalid class ID format")

        class_doc = await db.classes().find_one({"_id": ObjectId(class_id)})
        if not class_doc:
            raise ValueError("Class not found")

        valid_object_ids: List[ObjectId] = []
        for student_id in student_ids:
            if not ObjectId.is_valid(student_id):
                raise ValueError(f"Invalid student ID format: {student_id}")
            valid_object_ids.append(ObjectId(student_id))

        now = datetime.utcnow()

        # 1) Unassign currently enrolled students that are no longer selected.
        unassign_filter: dict = {"role": "student", "class_id": class_id}
        if valid_object_ids:
            unassign_filter["_id"] = {"$nin": valid_object_ids}

        unassign_result = await users_col.update_many(
            unassign_filter,
            {"$set": {"class_id": None, "updated_at": now}},
        )

        # 2) Assign selected students to this class.
        assign_result = await users_col.update_many(
            {"_id": {"$in": valid_object_ids}, "role": "student"} if valid_object_ids else {"_id": {"$in": []}},
            {"$set": {"class_id": class_id, "updated_at": now}},
        )

        return unassign_result.modified_count + assign_result.modified_count
