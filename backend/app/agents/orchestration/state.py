# backend/app/agents/orchestration/state.py

"""
Agent State Schema - Updated for Full Agent System.

Tracks agent execution, tool results, and inter-agent communication.
"""

from typing import TypedDict, List, Optional, Dict, Any, Annotated
import operator


class AgentEdState(TypedDict, total=False):
    """
    Complete state schema for multi-agent workflow.
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
    constraints: Optional[Dict[str, Any]]
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
    # QUIZ DATA (Extended for Agent Execution)
    # ============================
    quiz: Optional[Dict[str, Any]]
    quiz_metadata: Optional[Dict[str, Any]]
    quiz_results: Optional[Dict[str, Any]]
    quiz_score: Optional[float]
    
    # NEW: Quiz agent execution tracking
    retrieved_quiz_content: Optional[Dict[str, Any]]  # Content retrieved by quiz agent
    quiz_objectives: Optional[List[str]]  # Learning objectives retrieved
    quiz_generation_status: Optional[str]  # "pending" | "success" | "failed"
    
    # ============================
    # FEEDBACK DATA (Extended for Agent Execution)
    # ============================
    feedback: Optional[Dict[str, Any]]
    performance_analysis: Optional[Dict[str, Any]]
    student_profile: Optional[Dict[str, Any]]
    
    # NEW: Feedback agent execution tracking
    retrieved_weak_materials: Optional[Dict[str, Any]]  # Materials for weak topics
    student_progress_context: Optional[Dict[str, Any]]  # Progress from planner
    performance_metrics: Optional[Dict[str, Any]]  # Calculated metrics
    feedback_generation_status: Optional[str]  # "pending" | "success" | "failed"
    
    # ============================
    # CONVERSATION MEMORY
    # ============================
    messages: Annotated[List[str], operator.add]
    chat_history: Optional[List[Dict[str, Any]]]
    
    # ============================
    # CONTROL FLOW
    # ============================
    next_step: str
    workflow_complete: bool
    
    # ============================
    # ERROR HANDLING & LOGGING
    # ============================
    errors: Optional[List[str]]
    tool_execution_log: Optional[List[Dict[str, Any]]]  # Track tool calls
    agent_error_log: Optional[List[str]]  # Track agent-specific errors
    
    # ============================
    # INTER-AGENT COMMUNICATION
    # ============================
    agent_dependencies: Optional[Dict[str, str]]  # Maps agent dependencies
    tool_results: Optional[List[Dict[str, Any]]]  # Results from tool executions
    
    # ============================
    # METADATA
    # ============================
    timestamp: Optional[str]
    workflow_id: Optional[str]
    agent_trace: Optional[List[str]]  # Which agents were called
    execution_times: Optional[Dict[str, float]]  # Track agent execution time