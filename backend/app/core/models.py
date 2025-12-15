from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SyllabusUnit(BaseModel):
    topic_name: str
    difficulty_level: str  
    estimated_hours: float
    related_chunks: List[str] 
    
class StudyTask(BaseModel):
    date: str
    topic: str
    status: str # "Pending", "Completed", "Missed"

class StudyPlan(BaseModel):
    student_id: str
    exam_date: str
    tasks: List[StudyTask]

class StudentProfile(BaseModel):
    student_id: str
    weak_topics: List[str] # List of topics where quiz score < 60%
    mastered_topics: List[str]

class UserProfile(BaseModel):
    user_id: str
    username: str
    created_at: datetime = Field(default_factory=datetime.now)
    # Track progress for the Planner Agent
    weak_topics: List[str] = []
    mastered_topics: List[str] = []
    # Simple way to track quiz performance
    total_score: int = 0

