# backend/app/agents/orchestration/workflow.py

"""
LangGraph Workflow (Refactored) - Production-Ready Orchestration.

Integrates all agents:
- Study Plan Agent (PlannerService wrapper)
- Resource Agent (RetrievalService + Tavily wrapper)
- Quiz Agent (content-based quiz generation)
- Feedback Agent (performance analysis)

NO CHANGES to existing services required.
"""

from langgraph.graph import StateGraph, END
from datetime import datetime
import uuid

from app.agents.orchestration.state import AgentEdState
from app.agents.orchestration.router import (
    route_supervisor,
    route_from_study_plan,
    route_from_content,
    route_from_quiz,
    route_from_feedback
)

# Import agent nodes
from app.agents.planner_agent import study_plan_node
from app.agents.resource_agent import resource_agent_node
from app.agents.quiz_agent import quiz_agent_node
from app.agents.feedback_agent import feedback_agent_node


# ============================
# BUILD WORKFLOW GRAPH
# ============================

def build_workflow() -> StateGraph:

    
    # Initialize workflow with state schema
    workflow = StateGraph(AgentEdState)
    
    # -------------------------
    # Add Agent Nodes
    # -------------------------
    workflow.add_node("study_plan", study_plan_node)
    workflow.add_node("content", resource_agent_node)
    workflow.add_node("quiz", quiz_agent_node)
    workflow.add_node("feedback", feedback_agent_node)
    
    # -------------------------
    # Set Entry Point (Router)
    # -------------------------
    workflow.set_conditional_entry_point(
        route_supervisor,
        {
            "study_plan": "study_plan",
            "content": "content",
            "quiz": "quiz",
            "feedback": "feedback",
            "__end__": END
        }
    )
    
    # -------------------------
    # Define Edges (Agent → Router → Next Agent)
    # -------------------------
    
    # From Study Plan Agent
    workflow.add_conditional_edges(
        "study_plan",
        route_from_study_plan,
        {
            "content": "content",
            "quiz": "quiz",
            "__end__": END
        }
    )
    
    # From Resource Agent
    workflow.add_conditional_edges(
        "content",
        route_from_content,
        {
            "quiz": "quiz",
            "study_plan": "study_plan",
            "__end__": END
        }
    )
    
    # From Quiz Agent
    workflow.add_conditional_edges(
        "quiz",
        route_from_quiz,
        {
            "feedback": "feedback",
            "__end__": END
        }
    )
    
    # From Feedback Agent
    workflow.add_conditional_edges(
        "feedback",
        route_from_feedback,
        {
            "content": "content",
            "study_plan": "study_plan",
            "__end__": END
        }
    )
    
    return workflow


# Compile workflow (singleton)
agent_graph = build_workflow().compile()


# ============================
# PUBLIC API
# ============================

