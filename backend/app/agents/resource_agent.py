# backend/app/agents/resource_agent.py

"""
Resource Agent - LangChain v1 Compatible (Official Migration)

Uses langchain.agents.create_agent for knowledge retrieval.
"""

import os
import asyncio
import sys
from bson import ObjectId
from typing import Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage

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


# ============================
# LOGGING HELPER (Must be defined early)
# ============================
def log_print(msg: str):
    """Print with immediate flush to ensure logs appear."""
    print(msg, flush=True)
    sys.stdout.flush()
    sys.stderr.flush()


# ============================
# LLM INITIALIZATION
# ============================
_api_key = os.getenv("GEMINI_API_KEY")
log_print(f"Gemini API key loaded: {'YES' if _api_key else 'NO'} (length: {len(_api_key) if _api_key else 0})")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.4,
    google_api_key=_api_key
)


# ============================
# TOOLS (Using @tool decorator)
# ============================
# Helper function - NOT a tool (called directly, not by agent)
def cache_lookup(user_id: str, session_id: str, question: str, intent: str = "answer") -> str:
    """
    Check if this question was answered before with the same intent.
    Use FIRST before searching. Cached answers must match intent.
    """
    try:
        if not session_id:
            return "No session ID provided. Cache unavailable."
        
        # Note: Cannot use asyncio.run() from within async context
        # This function will be called from async context, so we can't use asyncio.run()
        # For now, we'll return "Not found" - the actual cache check will happen via RAG
        log_print(f"⚠️ Cache lookup called but cannot be executed from async context")
        return "Not found in cache."
    
    except Exception as e:
        return f"Cache lookup error: {str(e)}"


# Helper function - NOT a tool (called directly, not by agent)
def rag_retriever(user_id: str, question: str, subject: str = None) -> str:
    """
    Retrieve information from uploaded notes and study materials.
    
    Filters by subject if provided to ensure context-relevant results.
    """
    try:
        log_print(f"🔧 RAG Retriever called:")
        log_print(f"   user_id: {user_id} (type: {type(user_id).__name__})")
        log_print(f"   question: {question}")
        log_print(f"   subject: {subject}")
        
        retrieval_service = RetrievalService()
        
        # Search documents for this user, filtered by subject if provided
        # If subject is provided, prioritize results from that subject
        results = retrieval_service.query(
            question=question,
            user_id=user_id,
            subject=subject,  # Filter by subject if provided
            chapter=None,  # Search all chapters within subject
            k=5
        )
        
        if not results:
            log_print(f"❌ RAG: No results found for: {question}")
            return "No relevant content found in your notes. You may need to upload study materials first."
        
        log_print(f"✅ RAG: Found {len(results)} sources for: {question}")
        
        formatted = []
        for i, doc in enumerate(results, 1):
            content = doc["content"]
            metadata = doc.get("metadata", {})
            
            # Extract meaningful source info
            source_file = metadata.get('source_file', 'Unknown')
            subject = metadata.get('subject', 'Unknown')
            chapter = metadata.get('chapter', 'Unknown')
            confidence = doc.get('confidence', 0)
            
            log_print(f"   Source {i}: {subject} - {chapter} - {source_file} (confidence: {confidence:.2f})")
            
            formatted.append(
                f"Source {i} (From {subject}, {chapter} - Confidence: {confidence:.2f}):\n"
                f"{content}\n"
                f"[File: {source_file}]"
            )
        
        return "\n\n".join(formatted)
    
    except Exception as e:
        log_print(f"❌ RAG Error: {str(e)}")
        import traceback
        import io
        tb_str = io.StringIO()
        traceback.print_exc(file=tb_str)
        log_print(tb_str.getvalue())
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

log_print("resource_agent module loaded successfully")

# ============================
# AGENT NODE
# ============================

