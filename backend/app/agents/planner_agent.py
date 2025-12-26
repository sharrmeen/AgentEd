# backend/app/agents/study_plan_agent.py

"""
Study Plan Agent (Refactored) - Wraps PlannerService.

Responsibilities:
- Generate optimized study plans from syllabus
- Parse user constraints (exam dates, study hours)
- Track progress and objectives
- Auto-replan when deadlines missed
- NO CHANGES to PlannerService
"""

import os
from bson import ObjectId
from typing import Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain.agents import create_react_agent
from langchain import hub

from app.agents.orchestration.state import AgentEdState
from app.services.planner_service import PlannerService
from app.services.subject_service import SubjectService
from app.services.syllabus_service import SyllabusService


# ============================
# LLM SETUP
# ============================

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.3,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)


# ============================
# TOOLS (Wrap PlannerService)
# ============================

async def generate_study_plan_tool(params: Dict) -> str:
    """
    Tool that calls PlannerService.generate_plan().
    
    Input: {user_id, subject_id, target_days, daily_hours}
    Output: Generated study plan summary
    """
    try:
        planner_state = await PlannerService.generate_plan(
            user_id=ObjectId(params["user_id"]),
            subject_id=ObjectId(params["subject_id"]),
            target_days=params.get("target_days", 30),
            daily_hours=params.get("daily_hours", 2.0)
        )
        
        # Get full plan
        subject = await SubjectService.get_subject_by_id(
            user_id=ObjectId(params["user_id"]),
            subject_id=ObjectId(params["subject_id"])
        )
        
        chapters = subject.plan.get("chapters", [])
        chapter_list = "\n".join([
            f"Chapter {ch['chapter_number']}: {ch['title']} ({ch['estimated_hours']}h)"
            for ch in chapters
        ])
        
        return f"""Study plan generated successfully!
Total Chapters: {planner_state.total_chapters}
Target Days: {planner_state.target_days}
Daily Hours: {planner_state.daily_hours}

Chapters:
{chapter_list}"""
    
    except Exception as e:
        return f"Error generating plan: {str(e)}"


async def check_progress_tool(params: Dict) -> str:
    """
    Tool that checks study progress.
    
    Input: {user_id, subject_id}
    Output: Current progress summary
    """
    try:
        planner_state = await PlannerService.get_planner_state(
            user_id=ObjectId(params["user_id"]),
            subject_id=ObjectId(params["subject_id"])
        )
        
        if not planner_state:
            return "No study plan found. Generate one first."
        
        completed = len(planner_state.completed_chapters)
        total = planner_state.total_chapters
        percent = planner_state.completion_percent
        
        return f"""Progress Report:
Completed: {completed}/{total} chapters ({percent}%)
Current Chapter: {planner_state.current_chapter}
Next Suggestion: {planner_state.next_suggestion}"""
    
    except Exception as e:
        return f"Error checking progress: {str(e)}"


async def mark_objective_tool(params: Dict) -> str:
    """
    Tool that marks objectives complete.
    
    Input: {user_id, subject_id, chapter_number, objective}
    Output: Update result with auto-replan notification
    """
    try:
        result = await PlannerService.mark_objective_complete(
            user_id=ObjectId(params["user_id"]),
            subject_id=ObjectId(params["subject_id"]),
            chapter_number=params["chapter_number"],
            objective=params["objective"]
        )
        
        message = "✅ Objective marked complete."
        
        if result["chapter_completed"]:
            message += "\n🎉 Chapter completed! All objectives done."
        
        if result["replanned"]:
            message += "\n⚠️ Deadline missed. Plan automatically adjusted."
        
        return message
    
    except Exception as e:
        return f"Error marking objective: {str(e)}"


# Wrap tools for LangChain
study_plan_tool = Tool(
    name="generate_study_plan",
    description="""Generate an optimized study plan from syllabus.
    Input: JSON with user_id, subject_id, target_days (int), daily_hours (float).
    Use this when user wants to create or regenerate a study plan.""",
    func=generate_study_plan_tool
)

progress_tool = Tool(
    name="check_progress",
    description="""Check current study progress.
    Input: JSON with user_id, subject_id.
    Use this when user asks about their progress, status, or completion.""",
    func=check_progress_tool
)

objective_tool = Tool(
    name="mark_objective_complete",
    description="""Mark a learning objective as complete.
    Input: JSON with user_id, subject_id, chapter_number (int), objective (str).
    Use this when user has completed a specific objective or topic.""",
    func=mark_objective_tool
)


# ============================
# AGENT NODE
# ============================

async def study_plan_node(state: AgentEdState) -> Dict:
    """
    LangGraph node for study planning.
    
    Uses LangChain ReAct agent with PlannerService tools.
    """
    
    print("--- 📅 STUDY PLAN AGENT: Working... ---")
    
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
    
    # Extract constraints from state or query
    constraints = state.get("constraints", {})
    target_days = constraints.get("target_days", 30)
    daily_hours = constraints.get("daily_hours", 2.0)
    
    # Build context for agent
    context = f"""
User Query: {query}
Subject ID: {subject_id}
Target Days: {target_days}
Daily Hours: {daily_hours}

Available Information:
- Syllabus: {"✅ Available" if syllabus else "❌ Not loaded"}

Your task: Help the user with their study planning request.
"""
    
    # Create ReAct agent
    prompt = hub.pull("hwchase17/react")
    
    agent = create_react_agent(
        llm=llm,
        tools=[study_plan_tool, progress_tool, objective_tool],
        prompt=prompt
    )
    
    try:
        # Run agent
        from langchain.agents import AgentExecutor
        
        executor = AgentExecutor(
            agent=agent,
            tools=[study_plan_tool, progress_tool, objective_tool],
            verbose=True,
            handle_parsing_errors=True
        )
        
        result = await executor.ainvoke({
            "input": context,
            "agent_scratchpad": ""
        })
        
        agent_output = result.get("output", "I couldn't complete that task.")
        
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
        return {
            "errors": [f"Study Plan Agent: {str(e)}"],
            "messages": ["Sorry, I couldn't process your planning request."],
            "next_step": "END",
            "workflow_complete": True
        }