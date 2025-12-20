# backend/app/services/rag_service.py
"""
RAG Service - Unified interface combining ingestion and retrieval functionality.
This module re-exports the separated ingestion and retrieval services for backward compatibility.
"""

from app.services.ingestion import IngestionService
from app.services.retrieval import RetrievalService


class RAGService(IngestionService, RetrievalService):
    """
    Unified RAG Service combining document ingestion and retrieval.
    Inherits all functionality from IngestionService and RetrievalService.
    
    This class maintains backward compatibility while leveraging the modular structure
    of separated ingestion and retrieval services.
    """
    
    def __init__(self, db_directory="./chroma_db", subject=None, chapter=None):
        """Initialize both ingestion and retrieval services."""
        IngestionService.__init__(self, db_directory=db_directory, subject=subject, chapter=chapter)
        RetrievalService.__init__(self, db_directory=db_directory)