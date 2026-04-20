"""
Class management endpoints for admin and teachers.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from bson import ObjectId

from app.api.deps import get_current_admin_user, get_current_teacher_user
from app.core.database import db
from app.schemas.classroom import (
    ClassCreateRequest,
    ClassUpdateRequest,
    ClassListResponse,
    ClassResponse,
    ClassStudentsAssignRequest,
    ClassStudentsResponse,
    ClassStudentItem,
    TeacherClassProgressResponse,
    TeacherClassProgressStudent,
)
from app.services.class_service import ClassService
from app.services.user_service import UserService

router = APIRouter()


@router.post("/admin", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    request: ClassCreateRequest,
    current_user: dict = Depends(get_current_admin_user),
):
    try:
        class_doc = await ClassService.create_class(
            name=request.name,
            section=request.section,
            teacher_id=request.teacher_id,
            created_by=ObjectId(current_user["id"]),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    teacher_name = None
    if class_doc.get("teacher_id"):
        teacher = await UserService.get_user_by_id(class_doc["teacher_id"])
        teacher_name = teacher.name if teacher else None

    return ClassResponse(
        id=str(class_doc["_id"]),
        name=class_doc["name"],
        section=class_doc.get("section"),
        teacher_id=str(class_doc["teacher_id"]) if class_doc.get("teacher_id") else None,
        teacher_name=teacher_name,
        student_count=0,
        is_active=class_doc.get("is_active", True),
        created_at=class_doc["created_at"],
        updated_at=class_doc["updated_at"],
    )


@router.get("/admin", response_model=ClassListResponse)
async def list_classes_for_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_admin_user),
):
    classes, total = await ClassService.list_classes(skip=skip, limit=limit)

    return ClassListResponse(
        classes=[
            ClassResponse(
                id=str(item["_id"]),
                name=item["name"],
                section=item.get("section"),
                teacher_id=str(item["teacher_id"]) if item.get("teacher_id") else None,
                teacher_name=item.get("teacher_name"),
                student_count=item.get("student_count", 0),
                is_active=item.get("is_active", True),
                created_at=item["created_at"],
                updated_at=item["updated_at"],
            )
            for item in classes
        ],
        total=total,
    )


@router.patch("/admin/{class_id}", response_model=ClassResponse)
async def update_class_for_admin(
    class_id: str,
    request: ClassUpdateRequest,
    current_user: dict = Depends(get_current_admin_user),
):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID format")

    try:
        updated = await ClassService.update_class(
            class_id=ObjectId(class_id),
            name=request.name,
            section=request.section,
            teacher_id=request.teacher_id,
            is_active=request.is_active,
        )
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if str(e) == "Class not found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))

    teacher_name = None
    if updated.get("teacher_id"):
        teacher = await UserService.get_user_by_id(updated["teacher_id"])
        teacher_name = teacher.name if teacher else None

    student_count = len(await ClassService.list_students_for_class(class_id))

    return ClassResponse(
        id=str(updated["_id"]),
        name=updated["name"],
        section=updated.get("section"),
        teacher_id=str(updated["teacher_id"]) if updated.get("teacher_id") else None,
        teacher_name=teacher_name,
        student_count=student_count,
        is_active=updated.get("is_active", True),
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
    )


@router.get("/admin/{class_id}/students", response_model=ClassStudentsResponse)
async def list_students_for_class_admin(
    class_id: str,
    current_user: dict = Depends(get_current_admin_user),
):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID format")

    class_doc = await ClassService.get_class_by_id(ObjectId(class_id))
    if not class_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    students = await ClassService.list_students_for_class(class_id)
    return ClassStudentsResponse(
        class_id=class_id,
        students=[
            ClassStudentItem(
                id=str(s["_id"]),
                name=s.get("name"),
                username=s.get("username"),
                email=s.get("email"),
                class_id=s.get("class_id"),
                last_login=s.get("last_login"),
            )
            for s in students
        ],
        total=len(students),
    )


@router.post("/admin/{class_id}/students")
async def assign_students_to_class(
    class_id: str,
    request: ClassStudentsAssignRequest,
    current_user: dict = Depends(get_current_admin_user),
):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID format")

    class_doc = await ClassService.get_class_by_id(ObjectId(class_id))
    if not class_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    try:
        modified = await ClassService.assign_students(class_id=class_id, student_ids=request.student_ids)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"success": True, "modified": modified}


@router.get("/teacher/me", response_model=ClassListResponse)
async def list_classes_for_teacher(current_user: dict = Depends(get_current_teacher_user)):

    classes, total = await ClassService.list_classes(
        teacher_id=ObjectId(current_user["id"]),
        is_active=True,
    )

    return ClassListResponse(
        classes=[
            ClassResponse(
                id=str(item["_id"]),
                name=item["name"],
                section=item.get("section"),
                teacher_id=str(item["teacher_id"]) if item.get("teacher_id") else None,
                teacher_name=item.get("teacher_name"),
                student_count=item.get("student_count", 0),
                is_active=item.get("is_active", True),
                created_at=item["created_at"],
                updated_at=item["updated_at"],
            )
            for item in classes
        ],
        total=total,
    )


@router.get("/teacher/me/{class_id}/students", response_model=ClassStudentsResponse)
async def list_teacher_class_students(
    class_id: str,
    current_user: dict = Depends(get_current_teacher_user),
):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID format")

    class_doc = await ClassService.get_class_by_id(ObjectId(class_id))
    if not class_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    if class_doc.get("teacher_id") != ObjectId(current_user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for this class")

    students = await ClassService.list_students_for_class(class_id)
    return ClassStudentsResponse(
        class_id=class_id,
        students=[
            ClassStudentItem(
                id=str(s["_id"]),
                name=s.get("name"),
                username=s.get("username"),
                email=s.get("email"),
                class_id=s.get("class_id"),
                last_login=s.get("last_login"),
            )
            for s in students
        ],
        total=len(students),
    )


@router.get("/teacher/me/{class_id}/progress", response_model=TeacherClassProgressResponse)
async def teacher_class_progress(
    class_id: str,
    current_user: dict = Depends(get_current_teacher_user),
):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID format")

    class_doc = await ClassService.get_class_by_id(ObjectId(class_id))
    if not class_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    if class_doc.get("teacher_id") != ObjectId(current_user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for this class")

    students = await ClassService.list_students_for_class(class_id)
    quiz_results_col = db.quiz_results()

    progress_items = []
    for student in students:
        student_id = student["_id"]
        results = await quiz_results_col.find({"user_id": student_id}).to_list(None)
        quizzes_completed = len(results)
        average_score = 0.0
        if quizzes_completed > 0:
            average_score = round(sum(r.get("percentage", 0.0) for r in results) / quizzes_completed, 2)

        progress_items.append(
            TeacherClassProgressStudent(
                student_id=str(student_id),
                student_name=student.get("name", "Unknown"),
                username=student.get("username", ""),
                quizzes_completed=quizzes_completed,
                average_score=average_score,
            )
        )

    return TeacherClassProgressResponse(
        class_id=class_id,
        class_name=class_doc.get("name", "Class"),
        student_progress=progress_items,
    )
