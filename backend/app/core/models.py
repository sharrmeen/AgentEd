from typing import List
from pydantic import BaseModel


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
    weak_topics: List[str] # List of topics where quiz score < 60%
    mastered_topics: List[str]