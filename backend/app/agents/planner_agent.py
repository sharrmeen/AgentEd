# backend/app/agents/planner_agent.py

"""
Study Plan Agent - LangChain v1 Compatible (Official Migration)

Uses langchain.agents.create_agent instead of deprecated patterns.
"""

import os
import json
from bson import ObjectId
from typing import Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.tools import tool

from app.agents.orchestration.state import AgentEdState
from app.services.planner_service import PlannerService
from app.services.subject_service import SubjectService
from app.services.syllabus_service import SyllabusService

from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.3,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# ============================
# CORE FUNCTION (SERVICE-SAFE, NO TOOLS)
# =============================

async def generate_study_plan_core(
    *,
    syllabus_text: str,
    subject_name: str,
    target_days: int,
    daily_hours: float,
    user_preferences: Dict
) -> Dict:
    """
    Core planner logic - called by services, not by agent.
    This is pure, deterministic, and LLM-free.
    """
    # Placeholder: In production, integrate with LLM for chapter generation
    return {
        "meta": {
            "total_hours": target_days * daily_hours
        },
        "chapters": user_preferences.get("chapters_override", [])
    }


# ============================
# TOOLS (LLM-FACING ONLY)
# ============================

@tool
def generate_study_plan(user_id: str, subject_id: str, target_days: int = 30, daily_hours: float = 2.0) -> str:
    """Generate an optimized study plan from syllabus."""
    try:
        import asyncio
        
        result = asyncio.run(
            PlannerService.generate_plan(
                user_id=ObjectId(user_id),
                subject_id=ObjectId(subject_id),
                target_days=target_days,
                daily_hours=daily_hours
            )
        )
        
        subject = asyncio.run(
            SubjectService.get_subject_by_id(
                user_id=ObjectId(user_id),
                subject_id=ObjectId(subject_id)
            )
        )
        
        # Handle both Pydantic model and dict
        subject_plan = subject.plan if hasattr(subject, 'plan') else subject.get('plan', {})
        chapters = subject_plan.get("chapters", []) if isinstance(subject_plan, dict) else []
        chapter_list = "\n".join([
            f"Chapter {ch['chapter_number']}: {ch['title']} ({ch['estimated_hours']}h)"
            for ch in chapters
        ])
        
        # Handle both Pydantic model and dict
        total_chapters = result.total_chapters if hasattr(result, 'total_chapters') else result.get('total_chapters')
        target = result.target_days if hasattr(result, 'target_days') else result.get('target_days')
        hours = result.daily_hours if hasattr(result, 'daily_hours') else result.get('daily_hours')
        
        return f"""✅ Study plan generated successfully!
Total Chapters: {total_chapters}
Target Days: {target}
Daily Hours: {hours}

Chapters:
{chapter_list}"""
    
    except Exception as e:
        return f"❌ Error generating plan: {str(e)}"


@tool
def check_progress(user_id: str, subject_id: str) -> str:
    """Check current study progress."""
    try:
        import asyncio
        
        result = asyncio.run(
            PlannerService.get_planner_state(
                user_id=ObjectId(user_id),
                subject_id=ObjectId(subject_id)
            )
        )
        
        if not result:
            return "❌ No study plan found. Generate one first."
        
        # Handle both Pydantic model and dict
        completed_chapters = result.completed_chapters if hasattr(result, 'completed_chapters') else result.get('completed_chapters', [])
        total_chapters = result.total_chapters if hasattr(result, 'total_chapters') else result.get('total_chapters')
        completion_percent = result.completion_percent if hasattr(result, 'completion_percent') else result.get('completion_percent')
        current_chapter = result.current_chapter if hasattr(result, 'current_chapter') else result.get('current_chapter')
        next_suggestion = result.next_suggestion if hasattr(result, 'next_suggestion') else result.get('next_suggestion')
        
        completed = len(completed_chapters)
        
        return f"""📊 Progress Report:
Completed: {completed}/{total_chapters} chapters ({completion_percent}%)
Current Chapter: {current_chapter}
Next Suggestion: {next_suggestion}"""
    
    except Exception as e:
        return f"❌ Error checking progress: {str(e)}"


