from datetime import datetime
from typing import Optional, List
from bson import ObjectId
import hashlib
import math

from app.core.database import db
from app.core.models.chat_memory import ChatMemory
from app.services.embedding_service import embed_query

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2) if norm1 and norm2 else 0.0

class ChatMemoryService:
    """
    Handles conversational memory.

    RESPONSIBILITIES:
    - Cache lookup (exact + semantic)
    - Procedural similarity decision
    - MongoDB persistence
    - UI chat history
    """

    SIMILARITY_THRESHOLD = 0.85

    @staticmethod
    def _hash_question(question: str) -> str:
        return hashlib.sha256(
            question.strip().lower().encode("utf-8")
        ).hexdigest()

    @staticmethod
    async def get_cached_answer(
        *,
        user_id: ObjectId,
        session_id: ObjectId,
        intent_tag: str,
        question: str,
    ) -> Optional[ChatMemory]:
        """
        Cache lookup order (STRICT):
        1️⃣ Exact question hash match
        2️⃣ Semantic similarity via embeddings
        """

        col = db.chat_memory()
        question_hash = ChatMemoryService._hash_question(question)

        # ---------- 1️⃣ Exact Match ----------
        exact = await col.find_one({
            "user_id": user_id,
            "session_id": session_id,
            "question_hash": question_hash,
            "intent_tag": intent_tag,
        })

        if exact:
            exact["source"] = "CACHE"
            return ChatMemory(**exact)

        # ---------- 2️⃣ Semantic Match ----------
        query_embedding = embed_query(question)

        candidates = await col.find({
            "user_id": user_id,
            "session_id": session_id,
            "intent_tag": intent_tag,
        }).to_list(None)

        best_match = None
        best_score = 0.0

        for doc in candidates:
            score = cosine_similarity(
                query_embedding,
                doc["embedding"]
            )

            if score > best_score:
                best_score = score
                best_match = doc

        if best_match and best_score >= ChatMemoryService.SIMILARITY_THRESHOLD:
            best_match["source"] = "CACHE"
            best_match["confidence_score"] = best_score
            return ChatMemory(**best_match)

        return None

    @staticmethod
    async def store_memory(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        session_id: ObjectId,
        chat_id: ObjectId,
        question: str,
        answer: str,
        intent_tag: str,
        confidence_score: float,
        source: str,  # CACHE | LLM
    ) -> ChatMemory:
        """
        Persist a new chat turn.
        """

        col = db.chat_memory()

        embedding = embed_query(question)

        doc = {
            "user_id": user_id,
            "subject_id": subject_id,
            "session_id": session_id,
            "chat_id": chat_id,

            "question": question,
            "question_hash": ChatMemoryService._hash_question(question),
            "intent_tag": intent_tag,

            "answer": answer,
            "embedding": embedding,

            "confidence_score": confidence_score,
            "source": source,

            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await col.insert_one(doc)
        doc["_id"] = result.inserted_id

        return ChatMemory(**doc)

    @staticmethod
    async def get_chat_history(
        *,
        user_id: ObjectId,
        chat_id: ObjectId,
        limit: int = 50,
    ) -> List[ChatMemory]:
        """
        Used by frontend to render chat messages.
        Ordered chronologically.
        """

        col = db.chat_memory()

        cursor = (
            col.find({
                "user_id": user_id,
                "chat_id": chat_id,
            })
            .sort("created_at", 1)
            .limit(limit)
        )

        docs = await cursor.to_list(None)
        return [ChatMemory(**doc) for doc in docs]
        

