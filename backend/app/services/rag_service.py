# backend/app/services/rag_service.py
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, UnstructuredPDFLoader
from langchain_core.documents import Document

# --- NEW: Import your OCR service ---
# We assume ocr_service.py is in the same 'app.services' package
try:
    from app.services.ocr_service import extract_text_preprocessed
except ImportError:
    # Fallback for running script directly instead of as a module
    from ocr_service import extract_text_preprocessed

class RAGService:
    def __init__(self, db_directory="./chroma_db"):
        self.db_directory = db_directory
        self.embedding_model = SentenceTransformerEmbeddings(model_name="intfloat/multilingual-e5-large")
        
    def _get_db(self):
        """Internal helper to load the database with persistence."""
        return Chroma(
            persist_directory=self.db_directory,
            embedding_function=self.embedding_model,
            collection_name="rag_knowledge_base"
        )

    def ingest_docx(self, file_path):
        """Loads a DOCX file, chunks it, and saves to DB."""
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found."
            
        print(f"Loading {file_path}...")
        loader = UnstructuredWordDocumentLoader(file_path)
        documents = loader.load()
        text_content = documents[0].page_content
        
        return self.ingest_text(text_content, source=file_path)

    # --- NEW ROUTINE: Image Ingestion ---
    def ingest_image(self, image_path):
        """
        1. Uses OCR to extract text from an image.
        2. Sends that text to the vector database.
        """
        if not os.path.exists(image_path):
            return f"Error: Image {image_path} not found."

        print(f"Starting OCR for {image_path}...")
        
        try:
            # Step 1: Extract text using your existing OCR service
            extracted_text = extract_text_preprocessed(image_path)
            
            # Check if OCR actually found anything
            if not extracted_text.strip():
                return "Warning: No text could be extracted from this image."

            print(f"OCR Complete. Extracted {len(extracted_text)} characters.")

            # Step 2: Feed text into the RAG pipeline
            return self.ingest_text(extracted_text, source=image_path)

        except Exception as e:
            return f"Failed to process image: {str(e)}"
        
    def ingest_pdf(self, file_path):
        """Loads a PDF file, chunks it, and saves to DB."""
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found."
            
        print(f"Loading {file_path}...")
        
        # --- CHANGE HERE ---
        # Use the dedicated PDF loader
        loader = UnstructuredPDFLoader(file_path)
        # -------------------
        
        documents = loader.load()
        text_content = documents[0].page_content
        
        return self.ingest_text(text_content, source=file_path)

    def ingest_text(self, text, source="unknown"):
        """
        Chunks and saves raw text. 
        """
        print("Splitting text into semantic chunks...")
        text_splitter = SemanticChunker(self.embedding_model)
        chunks = text_splitter.create_documents([text])
        
        # Add metadata so we know where this chunk came from
        for chunk in chunks:
            chunk.metadata = {"source": source}

        print(f"Saving {len(chunks)} chunks to Vector DB...")
        db = self._get_db()
        db.add_documents(chunks)
        
        return f"Successfully ingested {len(chunks)} chunks from {source}."

    def query(self, question, k=3):
        """Searches the DB for answers."""
        db = self._get_db()
        results = db.similarity_search(question, k=k)
        return [doc.page_content for doc in results]