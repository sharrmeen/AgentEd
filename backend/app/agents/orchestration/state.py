# backend/app/agents/orchestration/state.py

"""
Agent State Schema - Defines workflow state structure.

All fields are passed between agents via this state object.
"""

from typing import TypedDict, List, Optional, Dict, Any, Annotated
import operator


class AgentEdState(TypedDict, total=False):
    """
    Complete state schema for agent workflow.
    
    Using total=False makes all fields optional, allowing flexible initialization.
    """
    
    # ============================
    # USER CONTEXT
    # ============================
    user_id: str
    user_query: str
    
    # ============================
    # SUBJECT CONTEXT
    # ============================
    subject_id: Optional[str]
    subject_name: Optional[str]
    chapter_number: Optional[int]
    session_id: Optional[str]
    
    # ============================
    # STUDY PLAN DATA
    # ============================
    syllabus: Optional[Dict[str, Any]]
    syllabus_topics: Optional[List[dict]]
    constraints: Optional[Dict[str, Any]]  # target_days, daily_hours
    study_plan: Optional[Dict[str, Any]]
    planner_state: Optional[Dict[str, Any]]
    
    # ============================
    # RESOURCE/CONTENT DATA
    # ============================
    current_topic: Optional[str]
    content: Optional[str]
    retrieved_docs: Optional[List[Dict[str, Any]]]
    web_search_results: Optional[List[Dict[str, Any]]]
    answer: Optional[str]
    
    # ============================
    # QUIZ DATA
    # ============================
    quiz: Optional[Dict[str, Any]]
    quiz_metadata: Optional[Dict[str, Any]]
    quiz_results: Optional[Dict[str, Any]]
    quiz_score: Optional[float]
    
    # ============================
    # FEEDBACK DATA
    # ============================
    feedback: Optional[Dict[str, Any]]
    performance_analysis: Optional[Dict[str, Any]]
    student_profile: Optional[Dict[str, Any]]  # contains "weak_areas"
    
    # ============================
    # CONVERSATION MEMORY
    # ============================
    messages: Annotated[List[str], operator.add]
    chat_history: Optional[List[Dict[str, Any]]]
    
    # ============================
    # CONTROL FLOW
    # ============================
    next_step: str  # "study_plan", "content", "quiz", "feedback", "END"
    workflow_complete: bool
    
    # ============================
    # ERROR HANDLING
    # ============================
    errors: Optional[List[str]]
    
    # ============================
    # METADATA
    # ============================
    timestamp: Optional[str]
    workflow_id: Optional[str]
    agent_trace: Optional[List[str]]  # Track which agents were called