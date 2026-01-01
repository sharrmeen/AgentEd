# backend/app/agents/orchestration/workflow.py

"""
LangGraph Workflow - Updated for Full Agent System.

Includes error handling, execution tracking, and validation.
"""

from langgraph.graph import StateGraph, END
from datetime import datetime
import uuid
import time

from app.agents.orchestration.state import AgentEdState
from app.agents.orchestration.router import (
    route_supervisor,
    route_from_study_plan,
    route_from_content,
    route_from_quiz,
    route_from_feedback,
    validate_quiz_execution,
    validate_feedback_execution
)

from app.agents.planner_agent import study_plan_node
from app.agents.resource_agent import resource_agent_node
from app.agents.quiz_agent import quiz_agent_node
from app.agents.feedback_agent import feedback_agent_node


# ============================
# WRAPPER FUNCTIONS - Add execution tracking & error handling
# ============================

async def study_plan_node_wrapped(state: AgentEdState) -> dict:
    """Wrapped study plan node with error handling and status tracking."""
    try:
        start_time = time.time()
        result = await study_plan_node(state)
        execution_time = time.time() - start_time
        
        # Track execution time
        execution_times = state.get("execution_times", {})
        execution_times["study_plan"] = execution_time
        result["execution_times"] = execution_times
        
        print(f"✅ Study Plan Agent completed in {execution_time:.2f}s")
        return result
    
    except Exception as e:
        print(f"❌ Study Plan Agent failed: {e}")
        
        errors = state.get("errors", [])
        errors.append(f"Study Plan Agent: {str(e)}")
        
        return {
            "errors": errors,
            "messages": ["Study plan generation failed. Please try again."],
            "next_step": "END",
            "workflow_complete": True,
            "agent_trace": ["study_plan_error"]
        }


