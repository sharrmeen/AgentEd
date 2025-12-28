# backend/app/agents/feedback_agent.py

"""
Feedback Agent - LangChain v1 - Pedagogical Mentor (Full Agent)

Responsibilities:
- Analyze quiz performance and identify weak areas
- Retrieve source materials for weak topics
- Provide targeted revision suggestions linked to materials
- Generate context-aware motivational cues
- Track progress and learning patterns
"""

import os
from bson import ObjectId
from typing import Dict, List
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.agents.orchestration.state import AgentEdState
from app.services.planner_service import PlannerService
from app.services.retrieval import RetrievalService

from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.6,
    google_api_key=os.getenv("GEMINI_API_KEY")
)


# ============================
# OUTPUT SCHEMA
# ============================

class FeedbackReport(BaseModel):
    """Comprehensive feedback report."""
    overall_score: float
    performance_level: str
    performance_summary: str
    strengths: List[str] = Field(min_items=1)
    weak_areas: List[str] = Field(min_items=0)
    revision_tips: List[str] = Field(min_items=1)
    recommended_resources: List[str] = Field(default_factory=list)
    motivational_message: str
    next_steps: List[str] = Field(min_items=1)


# ============================
# TOOLS (Feedback Agent collaborates with these)
# ============================

@tool
def get_student_progress(user_id: str, subject_id: str) -> str:
    """Get overall learning progress to contextualize feedback."""
    try:
        import asyncio
        
        planner_state = asyncio.run(
            PlannerService.get_planner_state(
                user_id=ObjectId(user_id),
                subject_id=ObjectId(subject_id)
            )
        )
        
        if not planner_state:
            return "No study plan found."
        
        completed = len(planner_state.completed_chapters)
        total = planner_state.total_chapters
        percent = planner_state.completion_percent
        
        return f"""Student Progress:
- Overall Progress: {completed}/{total} chapters ({percent}%)
- Current Chapter: {planner_state.current_chapter}
- Study Pace: {"On track" if percent > 0 else "Just started"}
- Chapters Completed: {completed}
- Remaining Chapters: {total - completed}"""
    
    except Exception as e:
        return f"Error getting progress: {str(e)}"


@tool
def retrieve_weak_topic_materials(topic: str, user_id: str, subject: str = None) -> str:
    """Retrieve curriculum materials for weak areas to provide targeted revision."""
    try:
        retrieval_service = RetrievalService()
        
        results = retrieval_service.query(
            question=f"Detailed explanation of {topic}",
            user_id=user_id,
            subject=subject,
            k=5
        )
        
        if not results:
            return f"No materials found for {topic}."
        
        formatted = []
        for i, doc in enumerate(results, 1):
            metadata = doc.get("metadata", {})
            formatted.append(
                f"Resource {i}:\n{doc['content']}\n"
                f"(Source: {metadata.get('source_file', 'Unknown')})"
            )
        
        return "\n\n".join(formatted)
    
    except Exception as e:
        return f"Error retrieving materials: {str(e)}"


@tool
def analyze_performance_pattern(quiz_results: str, total_questions: int, correct_count: int) -> str:
    """Analyze performance patterns to identify learning trends."""
    try:
        percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        if percentage >= 80:
            pattern = "STRONG - Excellent mastery of concepts"
        elif percentage >= 60:
            pattern = "GOOD - Solid understanding with some gaps"
        else:
            pattern = "NEEDS IMPROVEMENT - Requires focused revision"
        
        return f"""Performance Analysis:
- Score: {percentage:.1f}%
- Correct Answers: {correct_count}/{total_questions}
- Performance Pattern: {pattern}
- Learning Trend: Based on performance, student needs focused revision on weak areas"""
    
    except Exception as e:
        return f"Error analyzing performance: {str(e)}"


tools = [get_student_progress, retrieve_weak_topic_materials, analyze_performance_pattern]


# ============================
# AGENT NODE
# ============================

