"""
Class management schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ClassCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    section: Optional[str] = Field(None, max_length=20)
    teacher_id: Optional[str] = None


class ClassUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    section: Optional[str] = Field(None, max_length=20)
    teacher_id: Optional[str] = None
    is_active: Optional[bool] = None


class ClassResponse(BaseModel):
    id: str
    name: str
    section: Optional[str] = None
    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = None
    student_count: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class ClassListResponse(BaseModel):
    classes: List[ClassResponse]
    total: int


class ClassStudentsAssignRequest(BaseModel):
    student_ids: List[str]


class ClassStudentItem(BaseModel):
    id: str
    name: str
    username: str
    email: Optional[str] = None
    class_id: Optional[str] = None
    last_login: Optional[datetime] = None


class ClassStudentsResponse(BaseModel):
    class_id: str
    students: List[ClassStudentItem]
    total: int


class TeacherClassProgressStudent(BaseModel):
    student_id: str
    student_name: str
    username: str
    quizzes_completed: int
    average_score: float


class TeacherClassProgressResponse(BaseModel):
    class_id: str
    class_name: str
    student_progress: List[TeacherClassProgressStudent]
