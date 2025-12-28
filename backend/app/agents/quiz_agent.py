# backend/app/agents/quiz_agent.py

"""
Quiz Agent - LangChain v1 - Formative Assessor (Full Agent)

Responsibilities:
- Retrieve content for quiz context
- Generate contextual questions from materials
- Create varied question types (MCQ, short answer, true/false)
- Ground questions in curriculum material
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
from app.services.retrieval import RetrievalService
from app.services.subject_service import SubjectService

from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.4,
    google_api_key=os.getenv("GEMINI_API_KEY")
)


# ============================
# OUTPUT SCHEMA
# ============================

class QuizQuestion(BaseModel):
    """Single quiz question."""
    question_number: int
    question_text: str
    question_type: str  # "mcq" | "short_answer" | "true_false"
    options: List[str] = Field(default_factory=list)
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
# TOOLS (Quiz Agent collaborates with these)
# ============================

@tool
def retrieve_quiz_content(topic: str, user_id: str, subject: str = None, chapter: str = None) -> str:
    """Retrieve curriculum content for quiz generation. Required before creating questions."""
    try:
        retrieval_service = RetrievalService()
        
        results = retrieval_service.query(
            question=f"Content about {topic}",
            user_id=user_id,
            subject=subject,
            chapter=chapter,
            k=10
        )
        
        if not results:
            return "No content found. Upload study materials first."
        
        # Format content for quiz generation
        formatted = []
        for i, doc in enumerate(results, 1):
            formatted.append(f"Source {i}:\n{doc['content']}")
        
        return "\n\n".join(formatted)
    
    except Exception as e:
        return f"Error retrieving content: {str(e)}"


@tool
def get_learning_objectives(subject_id: str, user_id: str, chapter_number: int) -> str:
    """Get chapter learning objectives to ground quiz questions in curriculum."""
    try:
        import asyncio
        
        subject = asyncio.run(
            SubjectService.get_subject_by_id(
                user_id=ObjectId(user_id),
                subject_id=ObjectId(subject_id)
            )
        )
        
        if not subject or not subject.plan:
            return "No learning objectives found."
        
        chapters = subject.plan.get("chapters", [])
        chapter = next(
            (ch for ch in chapters if ch.get("chapter_number") == chapter_number),
            None
        )
        
        if chapter:
            objectives = chapter.get("objectives", [])
            return "Learning Objectives:\n" + "\n".join(f"- {obj}" for obj in objectives)
        
        return "No objectives for this chapter."
    
    except Exception as e:
        return f"Error getting objectives: {str(e)}"


tools = [retrieve_quiz_content, get_learning_objectives]


# ============================
# AGENT NODE
# ============================

async def quiz_agent_node(state: AgentEdState) -> Dict:
    """
    Quiz Agent - Full Agent for formative assessment.
    
    Collaborates with Resource Agent through tools.
    INPUT/OUTPUT: Unchanged - fully compatible
    """
    
    print("--- 📝 QUIZ AGENT: Working... ---")
    
    user_id = state["user_id"]
    subject_id = state.get("subject_id")
    chapter_number = state.get("chapter_number")
    current_topic = state.get("current_topic")
    
    topic = current_topic or f"Chapter {chapter_number}" if chapter_number else "General"
    
    try:
        # Get subject context
        subject = None
        if subject_id:
            subject = await SubjectService.get_subject_by_id(
                user_id=ObjectId(user_id),
                subject_id=ObjectId(subject_id)
            )
        
        # Create agent with system prompt
        system_prompt = f"""You are an expert quiz creator (Formative Assessor).

Topic: {topic}
Subject: {subject.subject_name if subject else "Unknown"}
Chapter: {chapter_number if chapter_number else "General"}

Your workflow:
1. Use retrieve_quiz_content to get curriculum materials
2. Use get_learning_objectives to understand what students should know
3. Generate 5-8 varied questions grounded in the retrieved content
4. Ensure questions test understanding, not memorization
5. Provide detailed explanations linking to source materials

Create a comprehensive quiz based on the retrieved content and objectives."""

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt
        )
        
        # Invoke agent to gather content and objectives
        result = agent.invoke({
            "messages": [{
                "role": "user",
                "content": f"Create a quiz for {topic}"
            }]
        })
        
        # Extract agent's response (content retrieved + objectives understood)
        agent_context = getattr(result, "content", "")
        
        # Now generate quiz using Pydantic structured output
        parser = PydanticOutputParser(pydantic_object=QuizOutput)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert quiz creator generating structured quiz output.

{format_instructions}

Create a quiz with:
- 5-8 questions
- Mix of MCQ (60%), short answer (30%), true/false (10%)
- Clear explanations
- Total marks: 20-40

Generate as JSON."""),
            ("human", f"""Based on this context:

{agent_context}

Create a quiz titled "Quiz: {topic}" """)
        ])
        
        chain = prompt | llm
        
        response = await chain.ainvoke({
            "format_instructions": parser.get_format_instructions()
        })
        
        quiz_output = parser.parse(response.content)
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
            "next_step": "FEEDBACK",
            "agent_trace": ["quiz"],
            "workflow_complete": False
        }
    
    except Exception as e:
        print(f"❌ Quiz Agent Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "errors": [f"Quiz Agent: {str(e)}"],
            "messages": ["Sorry, I couldn't generate the quiz."],
            "next_step": "END",
            "workflow_complete": True
        }