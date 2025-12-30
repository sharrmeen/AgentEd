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
    """
    Search the web for factual or educational information
    and return content suitable for student explanations.
    
    Retrieves raw content from sources for better context and accuracy.
    """
    if not TAVILY_AVAILABLE:
        return "Web search not available. Tavily is not installed."
    
    try:
        tavily_client = TavilyClient(
            api_key=os.getenv("TAVILY_API_KEY")
        )
        
        response = tavily_client.search(
            query=f"Explain {query} with examples for students",
            search_depth="basic",
            max_results=5,
            include_raw_content=True
        )
        
        results = response.get("results", [])
        if not results:
            return "No web results found."
        
        formatted_results = []
        
        for i, result in enumerate(results, start=1):
            # Prioritize raw_content for better LLM context
            content = (
                result.get("raw_content")
                or result.get("content")
                or "No content available."
            )
            
            # Limit content length to avoid token overflow
            if len(content) > 500:
                content = content[:500] + "..."
            
            formatted_results.append(
                f"Source {i}: {result.get('title', 'No title')}\n"
                f"URL: {result.get('url', 'No URL')}\n"
                f"Content:\n{content}"
            )
        
        return "\n\n---\n\n".join(formatted_results)
    
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
        system_prompt = f"""You are a knowledgeable study assistant answering student questions.

CONTEXT PROVIDED:
- Question: {question}
- Subject: {subject_name}
- Session: {session_id or "No session"}
- You already have all the information you need. Do NOT ask for user ID or more details.

YOUR TASK: Answer the question "{question}" using available tools.

TOOL EXECUTION STRATEGY (FOLLOW STRICTLY):
1. **FIRST**: Call cache_lookup to check if this question was answered before
   - If [CACHED] result found → Use it IMMEDIATELY and provide the answer
   - Do NOT call other tools if cache hit
   
2. **IF NO CACHE**: Call rag_retriever to search student's uploaded notes
   - If you get 2+ good sources → Synthesize answer and STOP
   - Do NOT call web_search if RAG has sufficient info
   
3. **ONLY IF RAG INSUFFICIENT**: Call web_search for missing information
   - Only if RAG found nothing relevant
   - Use web_search results to supplement

IMPORTANT RULES:
- ✅ Use tools - don't just talk
- ✅ Provide complete answer from tool results
- ✅ Be educational and clear
- ✅ Cite sources when using multiple tools
- ❌ Do NOT ask for more information
- ❌ Do NOT ask for user ID
- ❌ Do NOT skip tools and just chat

RESPONSE FORMAT:
Provide a clear, complete answer to: "{question}"
Focus on the subject: {subject_name}
Minimize tool calls - stop as soon as you have enough information."""

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
        if isinstance(result, dict) and "messages" in result:
            last_message = result["messages"][-1]
            answer = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            answer = getattr(result, "content", "I couldn't find an answer to that question.")
        
        # NOTE: Message storage is handled by the chat endpoint (chat_service)
        # Agent stores are only for updating cached context if needed
        
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