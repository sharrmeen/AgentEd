# backend/app/services/retrieval.py
import os
from langchain_chroma import Chroma
from app.services.embedding_service import get_embedding_model


class RetrievalService:
    """
    Handles all document retrieval and query operations.
    """

    def __init__(self, db_directory="./chroma_db"):
        self.db_directory = db_directory
        self.embedding_model = get_embedding_model()


    def _get_db(self):
        return Chroma(
            persist_directory=self.db_directory,
            embedding_function=self.embedding_model,
            collection_name="rag_knowledge_base"
        )

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
        include_neighbors=True
    ):
        """
        Searches the vector database for relevant answers with confidence scores.

        user_id is REQUIRED to prevent cross-user retrieval.
        """
        db = self._get_db()
        prefixed_question = f"query: {question}"

        # ---------------------------
        # BUILD FILTER (CRITICAL)
        # ---------------------------
        filter_clauses = [
            {"user_id": {"$eq": str(user_id)}}
        ]

        if subject:
            filter_clauses.append({"subject": {"$eq": subject}})
        if chapter:
            filter_clauses.append({"chapter": {"$eq": chapter}})

        filter_dict = {"$and": filter_clauses}

        # ---------------------------
        # SIMILARITY SEARCH
        # ---------------------------
        results = db.similarity_search_with_score(
            prefixed_question,
            k=k,
            filter=filter_dict
        )

        processed_results = []
        seen_chunk_ids = set()

        for doc, distance in results:
            confidence = max(0, 1 - distance)
            content = doc.page_content

            if content.startswith("passage: "):
                content = content[9:]

            chunk_id = doc.metadata.get("chunk_id", "unknown")

            processed_results.append({
                "content": content,
                "metadata": doc.metadata,
                "confidence": round(confidence, 4),
                "chunk_id": chunk_id
            })

            seen_chunk_ids.add(chunk_id)

        # ---------------------------
        # NEIGHBOR FETCHING
        # ---------------------------
        if include_neighbors and processed_results:
            neighbors = self._fetch_neighbor_pages(
                processed_results,
                filter_dict
            )
            for n in neighbors:
                if n["chunk_id"] not in seen_chunk_ids:
                    processed_results.append(n)

        return processed_results

    def _fetch_neighbor_pages(self, results, filters):
        """
        Fetch p-1 and p+1 pages with SAME FILTERS (user-safe).
        """
        db = self._get_db()
        neighbors = []
        seen_chunk_ids = {r["chunk_id"] for r in results}

        for result in results:
            metadata = result["metadata"]
            source = metadata.get("source")
            current_page = metadata.get("page")

            if not source or current_page is None:
                continue

            for neighbor_page in (current_page - 1, current_page + 1):
                if neighbor_page < 1:
                    continue

                neighbor_clauses = [
                    {"source": {"$eq": source}},
                    {"page": {"$eq": neighbor_page}},
                ]

                # Inherit ALL original filters (user_id, subject, chapter)
                if filters and "$and" in filters:
                    neighbor_clauses.extend(filters["$and"])

                neighbor_filter = {"$and": neighbor_clauses}

                try:
                    neighbor_docs = db.get(
                        where=neighbor_filter,
                        limit=1
                    )

                    if not neighbor_docs or not neighbor_docs.get("documents"):
                        continue

                    content = neighbor_docs["documents"][0]
                    metadata = neighbor_docs.get("metadatas", [{}])[0]

                    chunk_id = metadata.get("chunk_id", "unknown")
                    if chunk_id in seen_chunk_ids:
                        continue

                    if isinstance(content, str) and content.startswith("passage: "):
                        content = content[9:]

                    neighbors.append({
                        "content": content,
                        "metadata": metadata,
                        "confidence": round(result["confidence"] * 0.8, 4),
                        "chunk_id": chunk_id,
                        "is_neighbor": True
                    })

                    seen_chunk_ids.add(chunk_id)

                except Exception as e:
                    print(f"Warning: Neighbor fetch failed: {e}")

        return neighbors
