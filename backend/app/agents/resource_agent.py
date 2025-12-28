# backend/app/agents/resource_agent.py

"""
Resource Agent - LangChain v1 Compatible (Official Migration)

Uses langchain.agents.create_agent for knowledge retrieval.
"""

import os
from bson import ObjectId
from typing import Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.tools import tool

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("⚠️ Tavily not installed. Web search will be disabled.")

from app.agents.orchestration.state import AgentEdState
from app.services.retrieval import RetrievalService
from app.services.chat_memory_service import ChatMemoryService
from app.services.subject_service import SubjectService

from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.4,
    google_api_key=os.getenv("GEMINI_API_KEY")
)


# ============================
# TOOLS (Using @tool decorator)
# ============================

@tool
def cache_lookup(user_id: str, session_id: str, question: str) -> str:
    """Check if this question was answered before. Use FIRST before searching."""
    try:
        import asyncio
        
        if not session_id:
            return "No session ID provided. Cache unavailable."
        
        cached = asyncio.run(
            ChatMemoryService.get_cached_answer(
                user_id=ObjectId(user_id),
                session_id=ObjectId(session_id),
                intent_tag="Answer",
                question=question
            )
        )
        
        if cached:
            return f"[CACHED] {cached.answer}"
        else:
            return "Not found in cache."
    
    except Exception as e:
        return f"Cache lookup error: {str(e)}"


@tool
def rag_retriever(user_id: str, question: str, subject: str = None, chapter: str = None) -> str:
    """Retrieve information from uploaded notes and study materials."""
    try:
        retrieval_service = RetrievalService()
        
        results = retrieval_service.query(
            question=question,
            user_id=user_id,
            subject=subject,
            chapter=chapter,
            k=5
        )
        
        if not results:
            return "No relevant content found in your notes."
        
        formatted = []
        for i, doc in enumerate(results, 1):
            content = doc["content"]
            metadata = doc.get("metadata", {})
            
            formatted.append(
                f"Source {i} (Confidence: {doc.get('confidence', 0):.2f}):\n"
                f"{content}\n"
                f"[From: {metadata.get('source_file', 'Unknown')}]"
            )
        
        return "\n\n".join(formatted)
    
    except Exception as e:
        return f"RAG retrieval error: {str(e)}"


@tool
def web_search(query: str) -> str:
    """Search the web for recent or factual information."""
    if not TAVILY_AVAILABLE:
        return "Web search not available. Tavily not installed."
    
    try:
        tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=3
        )
        
        results = response.get("results", [])
        
        if not results:
            return "No web results found."
        
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"{i}. {result.get('title', 'No title')}\n"
                f"   {result.get('content', 'No content')}\n"
                f"   Source: {result.get('url', 'No URL')}"
            )
        
        return "\n\n".join(formatted)
    
    except Exception as e:
        return f"Web search error: {str(e)}"


# Only include web_search if available
resource_tools = [cache_lookup, rag_retriever]
if TAVILY_AVAILABLE:
    resource_tools.append(web_search)


# ============================
# AGENT NODE
# ============================

async def resource_agent_node(state: AgentEdState) -> Dict:
    """
    LangGraph node for knowledge retrieval and Q&A.
    Uses official LangChain v1 create_agent.
    INPUT/OUTPUT: Unchanged - fully compatible
    """
    
    print("--- 📚 RESOURCE AGENT: Working... ---")
    
    user_id = state["user_id"]
    subject_id = state.get("subject_id")
    session_id = state.get("session_id")
    question = state["user_query"]
    
    # Get subject context
    subject_name = "Unknown"
    if subject_id:
        try:
            subject = await SubjectService.get_subject_by_id(
                user_id=ObjectId(user_id),
                subject_id=ObjectId(subject_id)
            )
            subject_name = subject.subject_name if subject else "Unknown"
        except:
            pass
    
    try:
        # Build system prompt (official v1 way)
        system_prompt = f"""You are a knowledgeable study assistant.

Question: {question}
Subject: {subject_name}
Session: {session_id or "No session"}

Strategy:
1. First try cache_lookup - if found, use cached answer
2. Then try rag_retriever - search student's notes
3. Only use web_search if notes don't have enough info
4. Provide clear, educational answers"""

        # Create agent using official v1 API
        agent = create_agent(
            model=llm,
            tools=resource_tools,
            system_prompt=system_prompt
        )
        
        # Invoke agent
        result = agent.invoke({
            "messages": [{"role": "user", "content": question}]
        })
        
        # Extract output
        answer = getattr(result, "content", "I couldn't find an answer to that question.")
        
        # Store in cache if session exists
        if session_id and subject_id:
            try:
                await ChatMemoryService.store_memory(
                    user_id=ObjectId(user_id),
                    subject_id=ObjectId(subject_id),
                    session_id=ObjectId(session_id),
                    chat_id=ObjectId(session_id),
                    question=question,
                    answer=answer,
                    intent_tag="Answer",
                    confidence_score=0.9,
                    source="AGENT"
                )
            except:
                pass
        
        next_step = "END"
        if "quiz" in question.lower():
            next_step = "QUIZ"
        
        return {
            "answer": answer,
            "content": answer,
            "messages": [answer],
            "next_step": next_step,
            "agent_trace": ["resource"],
            "workflow_complete": (next_step == "END")
        }
    
    except Exception as e:
        print(f"❌ Resource Agent Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "errors": [f"Resource Agent: {str(e)}"],
            "messages": ["Sorry, I couldn't retrieve that information."],
            "next_step": "END",
            "workflow_complete": True
        }