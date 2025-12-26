# backend/app/agents/orchestration/router.py

"""
State Router (Refactored) - Intelligent Routing Logic.

Routes workflow between agents based on:
- User query keywords
- Current state (next_step)
- Workflow completion flag
"""

from typing import Literal
from app.agents.orchestration.state import AgentEdState


def route_supervisor(state: AgentEdState) -> Literal["study_plan", "content", "quiz", "feedback", "__end__"]:
    """
    Main routing function for agent workflow.
    
    Routing Priority:
    1. Check workflow_complete flag (if True → END)
    2. Check explicit next_step in state
    3. Parse user query for intent
    4. Default to END if no clear route
    """
    
    # -------------------------
    # 1️⃣ Check Completion Flag
    # -------------------------
    if state.get("workflow_complete", False):
        print("🎯 Router: Workflow marked complete → END")
        return "__end__"
    
    # -------------------------
    # 2️⃣ Check Explicit Next Step
    # -------------------------
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
    
    # -------------------------
    # 3️⃣ Parse User Query
    # -------------------------
    query = state.get("user_query", "").lower()
    
    # Planning intents
    if any(keyword in query for keyword in [
        "plan", "schedule", "organize", "create plan", "generate plan",
        "study plan", "progress", "objective", "complete"
    ]):
        print("🎯 Router: Query intent=PLAN → study_plan agent")
        return "study_plan"
    
    # Quiz intents
    if any(keyword in query for keyword in [
        "quiz", "test", "assessment", "exam", "practice", "questions"
    ]):
        print("🎯 Router: Query intent=QUIZ → quiz agent")
        return "quiz"
    
    # Feedback intents
    if any(keyword in query for keyword in [
        "feedback", "results", "score", "performance", "how did i do",
        "analyze", "review my"
    ]):
        print("🎯 Router: Query intent=FEEDBACK → feedback agent")
        return "feedback"
    
    # Knowledge/content intents (default for questions)
    if any(keyword in query for keyword in [
        "what", "explain", "how", "why", "tell me", "teach me",
        "describe", "define", "?"
    ]):
        print("🎯 Router: Query intent=CONTENT → resource agent")
        return "content"
    
    # -------------------------
    # 4️⃣ Default to END
    # -------------------------
    print("🎯 Router: No clear intent → END")
    return "__end__"


def route_from_study_plan(state: AgentEdState) -> Literal["content", "quiz", "__end__"]:
    """
    Route after study plan agent completes.
    
    Possible transitions:
    - If user wants to learn content → content agent
    - If user wants quiz → quiz agent
    - Otherwise → end
    """
    next_step = state.get("next_step", "END").upper()
    
    if next_step == "CONTENT":
        return "content"
    if next_step == "QUIZ":
        return "quiz"
    
    return "__end__"


def route_from_content(state: AgentEdState) -> Literal["quiz", "study_plan", "__end__"]:
    """
    Route after resource agent completes.
    
    Possible transitions:
    - If user wants quiz next → quiz agent
    - If user wants to update plan → study_plan agent
    - Otherwise → end
    """
    next_step = state.get("next_step", "END").upper()
    
    if next_step == "QUIZ":
        return "quiz"
    if next_step == "PLAN":
        return "study_plan"
    
    return "__end__"


def route_from_quiz(state: AgentEdState) -> Literal["feedback", "__end__"]:
    """
    Route after quiz agent completes.
    
    Typically goes to feedback agent if quiz results exist.
    """
    next_step = state.get("next_step", "FEEDBACK").upper()
    
    # If quiz was generated but not taken yet
    if not state.get("quiz_results"):
        print("🎯 Router: Quiz generated but not taken yet → END")
        return "__end__"
    
    # If quiz was taken, show feedback
    if next_step == "FEEDBACK":
        return "feedback"
    
    return "__end__"


def route_from_feedback(state: AgentEdState) -> Literal["content", "study_plan", "__end__"]:
    """
    Route after feedback agent completes.
    
    User might want to:
    - Review content → content agent
    - Update study plan → study_plan agent
    - End workflow
    """
    next_step = state.get("next_step", "END").upper()
    
    if next_step == "CONTENT":
        return "content"
    if next_step == "PLAN":
        return "study_plan"
    
    return "__end__"