async def feedback_agent_node(state: AgentEdState) -> Dict:
    """
    Feedback Agent - Full Agent for pedagogical mentoring.
    
    Collaborates with other agents to provide comprehensive feedback.
    INPUT/OUTPUT: Unchanged - fully compatible
    """
    
    print("--- 💬 FEEDBACK AGENT: Working... ---")
    
    user_id = state["user_id"]
    subject_id = state.get("subject_id")
    
    quiz_questions = state.get("quiz", [])
    quiz_results = state.get("quiz_results", {})
    
    if not quiz_questions or not quiz_results:
        return {
            "messages": ["Complete a quiz first to receive feedback."],
            "next_step": "END",
            "workflow_complete": True
        }
    
    try:
        # Calculate performance metrics
        total_questions = len(quiz_questions)
        correct_count = 0
        incorrect_topics = []
        
        for i, question in enumerate(quiz_questions, 1):
            user_answer = quiz_results.get(f"q{i}")
            correct_answer = question.get("correct_answer")
            
            if user_answer == correct_answer:
                correct_count += 1
            else:
                incorrect_topics.append(question.get("question_text", ""))
        
        score_percent = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Determine performance level
        if score_percent >= 80:
            emoji = "🎉"
        elif score_percent >= 60:
            emoji = "👍"
        else:
            emoji = "💪"
        
        # Create agent to analyze and provide feedback
        system_prompt = f"""You are a Pedagogical Mentor providing comprehensive performance feedback.

Quiz Performance: {score_percent:.1f}% ({correct_count}/{total_questions} correct)
Weak Topics: {", ".join(incorrect_topics[:3]) if incorrect_topics else "None"}

Your responsibilities:
1. Use get_student_progress to understand overall learning context
2. Use retrieve_weak_topic_materials for topics where student struggled
3. Use analyze_performance_pattern to identify learning trends
4. Provide targeted, material-linked revision suggestions
5. Offer context-aware motivational messaging
6. Suggest concrete next steps for improvement

Generate comprehensive, encouraging, and actionable feedback."""

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt
        )
        
        # Invoke agent to gather feedback context
        weak_topics_str = ", ".join(incorrect_topics[:5]) if incorrect_topics else "None"
        
        result = agent.invoke({
            "messages": [{
                "role": "user",
                "content": f"""Analyze this quiz performance and provide feedback:
- Score: {score_percent:.1f}%
- Correct: {correct_count}/{total_questions}
- Weak Areas: {weak_topics_str}

Provide comprehensive feedback with specific revision suggestions."""
            }]
        })
        
        # Extract agent's analysis
        if isinstance(result, dict) and "messages" in result:
            last_message = result["messages"][-1]
            agent_analysis = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            agent_analysis = getattr(result, "content", "No response")
        
        # Now generate structured feedback
        parser = PydanticOutputParser(pydantic_object=FeedbackReport)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an empathetic academic mentor generating structured feedback.

{format_instructions}

Based on performance analysis, generate comprehensive feedback with:
- Clear performance summary
- Specific strengths
- Identified weak areas
- Material-linked revision tips
- Motivational message appropriate to performance level
- Concrete next steps

Return as JSON."""),
            ("human", f"""Based on this analysis:

{agent_analysis}

Generate structured feedback report.""")
        ])
        
        chain = prompt | llm
        
        response = await chain.ainvoke({
            "format_instructions": parser.get_format_instructions()
        })
        
        feedback_output = parser.parse(response.content)
        feedback_dict = feedback_output.model_dump()
        
        # Format message
        message = f"""{emoji} Quiz Results: {score_percent:.1f}% ({correct_count}/{total_questions})

{feedback_output.performance_summary}

💪 Strengths:
{chr(10).join(f"  • {s}" for s in feedback_output.strengths)}

📚 Areas to Review:
{chr(10).join(f"  • {w}" for w in feedback_output.weak_areas) if feedback_output.weak_areas else "  • Great job! No major gaps."}

📝 Revision Tips:
{chr(10).join(f"  • {t}" for t in feedback_output.revision_tips)}

🎯 Next Steps:
{chr(10).join(f"  • {n}" for n in feedback_output.next_steps)}

💡 {feedback_output.motivational_message}"""
        
        return {
            "feedback": feedback_dict,
            "quiz_score": score_percent,
            "performance_analysis": {
                "correct": correct_count,
                "total": total_questions,
                "percent": score_percent,
                "level": "excellent" if score_percent >= 80 else "good" if score_percent >= 60 else "needs_improvement",
                "incorrect_topics": incorrect_topics
            },
            "messages": [message],
            "next_step": "END",
            "agent_trace": ["feedback"],
            "workflow_complete": True
        }
    
    except Exception as e:
        print(f"❌ Feedback Agent Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "errors": [f"Feedback Agent: {str(e)}"],
            "messages": ["Sorry, I couldn't generate feedback."],
            "next_step": "END",
            "workflow_complete": True
        }