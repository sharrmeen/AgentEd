# backend/app/api/v1/chat.py

"""
Chat endpoints - Q&A and conversational interaction.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId

from app.services.chat_service import ChatService
from app.services.chat_memory_service import ChatMemoryService
from app.core.database import db
from app.agents.orchestration.workflow import run_workflow
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryResponse,
    ChatResponse
)
from app.api.deps import get_user_id

router = APIRouter()


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Get chat container details.
    
    Args:
        chat_id: Chat ID
        
    Returns:
        Chat container information
    """
    try:
        chat_obj_id = ObjectId(chat_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat ID format"
        )
    
    chat = await ChatService.get_chat_by_id(
        user_id=user_id,
        chat_id=chat_obj_id
    )
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    return ChatResponse(
        id=str(chat.id),
        session_id=str(chat.session_id),
        subject_id=str(chat.subject_id),
        chapter_number=chat.chapter_number,
        chapter_title=chat.chapter_title,
        created_at=chat.created_at
    )


@router.post("/{chat_id}/message", response_model=ChatMessageResponse)
async def send_message(
    chat_id: str,
    request: ChatMessageRequest,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Send a question and get an answer.
    
    Features:
    - Cache-aware Q&A (checks exact match and semantic similarity)
    - LLM generation if no cache hit
    - Stores answer in memory for future use
    
    Args:
        chat_id: Chat ID
        request: Message with question and intent
        
    Returns:
        Answer with source indication (CACHE or LLM)
    """
    try:
        chat_obj_id = ObjectId(chat_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat ID format"
        )
    
    try:
        # Validate chat ownership
        chat = await ChatService.validate_chat_ownership(
            user_id=user_id,
            chat_id=chat_obj_id
        )
        
        # Check cache first
        cached = await ChatMemoryService.get_cached_answer(
            user_id=user_id,
            session_id=chat.session_id,
            intent_tag=request.intent_tag,
            question=request.question
        )
        
        if cached:
            # Touch chat to update last_active
            await ChatService.touch_chat(chat_id=chat_obj_id)
            
            return ChatMessageResponse(
                answer=cached.answer,
                source="CACHE",
                cached=True,
                confidence_score=cached.confidence_score,
                session_id=str(chat.session_id),
                chat_id=str(chat.id)
            )
        
        # No cache hit - generate with LLM using agent workflow
        try:
            workflow_result = await run_workflow(
                user_id=str(user_id),
                user_query=request.question,
                subject_id=str(chat.subject_id),
                chapter_number=chat.chapter_number,
                session_id=str(chat.session_id),
                intent=request.intent_tag or "answer"
            )
            
            # Debug: Log workflow result structure
            print(f"🔍 Workflow result type: {type(workflow_result)}")
            print(f"🔍 Workflow result keys: {list(workflow_result.keys()) if hasattr(workflow_result, 'keys') else 'NOT A DICT'}")
            
            # Extract response from workflow state - try multiple fields
            answer = ""
            
            # Try messages array first
            messages = workflow_result.get("messages", []) if isinstance(workflow_result, dict) else []
            if messages and len(messages) > 0:
                print(f"✅ Found {len(messages)} messages: {messages}")
                # Filter out None/empty and join
                answer = " ".join([str(m) for m in messages if m and str(m).strip()])
            
            # Fallback to answer field
            if not answer:
                answer = workflow_result.get("answer", "") if isinstance(workflow_result, dict) else ""
                if answer:
                    print(f"✅ Found answer field: {answer[:100]}...")
            
            # Fallback to content field
            if not answer:
                answer = workflow_result.get("content", "") if isinstance(workflow_result, dict) else ""
                if answer:
                    print(f"✅ Found content field: {answer[:100]}...")
            
            if not answer or answer.strip() == "":
                print(f"❌ No answer found. Full result: {workflow_result}")
                raise ValueError("No response generated by LLM")
            
            print(f"✅ Final answer extracted: {answer[:100]}...")
            
            # Store in chat memory for future cache hits
            await ChatMemoryService.store_memory(
                user_id=user_id,
                subject_id=ObjectId(chat.subject_id),
                session_id=chat.session_id,
                chat_id=chat_obj_id,
                question=request.question,
                answer=answer,
                intent_tag=request.intent_tag,
                source="LLM",
                confidence_score=0.95
            )
            
            # Touch chat to update last_active
            await ChatService.touch_chat(chat_id=chat_obj_id)
            
            return ChatMessageResponse(
                answer=answer,
                source="LLM",
                cached=False,
                confidence_score=0.95,
                session_id=str(chat.session_id),
                chat_id=str(chat.id)
            )
        
        except Exception as llm_error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate answer: {str(llm_error)}"
            )
    
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to chat"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{chat_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    chat_id: str,
    limit: int = 50,
    skip: int = 0,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Get chat history (Q&A turns) with pagination support.
    
    Query Parameters:
        limit: Maximum number of messages to return (default: 50, max: 100)
        skip: Number of messages to skip for pagination (default: 0)
        
    Returns:
        Chronological list of messages with pagination info
        
    Example:
        - First page: /history?limit=50&skip=0
        - Next page: /history?limit=50&skip=50
        - Older messages: /history?limit=50&skip=100
    """
    # Validate limit
    limit = min(limit, 100)  # Max 100 messages per request
    if limit < 1:
        limit = 50
    if skip < 0:
        skip = 0
    
    try:
        chat_obj_id = ObjectId(chat_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat ID format"
        )
    
    try:
        # Validate ownership
        chat = await ChatService.validate_chat_ownership(
            user_id=user_id,
            chat_id=chat_obj_id
        )
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to chat"
            )
        
        # Get total count for pagination
        col = db.chat_memory()
        total_count = await col.count_documents({
            "user_id": user_id,
            "chat_id": chat_obj_id,
        })
        
        # Get paginated history (skip oldest, show latest)
        cursor = (
            col.find({
                "user_id": user_id,
                "chat_id": chat_obj_id,
            })
            .sort("created_at", 1)  # Oldest first
            .skip(skip)
            .limit(limit)
        )
        
        messages_docs = await cursor.to_list(None)
        
        message_responses = [
            {
                "id": str(m["_id"]),
                "question": m.get("question", ""),
                "answer": m.get("answer", ""),
                "intent_tag": m.get("intent_tag", "Answer"),
                "source": m.get("source", "LLM"),
                "confidence_score": m.get("confidence_score", 0),
                "created_at": m.get("created_at")
            }
            for m in messages_docs
        ]
        
        # Build response with pagination info
        response = ChatHistoryResponse(
            chat_id=chat_id,
            session_id=str(chat.session_id),
            subject_id=str(chat.subject_id),
            chapter_number=chat.chapter_number,
            chapter_title=chat.chapter_title,
            messages=message_responses,
            total=total_count,
            limit=limit,
            skip=skip,
            has_more=(skip + limit) < total_count
        )
        
        return response
    
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to chat"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
