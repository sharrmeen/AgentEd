from typing import TypedDict, List, Optional, Annotated
import operator

class AgentEdState(TypedDict):
    # user Input
    user_query: str
    
    # data frm models
    syllabus_topics: Optional[List[dict]] 
    study_plan: Optional[dict]            
    student_profile: Optional[dict]       # contains "weak_areas"
    
    #conversation memory
    messages: Annotated[List[str], operator.add]
    
    # routing
    next_step: str  # "planner", "quizzer", "content", or "end"