@tool
def mark_objective_complete(user_id: str, subject_id: str, chapter_number: int, objective: str) -> str:
    """Mark a learning objective as complete."""
    try:
        import asyncio
        
        result = asyncio.run(
            PlannerService.mark_objective_complete(
                user_id=ObjectId(user_id),
                subject_id=ObjectId(subject_id),
                chapter_number=chapter_number,
                objective=objective
            )
        )
        
        message = "✅ Objective marked complete."
        
        # Handle both dict and Pydantic model
        chapter_completed = result.get("chapter_completed") if isinstance(result, dict) else result.chapter_completed
        replanned = result.get("replanned") if isinstance(result, dict) else result.replanned
        
        if chapter_completed:
            message += "\n🎉 Chapter completed! All objectives done."
        
        if replanned:
            message += "\n⚠️ Deadline missed. Plan automatically adjusted."
        
        return message
    
    except Exception as e:
        return f"Error marking objective: {str(e)}"


tools = [generate_study_plan, check_progress, mark_objective_complete]


# ============================
# AGENT NODE
# ============================

async def study_plan_node(state: AgentEdState) -> Dict:
    """
    LangGraph node for study planning.
    Uses official LangChain v1 create_agent.
    INPUT/OUTPUT: Unchanged - fully compatible
    """
    
    print("--- 📋 STUDY PLAN AGENT: Working... ---")
    
    user_id = state["user_id"]
    subject_id = state.get("subject_id")
    query = state["user_query"]
    
    # Get syllabus if available
    syllabus = state.get("syllabus")
    if not syllabus and subject_id:
        try:
            syl = await SyllabusService.get_by_subject_id(
                user_id=ObjectId(user_id),
                subject_id=ObjectId(subject_id)
            )
            syllabus = syl.raw_text if syl else None
        except:
            pass
    
    constraints = state.get("constraints", {})
    target_days = constraints.get("target_days", 30)
    daily_hours = constraints.get("daily_hours", 2.0)
    
    try:
        # Build system prompt (official v1 way)
        system_prompt = f"""You are a helpful study planning assistant.

User Query: {query}
Subject ID: {subject_id or "Not specified"}
Target Days: {target_days}
Daily Hours: {daily_hours}
Syllabus Available: {"✅ Available" if syllabus else "❌ Not loaded"}

Help the user with their study planning request using available tools."""

        # Create agent using official v1 API
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt
        )
        
        # Invoke agent
        result = agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        
        # Extract output 
        if isinstance(result, dict) and "messages" in result:
            last_message = result["messages"][-1]
            agent_output = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            agent_output = getattr(result, "content", "No response")
        
        # Fetch updated planner state
        planner_state_dict = None
        if subject_id:
            try:
                planner = await PlannerService.get_planner_state(
                    user_id=ObjectId(user_id),
                    subject_id=ObjectId(subject_id)
                )
                if planner:
                    planner_state_dict = planner.model_dump()
            except:
                pass
        
        # Determine next step
        next_step = "END"
        if "quiz" in query.lower() or "test" in query.lower():
            next_step = "QUIZ"
        elif "explain" in query.lower() or "what is" in query.lower():
            next_step = "CONTENT"
        
        return {
            "planner_state": planner_state_dict,
            "messages": [agent_output],
            "next_step": next_step,
            "agent_trace": ["study_plan"],
            "workflow_complete": (next_step == "END")
        }
    
    except Exception as e:
        print(f"❌ Study Plan Agent Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "errors": [f"Study Plan Agent: {str(e)}"],
            "messages": ["Sorry, I couldn't process your planning request."],
            "next_step": "END",
            "workflow_complete": True
        }