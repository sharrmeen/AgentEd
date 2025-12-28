# backend/app/agents/orchestration/router.py

"""
State Router - Updated for Full Agent System.

Routes workflow with agent execution validation and dependency checking.
"""

from typing import Literal
from app.agents.orchestration.state import AgentEdState


def route_supervisor(state: AgentEdState) -> Literal["study_plan", "content", "quiz", "feedback", "__end__"]:
    """
    Main routing function - Entry point.
    
    Routes based on:
    1. Workflow completion flag
    2. Explicit next_step
    3. User query intent
    """
    
    if state.get("workflow_complete", False):
        print("🎯 Router: Workflow marked complete → END")
        return "__end__"
    
    next_step = state.get("next_step", "").upper()
    
    if next_step == "CONTENT":
        print("🎯 Router: next_step=CONTENT → resource agent")
        return "content"
    
    if next_step == "QUIZ":
        print("🎯 Router: next_step=QUIZ → quiz agent")
        return "quiz"
    
    if next_step == "FEEDBACK":
        print("🎯 Router: next_step=FEEDBACK → feedback agent")
        return "feedback"
    
    if next_step == "END":
        print("🎯 Router: next_step=END → workflow complete")
        return "__end__"
    
    # Parse user query for intent
    query = state.get("user_query", "").lower()
    
    if any(keyword in query for keyword in [
        "plan", "schedule", "organize", "create plan", "generate plan",
        "study plan", "progress", "objective", "complete"
    ]):
        print("🎯 Router: Query intent=PLAN → study_plan agent")
        return "study_plan"
    
    if any(keyword in query for keyword in [
        "quiz", "test", "assessment", "exam", "practice", "questions"
    ]):
        print("🎯 Router: Query intent=QUIZ → quiz agent")
        return "quiz"
    
    if any(keyword in query for keyword in [
        "feedback", "results", "score", "performance", "how did i do",
        "analyze", "review my"
    ]):
        print("🎯 Router: Query intent=FEEDBACK → feedback agent")
        return "feedback"
    
    if any(keyword in query for keyword in [
        "what", "explain", "how", "why", "tell me", "teach me",
        "describe", "define", "?"
    ]):
        print("🎯 Router: Query intent=CONTENT → resource agent")
        return "content"
    
    print("🎯 Router: No clear intent → END")
    return "__end__"


def route_from_study_plan(state: AgentEdState) -> Literal["content", "quiz", "__end__"]:
    """
    Route after study plan agent completes.
    
    Validates agent execution before routing.
    """
    
    # Check if agent completed successfully
    if state.get("planner_state") is None:
        print("⚠️ Router: Study plan generation failed → END")
        return "__end__"
    
    next_step = state.get("next_step", "END").upper()
    
    if next_step == "CONTENT":
        return "content"
    if next_step == "QUIZ":
        return "quiz"
    
    return "__end__"


def route_from_content(state: AgentEdState) -> Literal["quiz", "study_plan", "__end__"]:
    """
    Route after resource agent completes.
    
    Validates agent execution before routing.
    """
    
    # Check if agent completed successfully
    if state.get("answer") is None and state.get("content") is None:
        print("⚠️ Router: Content retrieval failed → END")
        return "__end__"
    
    next_step = state.get("next_step", "END").upper()
    
    if next_step == "QUIZ":
        return "quiz"
    if next_step == "PLAN":
        return "study_plan"
    
    return "__end__"


def route_from_quiz(state: AgentEdState) -> Literal["feedback", "__end__"]:
    """
    Route after quiz agent completes.
    
    UPDATED: Validates quiz generation before proceeding to feedback.
    Dependencies:
    - Quiz must be generated successfully
    - Feedback agent requires quiz + results
    """
    
    # Check quiz generation status
    quiz_status = state.get("quiz_generation_status")
    if quiz_status == "failed":
        print("❌ Router: Quiz generation failed → END")
        return "__end__"
    
    # Check if quiz was generated
    if not state.get("quiz"):
        print("⚠️ Router: No quiz generated → END")
        return "__end__"
    
    # If quiz generated but no results submitted yet
    if not state.get("quiz_results"):
        print("⚠️ Router: Quiz generated, awaiting user results → END")
        return "__end__"
    
    # If quiz taken, provide feedback
    next_step = state.get("next_step", "FEEDBACK").upper()
    if next_step == "FEEDBACK":
        print("🎯 Router: Quiz taken with results → feedback agent")
        return "feedback"
    
    return "__end__"


def route_from_feedback(state: AgentEdState) -> Literal["content", "study_plan", "__end__"]:
    """
    Route after feedback agent completes.
    
    UPDATED: Validates feedback generation before routing.
    Dependencies:
    - Feedback must be generated successfully
    - Requires quiz results for analysis
    """
    
    # Check feedback generation status
    feedback_status = state.get("feedback_generation_status")
    if feedback_status == "failed":
        print("❌ Router: Feedback generation failed → END")
        return "__end__"
    
    # Check if feedback was generated
    if not state.get("feedback"):
        print("⚠️ Router: No feedback generated → END")
        return "__end__"
    
    # Allow further actions based on user intent
    next_step = state.get("next_step", "END").upper()
    
    if next_step == "CONTENT":
        print("🎯 Router: User wants to review content → resource agent")
        return "content"
    if next_step == "PLAN":
        print("🎯 Router: User wants to update plan → study_plan agent")
        return "study_plan"
    
    print("🎯 Router: Feedback complete → END")
    return "__end__"


# ============================
# VALIDATION HELPERS
# ============================

def validate_quiz_execution(state: AgentEdState) -> bool:
    """Check if quiz agent executed successfully."""
    return (
        state.get("quiz_generation_status") == "success" and
        state.get("quiz") is not None and
        len(state.get("quiz", [])) > 0
    )


def validate_feedback_execution(state: AgentEdState) -> bool:
    """Check if feedback agent executed successfully."""
    return (
        state.get("feedback_generation_status") == "success" and
        state.get("feedback") is not None
    )


def validate_content_execution(state: AgentEdState) -> bool:
    """Check if resource agent executed successfully."""
    return (
        state.get("answer") is not None or 
        state.get("content") is not None
    )


def validate_plan_execution(state: AgentEdState) -> bool:
    """Check if study plan agent executed successfully."""
    return (
        state.get("planner_state") is not None and
        state.get("planner_state").get("total_chapters") is not None
    )