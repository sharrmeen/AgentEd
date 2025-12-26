# backend/app/agents/resource_agent.py

"""
Resource Agent (Refactored) - Knowledge Librarian + Expert.

Responsibilities:
- Semantic search in ChromaDB (via RetrievalService)
- Web search using Tavily (for recent/factual info)
- Cache-aware Q&A (via ChatMemoryService)
- Context-grounded answer generation
- NO CHANGES to existing services
"""

import os
from bson import ObjectId
from typing import Dict, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub

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


# ============================
# LLM SETUP
# ============================

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.7,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)


# ============================
# TAVILY TOOL (Web Search)
# ============================

if TAVILY_AVAILABLE:
    tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    def tavily_search_func(query: str) -> str:
        """
        Search the web using Tavily.
        
        Use for:
        - Recent events or news
        - Factual questions not in curriculum
        - Real-time information
        """
        try:
            response = tavily_client.search(
                query=query,
                search_depth="advanced",
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
            return f"Tavily search error: {str(e)}"
    
    tavily_tool = StructuredTool.from_function(
        name="web_search",
        func=tavily_search_func,
        description="""Search the web for recent or factual information.
        Use this for:
        - Current events, news, latest developments
        - Facts not covered in curriculum
        - Real-world applications
        Input: search query string
        Output: formatted search results"""
    )
else:
    tavily_tool = None


# ============================
# RAG TOOL (Internal Knowledge)
# ============================

async def rag_retrieval_func(params: Dict) -> str:
    """
    Retrieve content from internal ChromaDB using RetrievalService.
    
    Input: {user_id, subject, chapter, question}
    Output: Retrieved context
    """
    try:
        retrieval_service = RetrievalService()
        
        results = retrieval_service.query(
            question=params["question"],
            user_id=params["user_id"],
            subject=params.get("subject"),
            chapter=params.get("chapter"),
            k=5
        )
        
        if not results:
            return "No relevant content found in your notes."
        
        formatted = []
        for i, doc in enumerate(results, 1):
            content = doc["content"]
            metadata = doc.get("metadata", {})
            
            formatted.append(
                f"Source {i} (Confidence: {doc['confidence']:.2f}):\n"
                f"{content}\n"
                f"[From: {metadata.get('source_file', 'Unknown')}]"
            )
        
        return "\n\n".join(formatted)
    
    except Exception as e:
        return f"RAG retrieval error: {str(e)}"


rag_tool = StructuredTool.from_function(
    name="rag_retriever",
    func=rag_retrieval_func,
    description="""Retrieve information from your uploaded notes and study materials.
    Use this for:
    - Questions about syllabus content
    - Topics covered in your notes
    - Curriculum-specific information
    Input: JSON with user_id, question, subject (optional), chapter (optional)
    Output: retrieved content from ChromaDB"""
)


# ============================
# CACHE LOOKUP TOOL
# ============================

async def cache_lookup_func(params: Dict) -> str:
    """
    Check if question was answered before (via ChatMemoryService).
    
    Input: {user_id, session_id, question}
    Output: Cached answer or "Not found"
    """
    try:
        if not params.get("session_id"):
            return "No session ID provided. Cache unavailable."
        
        cached = await ChatMemoryService.get_cached_answer(
            user_id=ObjectId(params["user_id"]),
            session_id=ObjectId(params["session_id"]),
            intent_tag="Answer",
            question=params["question"]
        )
        
        if cached:
            return f"[CACHED] {cached.answer}"
        else:
            return "Not found in cache."
    
    except Exception as e:
        return f"Cache lookup error: {str(e)}"


cache_tool = StructuredTool.from_function(
    name="cache_lookup",
    func=cache_lookup_func,
    description="""Check if this question was answered before (saves time).
    Use this FIRST before searching or retrieving.
    Input: JSON with user_id, session_id, question
    Output: cached answer or "Not found" """
)


# ============================
# AGENT NODE
# ============================

async def resource_agent_node(state: AgentEdState) -> Dict:
    """
    LangGraph node for knowledge retrieval and Q&A.
    
    Strategy:
    1. Check cache first (fast)
    2. If miss, try RAG (internal notes)
    3. If insufficient, try Tavily (web search)
    4. Generate answer with LLM
    5. Store in cache
    """
    
    print("--- 📚 RESOURCE AGENT: Working... ---")
    
    user_id = state["user_id"]
    subject_id = state.get("subject_id")
    session_id = state.get("session_id")
    question = state["user_query"]
    
    # Get subject context
    subject_name = None
    if subject_id:
        try:
            subject = await SubjectService.get_subject_by_id(
                user_id=ObjectId(user_id),
                subject_id=ObjectId(subject_id)
            )
            subject_name = subject.subject_name if subject else None
        except:
            pass
    
    # Build agent tools (only include available ones)
    tools = [cache_tool, rag_tool]
    if tavily_tool:
        tools.append(tavily_tool)
    
    # Create ReAct agent
    prompt = hub.pull("hwchase17/react")
    
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5
    )
    
    try:
        # Context for agent
        context = f"""
User Question: {question}
Subject: {subject_name or "Unknown"}
Session ID: {session_id or "No session"}

Your task:
1. First, check the cache using cache_lookup
2. If not cached, search internal notes using rag_retriever
3. If notes don't have the answer, use web_search (if available)
4. Provide a clear, educational answer

Remember: Prioritize internal notes over web search for curriculum questions.
"""
        
        result = await executor.ainvoke({
            "input": context,
            "agent_scratchpad": ""
        })
        
        answer = result.get("output", "I couldn't find an answer to that question.")
        
        # Store in cache if session exists
        if session_id:
            try:
                await ChatMemoryService.store_memory(
                    user_id=ObjectId(user_id),
                    subject_id=ObjectId(subject_id) if subject_id else ObjectId(),
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
        
        # Determine next step
        next_step = "END"
        if "quiz" in question.lower():
            next_step = "QUIZ"
        
        return {
            "answer": answer,
            "content": answer,  # For compatibility
            "messages": [answer],
            "next_step": next_step,
            "agent_trace": ["resource"],
            "workflow_complete": (next_step == "END")
        }
    
    except Exception as e:
        print(f"❌ Resource Agent Error: {e}")
        return {
            "errors": [f"Resource Agent: {str(e)}"],
            "messages": ["Sorry, I couldn't retrieve that information."],
            "next_step": "END",
            "workflow_complete": True
        }