async def run_workflow(
    user_id: str,
    user_query: str,
    subject_id: str = None,
    chapter_number: int = None,
    session_id: str = None,
    constraints: dict = None,
    quiz_results: dict = None,
    **kwargs
) -> dict:
    """
    Execute the complete agent workflow.
    
    This is the main entry point for the agent system.
    
    Args:
        user_id: MongoDB ObjectId as string
        user_query: Natural language input
        subject_id: Optional subject context
        chapter_number: Optional chapter context
        session_id: Optional session for cache
        constraints: Optional planning constraints {target_days, daily_hours}
        quiz_results: Optional quiz answers {q1: "B", q2: "A", ...}
        **kwargs: Additional state fields
    
    Returns:
        Final state dict with agent responses
    
    Example:
        # Generate study plan
        result = await run_workflow(
            user_id="507f1f77bcf86cd799439011",
            user_query="Create a 30-day study plan",
            subject_id="507f1f77bcf86cd799439012",
            constraints={"target_days": 30, "daily_hours": 2}
        )
        
        # Ask question
        result = await run_workflow(
            user_id="507f1f77bcf86cd799439011",
            user_query="What is photosynthesis?",
            subject_id="507f1f77bcf86cd799439012",
            session_id="507f1f77bcf86cd799439013"
        )
        
        # Generate quiz
        result = await run_workflow(
            user_id="507f1f77bcf86cd799439011",
            user_query="Give me a quiz on chapter 2",
            subject_id="507f1f77bcf86cd799439012",
            chapter_number=2
        )
        
        # Get feedback
        result = await run_workflow(
            user_id="507f1f77bcf86cd799439011",
            user_query="Show my quiz results",
            subject_id="507f1f77bcf86cd799439012",
            quiz_results={"q1": "B", "q2": "A", "q3": "C"}
        )
    """
    
    # Initialize state
    initial_state = AgentEdState(
        # User context
        user_id=user_id,
        user_query=user_query,
        
        # Subject context
        subject_id=subject_id,
        subject_name=None,
        chapter_number=chapter_number,
        session_id=session_id,
        
        # Study Plan data
        syllabus=None,
        constraints=constraints or {},
        study_plan=None,
        planner_state=None,
        
        # Resource data
        current_topic=None,
        content=None,
        retrieved_docs=None,
        web_search_results=None,
        answer=None,
        
        # Quiz data
        quiz=None,
        quiz_metadata=None,
        quiz_results=quiz_results,
        quiz_score=None,
        
        # Feedback data
        feedback=None,
        performance_analysis=None,
        
        # Conversation
        messages=[],
        chat_history=None,
        
        # Control flow
        next_step="",
        workflow_complete=False,
        
        # Error handling
        errors=[],
        
        # Metadata
        timestamp=datetime.utcnow().isoformat(),
        workflow_id=str(uuid.uuid4()),
        agent_trace=[],
        
        **kwargs  # Allow additional fields
    )
    
    # Log workflow start
    print(f"\n{'='*70}")
    print(f"🚀 AGENT WORKFLOW STARTED")
    print(f"   Query: {user_query}")
    print(f"   Workflow ID: {initial_state['workflow_id']}")
    print(f"{'='*70}\n")
    
    # Execute workflow
    try:
        final_state = await agent_graph.ainvoke(initial_state)
        
        # Log completion
        print(f"\n{'='*70}")
        print(f"✅ WORKFLOW COMPLETE")
        print(f"   Agents Called: {', '.join(final_state.get('agent_trace', []))}")
        print(f"   Messages: {len(final_state.get('messages', []))}")
        print(f"   Errors: {len(final_state.get('errors', []))}")
        print(f"{'='*70}\n")
        
        return final_state
    
    except Exception as e:
        print(f"\n❌ WORKFLOW ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        
        return {
            **initial_state,
            "errors": [f"Workflow error: {str(e)}"],
            "messages": ["Sorry, something went wrong. Please try again."],
            "workflow_complete": True
        }


# ============================
# EXAMPLE USAGE
# ============================

async def test_workflow():
    """Test the workflow with various queries."""
    
    user_id = "507f1f77bcf86cd799439011"
    subject_id = "507f1f77bcf86cd799439012"
    
    print("\n" + "="*70)
    print("🧪 TESTING AGENT WORKFLOW")
    print("="*70)
    
    # Test 1: Study Planning
    print("\n📝 TEST 1: Generate Study Plan")
    print("-" * 70)
    result = await run_workflow(
        user_id=user_id,
        user_query="Create a 30-day study plan with 2 hours per day",
        subject_id=subject_id,
        constraints={"target_days": 30, "daily_hours": 2.0}
    )
    print(f"Response: {result['messages'][0] if result['messages'] else 'No response'}")
    
    # Test 2: Knowledge Question
    print("\n📚 TEST 2: Ask Question")
    print("-" * 70)
    result = await run_workflow(
        user_id=user_id,
        user_query="What is photosynthesis?",
        subject_id=subject_id,
        session_id="507f1f77bcf86cd799439013"
    )
    print(f"Response: {result['messages'][0] if result['messages'] else 'No response'}")
    
    # Test 3: Quiz Generation
    print("\n📝 TEST 3: Generate Quiz")
    print("-" * 70)
    result = await run_workflow(
        user_id=user_id,
        user_query="Create a quiz on chapter 1",
        subject_id=subject_id,
        chapter_number=1
    )
    print(f"Response: {result['messages'][0] if result['messages'] else 'No response'}")
    
    # Test 4: Feedback
    print("\n💬 TEST 4: Get Feedback")
    print("-" * 70)
    result = await run_workflow(
        user_id=user_id,
        user_query="Show my quiz results",
        subject_id=subject_id,
        quiz_results={"q1": "B", "q2": "A", "q3": "C", "q4": "A", "q5": "D"}
    )
    print(f"Response: {result['messages'][0] if result['messages'] else 'No response'}")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_workflow())