async def resource_agent_node(state: AgentEdState) -> Dict:
    """
    LangGraph node for knowledge retrieval and Q&A.
    Uses intent-based prompting (single agent, dynamic behavior based on intent).
    """
    
    log_print("\n\n🚀🚀🚀 RESOURCE_AGENT_NODE CALLED 🚀🚀🚀")
    log_print(f"Timestamp: {__import__('datetime').datetime.now()}")
    
    try:
        log_print("--- 📚 RESOURCE AGENT: Working... ---")
        log_print(f"🔍 State keys: {list(state.keys())}")
        
        user_id = state["user_id"]
        subject_id = state.get("subject_id")
        session_id = state.get("session_id")
        question = state["user_query"]
        intent = state.get("intent", "answer").lower()  # Get intent from state
        
        log_print(f"✅ Extracted state: user_id={user_id}, subject_id={subject_id}, session_id={session_id}, intent={intent}")
        
        # Get subject context
        subject_name = "Unknown"
        if subject_id:
            try:
                log_print(f"🔧 Getting subject name for subject_id={subject_id}...")
                subject = await SubjectService.get_subject_by_id(
                    user_id=ObjectId(user_id),
                    subject_id=ObjectId(subject_id)
                )
                subject_name = subject.subject_name if subject else "Unknown"
                log_print(f"✅ Got subject: {subject_name}")
            except Exception as subject_error:
                log_print(f"⚠️ Subject lookup error: {type(subject_error).__name__}: {subject_error}")
        
        log_print(f"🔧 Building system prompt for intent: {intent}")
        # Build INTENT-SPECIFIC system prompt
        intent_instructions = _get_intent_prompt(intent, question, subject_name)
        
        system_prompt = f"""You are a knowledgeable study assistant answering student questions.

CONTEXT PROVIDED:
- Question: {question}
- Subject: {subject_name}
- Session: {session_id or "No session"}
- Intent: {intent}

{intent_instructions}

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
Provide answer in a format matching the intent.
Focus on the subject: {subject_name}
Minimize tool calls - stop as soon as you have enough information."""

        log_print(f"✅ System prompt built ({len(system_prompt)} chars)")
        
        # Create single agent (regardless of intent)
        # Direct LLM invocation with tools - simpler approach without agent factories
        
        log_print(f"🔧 Starting answer generation...")
        
        # Skip cache_lookup - use RAG directly
        answer = None
        try:
            log_print(f"🔧 Step 1: Calling RAG retriever with user_id={user_id}, subject={subject_name}...")
            rag_result = rag_retriever(
                user_id=user_id,
                question=question,
                subject=subject_name
            )
            log_print(f"  RAG result length: {len(rag_result) if rag_result else 0}")
            
            if rag_result and "No relevant content" not in rag_result:
                log_print(f"✅ RAG found relevant content ({len(rag_result)} chars)")
                
                # Generate answer using LLM with RAG context
                log_print(f"🔧 Step 2: Generating LLM response with RAG context...")
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"""Based on the following context, answer the question:

CONTEXT:
{rag_result}

QUESTION: {question}

Provide a comprehensive answer based on the context above.""")
                ]
                
                try:
                    log_print(f"  Message count: {len(messages)}, calling llm.ainvoke()...")
                    response = await llm.ainvoke(messages)
                    log_print(f"  Raw response type: {type(response).__name__}")
                    log_print(f"  Raw response dir: {[attr for attr in dir(response) if not attr.startswith('_')]}")
                    
                    # Debug: Print all attributes of the response
                    if hasattr(response, 'content'):
                        log_print(f"  response.content = '{response.content}' (type: {type(response.content)})")
                    if hasattr(response, 'text'):
                        log_print(f"  response.text = '{response.text}'")
                    if hasattr(response, 'response_metadata'):
                        log_print(f"  response.response_metadata = {response.response_metadata}")
                    
                    # Extract content from response - try multiple approaches
                    answer = None
                    
                    if isinstance(response, str):
                        answer = response
                        log_print(f"  Used: response as string")
                    elif hasattr(response, 'content') and response.content:
                        answer = response.content
                        log_print(f"  Used: response.content")
                    elif hasattr(response, 'text') and response.text:
                        answer = response.text
                        log_print(f"  Used: response.text")
                    else:
                        # Try to convert to string
                        answer = str(response)
                        log_print(f"  Used: str(response) = {answer[:100] if answer else 'EMPTY'}")
                    
                    log_print(f"  Extracted answer type: {type(answer)}, length: {len(answer) if answer else 0}")
                    if answer and len(answer.strip()) > 0:
                        log_print(f"✅ LLM generated answer ({len(answer)} chars): {answer[:150]}...")
                    else:
                        log_print(f"⚠️ LLM returned empty or None response")
                        log_print(f"  Full response object: {response}")
                except Exception as llm_error:
                    log_print(f"⚠️ LLM error: {type(llm_error).__name__}: {llm_error}")
                    import io, traceback
                    tb_str = io.StringIO()
                    traceback.print_exc(file=tb_str)
                    log_print(tb_str.getvalue())
                    answer = f"Based on your notes: {rag_result[:500]}"
            else:
                log_print(f"ℹ️ RAG found no relevant content, will fallback to direct LLM")
        except Exception as rag_error:
            log_print(f"⚠️ RAG retriever failed: {type(rag_error).__name__}: {rag_error}")
        
        # If no answer from RAG+LLM, try direct LLM
        if not answer:
            log_print(f"🔧 Step 3: Fallback to direct LLM...")
            try:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=question)
                ]
                log_print(f"  Message count: {len(messages)}, calling llm.ainvoke()...")
                response = await llm.ainvoke(messages)
                log_print(f"  Raw response type: {type(response).__name__}")
                
                # Extract content from response
                if isinstance(response, str):
                    answer = response
                elif hasattr(response, 'content'):
                    answer = response.content
                else:
                    answer = str(response)
                
                log_print(f"  Extracted answer type: {type(answer)}, length: {len(answer) if answer else 0}")
                if answer and len(answer.strip()) > 0:
                    log_print(f"✅ LLM generated answer ({len(answer)} chars): {answer[:150]}...")
                else:
                    log_print(f"⚠️ LLM returned empty or None response")
            except Exception as llm_error:
                log_print(f"❌ LLM error in direct fallback: {type(llm_error).__name__}: {llm_error}")
                import io, traceback
                tb_str = io.StringIO()
                traceback.print_exc(file=tb_str)
                log_print(tb_str.getvalue())
                raise
        
        # Finalize
        log_print(f"🔧 Finalizing response...")
        if not answer or answer.strip() == "":
            log_print(f"⚠️ Answer is empty!")
            answer = "I couldn't find a suitable answer. Please try rephrasing your question."
        
        log_print(f"✅ Final answer ready ({len(answer)} chars)")
        
        next_step = "END"
        if "quiz" in question.lower():
            next_step = "QUIZ"
        
        print(f"✅ Returning successful response with next_step={next_step}")
        return {
            "answer": answer,
            "content": answer,
            "messages": [answer],
            "next_step": next_step,
            "agent_trace": ["resource"],
            "workflow_complete": (next_step == "END")
        }
    
    except Exception as e:
        log_print(f"\n❌❌❌ RESOURCE AGENT TOP-LEVEL ERROR ❌❌❌")
        log_print(f"Error type: {type(e).__name__}")
        log_print(f"Error message: {e}")
        import traceback
        import io
        # Capture traceback to log it properly
        tb_str = io.StringIO()
        traceback.print_exc(file=tb_str)
        log_print(tb_str.getvalue())
        log_print(f"❌❌❌ END ERROR ❌❌❌\n")
        
        return {
            "errors": [f"Resource Agent: {str(e)}"],
            "messages": ["Sorry, I couldn't retrieve that information."],
            "next_step": "END",
            "workflow_complete": True
        }


