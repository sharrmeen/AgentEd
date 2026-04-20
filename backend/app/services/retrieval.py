# backend/app/services/retrieval.py
from app.core.config import settings
from app.services.embedding_service import get_embedding_model
from app.services.pinecone_service import PineconeService


class RetrievalService:
    """
    Handles all document retrieval and query operations.
    """

    def __init__(self, db_directory=None):
        self.embedding_model = get_embedding_model()
        self.vector_provider = settings.VECTOR_DB_PROVIDER.lower().strip()
        if self.vector_provider != "pinecone":
            raise ValueError("VECTOR_DB_PROVIDER must be 'pinecone' in cloud runtime")


    def _get_db(self):
        return PineconeService()

    @staticmethod
    def _to_pinecone_filter(filter_dict):
        """Convert Chroma-style filters to Pinecone compatible metadata filters."""
        if not filter_dict:
            return None

        if "$and" in filter_dict:
            clauses = []
            for clause in filter_dict["$and"]:
                for key, value in clause.items():
                    if isinstance(value, dict) and "$eq" in value:
                        clauses.append({key: {"$eq": value["$eq"]}})
                    else:
                        clauses.append({key: value})
            return {"$and": clauses}

        converted = {}
        for key, value in filter_dict.items():
            if isinstance(value, dict) and "$eq" in value:
                converted[key] = {"$eq": value["$eq"]}
            else:
                converted[key] = value
        return converted

    # ===========================
    # RETRIEVAL / QUERYING
    # ===========================

    def query(
        self,
        question,
        user_id,
        k=3,
        subject=None,
        chapter=None,
        class_id=None,
        teacher_id=None,
        subject_id=None,
        include_neighbors=True
    ):
        """
        Searches the vector database for relevant answers with confidence scores.

        user_id is REQUIRED to prevent cross-user retrieval.
        """
        db = self._get_db()

        # ---------------------------
        # BUILD FILTER (CRITICAL)
        # ---------------------------
        user_id_str = str(user_id)
        filter_clauses = []

        # Class scope takes precedence for shared teacher-uploaded content.
        if class_id:
            filter_clauses.append({"class_id": {"$eq": str(class_id)}})
        else:
            filter_clauses.append({"user_id": {"$eq": user_id_str}})

        # Prefer stable template identifier when available.
        if subject_id:
            filter_clauses.append({"subject_id": {"$eq": str(subject_id)}})
        elif subject:
            filter_clauses.append({"subject": {"$eq": subject}})
        if teacher_id:
            filter_clauses.append({"teacher_id": {"$eq": str(teacher_id)}})

        # Only use $and if we have multiple filter clauses
        # ChromaDB requires $and to have at least 2 conditions
        if len(filter_clauses) > 1:
            filter_dict = {"$and": filter_clauses}
        else:
            filter_dict = filter_clauses[0]
        
        print(f"🔍 RAG Query:")
        print(f"   Question: {question}")
        print(f"   User ID: {user_id_str}")
        print(f"   Subject filter: {subject}")
        print(f"   Filter: {filter_dict}")

        # ---------------------------
        # SIMILARITY SEARCH
        # ---------------------------
        pinecone_results = db.search_text(
            query=question,
            top_k=k,
            metadata_filter=self._to_pinecone_filter(filter_dict),
        )
        results = []
        for hit in pinecone_results:
            results.append((hit, hit.get("score", 0.0)))
        print(f"   Found {len(results)} results from Pinecone")

        processed_results = []

        for result_obj, raw_score in results:
            metadata = result_obj.get("metadata", {})
            content = result_obj.get("text") or metadata.get("text", "")
            chunk_id = result_obj.get("id") or metadata.get("chunk_id", "unknown")
            confidence = max(0.0, min(1.0, float(raw_score or 0.0)))

            print(f"   ✓ Result: {str(chunk_id)[:8]}... (confidence: {confidence:.4f})")
            print(
                "     Metadata: "
                f"subject={metadata.get('subject')}, "
                f"user_id={metadata.get('user_id')}, "
                f"class_id={metadata.get('class_id')}"
            )

            processed_results.append({
                "content": content,
                "metadata": metadata,
                "confidence": round(confidence, 4),
                "chunk_id": chunk_id
            })

        return processed_results
