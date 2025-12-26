# backend/app/agents/feedback_agent.py

"""
Feedback Agent (Refactored) - Pedagogical Mentor.

Responsibilities:
- Analyze quiz performance
- Identify strengths and weak areas
- Provide targeted revision suggestions
- Link feedback to source materials
- Context-aware motivational cues
"""

import os
from bson import ObjectId
from typing import Dict, List
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.agents.orchestration.state import AgentEdState
from app.services.planner_service import PlannerService


# ============================
# LLM SETUP
# ============================

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.6,  # More creative for motivational messages
    google_api_key=os.getenv("GOOGLE_API_KEY")
)


# ============================
# OUTPUT SCHEMA
# ============================

class FeedbackReport(BaseModel):
    """Comprehensive feedback report."""
    overall_score: float
    performance_level: str  # "excellent" | "good" | "needs_improvement"
    
    performance_summary: str
    strengths: List[str] = Field(min_items=1)
    weak_areas: List[str] = Field(min_items=0)
    
    revision_tips: List[str] = Field(min_items=1)
    recommended_resources: List[str] = Field(default_factory=list)
    
    motivational_message: str
    next_steps: List[str] = Field(min_items=1)


# ============================
# AGENT NODE
# ============================

async def feedback_agent_node(state: AgentEdState) -> Dict:
    """
    LangGraph node for performance feedback.
    
    Steps:
    1. Analyze quiz results
    2. Calculate performance metrics
    3. Get progress context from PlannerService
    4. Generate personalized feedback with LLM
    5. Provide actionable next steps
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
        # -------------------------
        # 1️⃣ Calculate Performance
        # -------------------------
        total_questions = len(quiz_questions)
        correct_count = 0
        incorrect_topics = []
        correct_topics = []
        
        for i, question in enumerate(quiz_questions, 1):
            user_answer = quiz_results.get(f"q{i}")
            correct_answer = question.get("correct_answer")
            
            if user_answer == correct_answer:
                correct_count += 1
                correct_topics.append(question.get("question_text", ""))
            else:
                incorrect_topics.append({
                    "question": question.get("question_text", ""),
                    "your_answer": user_answer,
                    "correct_answer": correct_answer,
                    "explanation": question.get("explanation", "")
                })
        
        score_percent = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Determine performance level
        if score_percent >= 80:
            performance_level = "excellent"
            emoji = "🎉"
        elif score_percent >= 60:
            performance_level = "good"
            emoji = "👍"
        else:
            performance_level = "needs_improvement"
            emoji = "💪"
        
        # -------------------------
        # 2️⃣ Get Progress Context
        # -------------------------
        progress_context = ""
        if subject_id:
            try:
                planner_state = await PlannerService.get_planner_state(
                    user_id=ObjectId(user_id),
                    subject_id=ObjectId(subject_id)
                )
                
                if planner_state:
                    completed = len(planner_state.completed_chapters)
                    total = planner_state.total_chapters
                    percent = planner_state.completion_percent
                    
                    progress_context = f"""
Overall Progress:
- Completed: {completed}/{total} chapters ({percent}%)
- Current Chapter: {planner_state.current_chapter}
- Study Pace: {"On track" if percent > 0 else "Just started"}
"""
            except:
                pass
        
        # -------------------------
        # 3️⃣ Generate Feedback with LLM
        # -------------------------
        parser = PydanticOutputParser(pydantic_object=FeedbackReport)
        
        # Format incorrect questions for prompt
        weak_areas_text = "\n".join([
            f"- {item['question']}\n  Your answer: {item['your_answer']}\n  Correct: {item['correct_answer']}"
            for item in incorrect_topics[:5]  # Show top 5
        ]) if incorrect_topics else "None - all answers correct!"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an empathetic academic mentor providing performance feedback.

REQUIREMENTS:
- Be encouraging yet honest
- Identify specific concepts to review
- Provide actionable revision tips
- Link suggestions to specific topics
- Include motivational message appropriate to performance level
- Suggest concrete next steps

Quiz Performance:
- Score: {score}%
- Correct: {correct}/{total}
- Performance Level: {level}

Questions Missed:
{weak_areas}

{progress_context}

{format_instructions}

Generate comprehensive, motivating feedback."""),
            ("human", "Provide the feedback report now.")
        ])
        
        chain = prompt | llm
        
        response = await chain.ainvoke({
            "score": round(score_percent, 1),
            "correct": correct_count,
            "total": total_questions,
            "level": performance_level,
            "weak_areas": weak_areas_text,
            "progress_context": progress_context,
            "format_instructions": parser.get_format_instructions()
        })
        
        # Parse structured output
        feedback_output = parser.parse(response.content)
        
        # -------------------------
        # 4️⃣ Format Response
        # -------------------------
        feedback_dict = feedback_output.model_dump()
        
        # Create user-friendly message
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
                "level": performance_level,
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
            "messages": ["Sorry, I couldn't generate feedback. Try again later."],
            "next_step": "END",
            "workflow_complete": True
        }