def _get_intent_prompt(intent: str, question: str, subject: str) -> str:
    """
    Get intent-specific instruction prompt.
    
    Single agent, different behaviors based on intent:
    - 'explain': Educational explanation with structure
    - 'summarize': Concise summary with key points
    - 'answer': Comprehensive structured answer (default)
    """
    
    if intent == "explain":
        return f"""YOUR TASK: Explain the concept: "{question}"

RESPONSE FORMAT:
1. **Definition/Introduction** - What is this concept?
2. **Why Do We Need This?** - Purpose and importance
3. **Core Idea** - Main principle in simple terms
4. **How It Works** - Step-by-step explanation
5. **Real-Life Example** - Practical illustration
6. **Key Takeaways** - Summary points to remember

STYLE: Clear, educational, suitable for learning {subject}
LENGTH: 300-500 words
TONE: Friendly and encouraging"""
    
    elif intent == "summarize":
        return f"""YOUR TASK: Summarize: "{question}"

RESPONSE FORMAT:
1. **Overview** - What is this about? (1-2 sentences)
2. **Key Points** - 3-5 main ideas
3. **Important Details** - Critical information
4. **Connections** - How it relates to {subject}
5. **Quick Summary** - Brief one-line conclusion

STYLE: Concise and comprehensive
LENGTH: 150-300 words
TONE: Direct and informative"""
    
    else:  # answer (default)
        return f"""YOUR TASK: Answer the question: "{question}"

RESPONSE FORMAT:
1. **Definition / Introduction** - What the topic is
2. **Why Do We Need This?** - Purpose and importance
3. **Core Idea / Key Concept** - Main principle
4. **Structure / Components / Architecture** - Parts involved
5. **Working / How It Works** - Step-by-step explanation
6. **Advantages** - Benefits and strengths
7. **Disadvantages / Limitations** - Drawbacks
8. **Example / Real-Life Illustration** - Practical example

STYLE: Comprehensive and structured
LENGTH: 400-600 words
TONE: Educational and detailed"""