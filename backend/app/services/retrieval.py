# backend/app/services/retrieval.py
import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


class RetrievalService:
    """
    Handles all document retrieval and query operations.
    Searches the vector database for relevant documents with:
    - E5 embedding model support (query prefix)
    - Neighboring page fetching for context
    - Confidence scores via similarity search
    - Metadata-based filtering
    """
    
    def __init__(self, db_directory="./chroma_db"):
        self.db_directory = db_directory
        self.embedding_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
        
    def _get_db(self):
        """Internal helper to load the database with persistence."""
        return Chroma(
            persist_directory=self.db_directory,
            embedding_function=self.embedding_model,
            collection_name="rag_knowledge_base"
        )

    # ===========================
    # RETRIEVAL / QUERYING
    # ===========================
    
    def query(self, question, k=3, subject=None, chapter=None, include_neighbors=True):
        """
        Searches the vector database for relevant answers with confidence scores.
        Optionally fetches neighboring pages for enhanced context.
        
        Args:
            question (str): The query question
            k (int): Number of primary results to return (default: 3)
            subject (str, optional): Filter by subject metadata
            chapter (str, optional): Filter by chapter metadata
            include_neighbors (bool): Include neighboring pages (p-1, p+1) for context
        Returns:
            list: List of dicts with 'content', 'metadata', and 'confidence' keys
                  Content has "query: " prefix removed for display
        """
        db = self._get_db()
        prefixed_question = f"query: {question}"

        # Build ChromaDB filter with $and operator for multiple fields
        filter_clauses = []
        if subject:
            filter_clauses.append({'subject': {'$eq': subject}})
        if chapter:
            filter_clauses.append({'chapter': {'$eq': chapter}})
        filter_dict = {'$and': filter_clauses} if filter_clauses else None

        # Perform similarity search with scores
        if filter_dict:
            results = db.similarity_search_with_score(prefixed_question, k=k, filter=filter_dict)
        else:
            results = db.similarity_search_with_score(prefixed_question, k=k)

        # Process results and fetch neighbors
        processed_results = []
        seen_chunk_ids = set()

        for doc, distance in results:
            confidence = max(0, 1 - distance)
            content = doc.page_content
            if content.startswith("passage: "):
                content = content[9:]
            result_dict = {
                "content": content,
                "metadata": doc.metadata,
                "confidence": round(confidence, 4),
                "chunk_id": doc.metadata.get("chunk_id", "unknown")
            }
            chunk_id = doc.metadata.get("chunk_id")
            if chunk_id:
                seen_chunk_ids.add(chunk_id)
            processed_results.append(result_dict)

        # Fetch neighboring pages if enabled
        if include_neighbors and processed_results:
            neighbor_results = self._fetch_neighbor_pages(
                processed_results,
                filter_dict if filter_dict else None
            )
            for neighbor in neighbor_results:
                if neighbor["chunk_id"] not in seen_chunk_ids:
                    processed_results.append(neighbor)

        return processed_results
    
    def _fetch_neighbor_pages(self, results, filters=None):
        """
        Fetch chunks from neighboring pages (p-1, p+1) of retrieved chunks.
        Provides richer context for document understanding.
        
        Args:
            results (list): List of primary search results
            filters (dict, optional): Metadata filters from original query
            
        Returns:
            list: List of neighboring chunks with confidence inherited from primary result
        """
        db = self._get_db()
        neighbors = []
        seen_chunk_ids = {r["chunk_id"] for r in results}
        
        for result in results:
            metadata = result["metadata"]
            source = metadata.get("source")
            current_page = metadata.get("page")

            if not source or not current_page:
                continue

            for neighbor_page in [current_page - 1, current_page + 1]:
                if neighbor_page < 1:
                    continue

                # Build $and filter for neighbor
                neighbor_clauses = [
                    {"source": {"$eq": source}},
                    {"page": {"$eq": neighbor_page}}
                ]
                if filters and "$and" in filters:
                    neighbor_clauses.extend(filters["$and"])
                neighbor_filter = {"$and": neighbor_clauses}

                try:
                    neighbor_docs = db.get(
                        where=neighbor_filter,
                        limit=1
                    )
                    if neighbor_docs and "documents" in neighbor_docs:
                        for doc in neighbor_docs["documents"]:
                            doc_metadata = neighbor_docs.get("metadatas", [{}])[0] if neighbor_docs.get("metadatas") else {}
                            chunk_id = doc_metadata.get("chunk_id", "unknown")
                            if chunk_id not in seen_chunk_ids:
                                content = doc
                                if isinstance(doc, str) and content.startswith("passage: "):
                                    content = content[9:]
                                neighbors.append({
                                    "content": content,
                                    "metadata": doc_metadata,
                                    "confidence": round(result["confidence"] * 0.8, 4),
                                    "chunk_id": chunk_id,
                                    "is_neighbor": True
                                })
                                seen_chunk_ids.add(chunk_id)
                except Exception as e:
                    print(f"Warning: Could not fetch neighbor page {neighbor_page}: {e}")
                    continue
        return neighbors
