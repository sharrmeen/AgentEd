# backend/app/agents/quiz_agent.py

"""
Quiz Agent (Refactored) - Formative Assessor.

Responsibilities:
- Generate contextual quiz questions from study content
- Collaborate with Resource Agent for content retrieval
- Variety of question types (MCQ, short answer, true/false)
- Grounded in curriculum material
"""

import os
from bson import ObjectId
from typing import Dict, List
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.agents.orchestration.state import AgentEdState
from app.services.retrieval import RetrievalService
from app.services.subject_service import SubjectService


# ============================
# LLM SETUP
# ============================

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.4,  # Lower for structured output
    google_api_key=os.getenv("GOOGLE_API_KEY")
)


# ============================
# OUTPUT SCHEMA
# ============================

class QuizQuestion(BaseModel):
    """Single quiz question."""
    question_number: int
    question_text: str
    question_type: str  # "mcq" | "short_answer" | "true_false"
    options: List[str] = Field(default_factory=list)  # For MCQ
    correct_answer: str
    explanation: str
    marks: int = 1


class QuizOutput(BaseModel):
    """Complete quiz."""
    title: str
    topic: str
    total_marks: int
    questions: List[QuizQuestion]


# ============================
# AGENT NODE
# ============================

async def quiz_agent_node(state: AgentEdState) -> Dict:
    """
    LangGraph node for quiz generation.
    
    Steps:
    1. Get topic from state (current_topic or chapter)
    2. Retrieve content using RetrievalService
    3. Generate quiz with LLM (structured output)
    4. Return quiz in state
    """
    
    print("--- 📝 QUIZ AGENT: Working... ---")
    
    user_id = state["user_id"]
    subject_id = state.get("subject_id")
    chapter_number = state.get("chapter_number")
    current_topic = state.get("current_topic")
    
    # Determine topic
    topic = current_topic or f"Chapter {chapter_number}" if chapter_number else "General"
    
    try:
        # -------------------------
        # 1️⃣ Get Subject Context
        # -------------------------
        subject = None
        chapter_info = None
        
        if subject_id:
            subject = await SubjectService.get_subject_by_id(
                user_id=ObjectId(user_id),
                subject_id=ObjectId(subject_id)
            )
            
            # Get chapter details from plan
            if chapter_number and subject and subject.plan:
                chapters = subject.plan.get("chapters", [])
                chapter_info = next(
                    (ch for ch in chapters if ch.get("chapter_number") == chapter_number),
                    None
                )
                
                if chapter_info:
                    topic = chapter_info.get("title", topic)
        
        # -------------------------
        # 2️⃣ Retrieve Content (RAG)
        # -------------------------
        retrieval_service = RetrievalService()
        
        rag_results = retrieval_service.query(
            question=f"Content about {topic}",
            user_id=user_id,
            subject=subject.subject_name if subject else None,
            chapter=str(chapter_number) if chapter_number else None,
            k=10  # More context for quiz generation
        )
        
        if not rag_results:
            return {
                "errors": ["No content found for quiz generation. Upload notes first."],
                "messages": ["Please upload study materials before generating quizzes."],
                "next_step": "END",
                "workflow_complete": True
            }
        
        # Format context
        context = "\n\n".join([
            f"Source {i+1}:\n{doc['content']}"
            for i, doc in enumerate(rag_results)
        ])
        
        # Get learning objectives if available
        objectives = []
        if chapter_info:
            objectives = chapter_info.get("objectives", [])
        
        # -------------------------
        # 3️⃣ Generate Quiz with LLM
        # -------------------------
        parser = PydanticOutputParser(pydantic_object=QuizOutput)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert quiz creator. Generate a comprehensive quiz based on the provided content.

REQUIREMENTS:
- Create 5-8 questions covering the main concepts
- Mix question types: 60% MCQ, 30% short answer, 10% true/false
- Ensure questions test understanding, not just memorization
- Provide clear explanations for correct answers
- Questions should be challenging but fair
- Total marks: 20-40

Learning Objectives (if provided):
{objectives}

Study Content:
{context}

{format_instructions}

Generate a quiz titled "Quiz: {topic}" """),
            ("human", "Create the quiz now.")
        ])
        
        chain = prompt | llm
        
        response = await chain.ainvoke({
            "topic": topic,
            "objectives": "\n".join(f"- {obj}" for obj in objectives) if objectives else "Not specified",
            "context": context[:4000],  # Limit context length
            "format_instructions": parser.get_format_instructions()
        })
        
        # Parse structured output
        quiz_output = parser.parse(response.content)
        
        # -------------------------
        # 4️⃣ Return Quiz
        # -------------------------
        quiz_dict = quiz_output.model_dump()
        
        return {
            "quiz": quiz_dict["questions"],
            "quiz_metadata": {
                "title": quiz_dict["title"],
                "topic": quiz_dict["topic"],
                "total_marks": quiz_dict["total_marks"],
                "total_questions": len(quiz_dict["questions"])
            },
            "messages": [
                f"✅ Quiz generated: {quiz_dict['title']}\n"
                f"   {len(quiz_dict['questions'])} questions, {quiz_dict['total_marks']} marks total"
            ],
            "next_step": "FEEDBACK",  # After quiz, show feedback
            "agent_trace": ["quiz"],
            "workflow_complete": False
        }
    
    except Exception as e:
        print(f"❌ Quiz Agent Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "errors": [f"Quiz Agent: {str(e)}"],
            "messages": ["Sorry, I couldn't generate the quiz. Try uploading more study materials."],
            "next_step": "END",
            "workflow_complete": True
        }