async def resource_agent_node_wrapped(state: AgentEdState) -> dict:
    """Wrapped resource agent with error handling and status tracking."""
    print("🔥🔥🔥 RESOURCE_AGENT_NODE_WRAPPED CALLED 🔥🔥🔥", flush=True)
    try:
        start_time = time.time()
        print(f"🔥 About to call resource_agent_node...", flush=True)
        result = await resource_agent_node(state)
        print(f"🔥 resource_agent_node returned", flush=True)
        execution_time = time.time() - start_time
        
        execution_times = state.get("execution_times", {})
        execution_times["resource"] = execution_time
        result["execution_times"] = execution_times
        
        print(f"✅ Resource Agent completed in {execution_time:.2f}s")
        return result
    
    except Exception as e:
        print(f"❌ Resource Agent failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
        
        errors = state.get("errors", [])
        errors.append(f"Resource Agent: {str(e)}")
        
        return {
            "errors": errors,
            "messages": ["Content retrieval failed. Please try again."],
            "next_step": "END",
            "workflow_complete": True,
            "agent_trace": ["resource_error"]
        }


async def quiz_agent_node_wrapped(state: AgentEdState) -> dict:
    """
    Wrapped quiz agent with error handling and status tracking.
    UPDATED: Sets generation_status for router validation.
    """
    try:
        start_time = time.time()
        result = await quiz_agent_node(state)
        execution_time = time.time() - start_time
        
        execution_times = state.get("execution_times", {})
        execution_times["quiz"] = execution_time
        result["execution_times"] = execution_times
        
        # Set generation status for router
        if result.get("quiz") and len(result.get("quiz", [])) > 0:
            result["quiz_generation_status"] = "success"
            print(f"✅ Quiz Agent completed in {execution_time:.2f}s")
        else:
            result["quiz_generation_status"] = "failed"
            print(f"⚠️ Quiz Agent completed but generated no questions")
        
        return result
    
    except Exception as e:
        print(f"❌ Quiz Agent failed: {e}")
        
        errors = state.get("errors", [])
        errors.append(f"Quiz Agent: {str(e)}")
        
        return {
            "errors": errors,
            "messages": ["Quiz generation failed. Please try again."],
            "quiz_generation_status": "failed",
            "next_step": "END",
            "workflow_complete": True,
            "agent_trace": ["quiz_error"]
        }


async def feedback_agent_node_wrapped(state: AgentEdState) -> dict:
    """
    Wrapped feedback agent with error handling and status tracking.
    UPDATED: Sets generation_status for router validation.
    """
    try:
        start_time = time.time()
        result = await feedback_agent_node(state)
        execution_time = time.time() - start_time
        
        execution_times = state.get("execution_times", {})
        execution_times["feedback"] = execution_time
        result["execution_times"] = execution_times
        
        # Set generation status for router
        if result.get("feedback"):
            result["feedback_generation_status"] = "success"
            print(f"✅ Feedback Agent completed in {execution_time:.2f}s")
        else:
            result["feedback_generation_status"] = "failed"
            print(f"⚠️ Feedback Agent completed but generated no feedback")
        
        return result
    
    except Exception as e:
        print(f"❌ Feedback Agent failed: {e}")
        
        errors = state.get("errors", [])
        errors.append(f"Feedback Agent: {str(e)}")
        
        return {
            "errors": errors,
            "messages": ["Feedback generation failed. Please try again."],
            "feedback_generation_status": "failed",
            "next_step": "END",
            "workflow_complete": True,
            "agent_trace": ["feedback_error"]
        }


# ============================
# BUILD WORKFLOW GRAPH
# ============================

def build_workflow() -> StateGraph:
    """Build LangGraph with error handling and execution tracking."""
    
    workflow = StateGraph(AgentEdState)
    
    # Add nodes (wrapped with error handling)
    workflow.add_node("study_plan", study_plan_node_wrapped)
    workflow.add_node("content", resource_agent_node_wrapped)
    workflow.add_node("quiz", quiz_agent_node_wrapped)
    workflow.add_node("feedback", feedback_agent_node_wrapped)
    
    # Set entry point
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
    
    # Define edges (with validation)
    workflow.add_conditional_edges(
        "study_plan",
        route_from_study_plan,
        {
            "content": "content",
            "quiz": "quiz",
            "__end__": END
        }
    )
    
    workflow.add_conditional_edges(
        "content",
        route_from_content,
        {
            "quiz": "quiz",
            "study_plan": "study_plan",
            "__end__": END
        }
    )
    
    workflow.add_conditional_edges(
        "quiz",
        route_from_quiz,
        {
            "feedback": "feedback",
            "__end__": END
        }
    )
    
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


# Compile workflow
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
    intent: str = "answer",
    constraints: dict = None,
    quiz_results: dict = None,
    **kwargs
) -> dict:
    """
    Execute the complete multi-agent workflow.
    
    Args:
        user_id: User identifier
        user_query: User's question/query
        subject_id: Subject context
        chapter_number: Chapter context
        session_id: Session identifier
        intent: Intent type - 'answer' (default) | 'explain' | 'summarize'
        constraints: Planning constraints
        quiz_results: Quiz results data
        
    Returns:
        Workflow result with answer, metadata, and execution info
    """
    
    initial_state = AgentEdState(
        user_id=user_id,
        user_query=user_query,
        intent=intent,
        subject_id=subject_id,
        subject_name=None,
        chapter_number=chapter_number,
        session_id=session_id,
        syllabus=None,
        constraints=constraints or {},
        study_plan=None,
        planner_state=None,
        current_topic=None,
        content=None,
        retrieved_docs=None,
        web_search_results=None,
        answer=None,
        quiz=None,
        quiz_metadata=None,
        quiz_results=quiz_results,
        quiz_score=None,
        feedback=None,
        performance_analysis=None,
        messages=[],
        chat_history=None,
        next_step="",
        workflow_complete=False,
        errors=[],
        tool_execution_log=[],
        agent_error_log=[],
        timestamp=datetime.utcnow().isoformat(),
        workflow_id=str(uuid.uuid4()),
        agent_trace=[],
        execution_times={},
        **kwargs
    )
    
    print(f"\n{'='*70}")
    print(f"🚀 AGENT WORKFLOW STARTED")
    print(f"   Query: {user_query}")
    print(f"   Workflow ID: {initial_state['workflow_id']}")
    print(f"{'='*70}\n")
    
    try:
        final_state = await agent_graph.ainvoke(initial_state)
        
        print(f"\n{'='*70}")
        print(f"✅ WORKFLOW COMPLETE")
        print(f"   Agents Called: {', '.join(final_state.get('agent_trace', []))}")
        print(f"   Messages: {len(final_state.get('messages', []))}")
        print(f"   Errors: {len(final_state.get('errors', []))}")
        
        # Print execution times
        exec_times = final_state.get("execution_times", {})
        if exec_times:
            print(f"   Execution Times:")
            for agent, time_taken in exec_times.items():
                print(f"     - {agent}: {time_taken:.2f}s")
        
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