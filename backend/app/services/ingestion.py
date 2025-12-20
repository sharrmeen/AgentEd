# backend/app/services/ingestion.py
import os
import re
import tempfile
import hashlib
import uuid
import asyncio
from functools import wraps
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, UnstructuredPDFLoader
from langchain_core.documents import Document
from pdf2image import convert_from_path
import PyPDF2

# --- Import OCR service ---
try:
    from app.services.ocr_service import extract_text_preprocessed
except ImportError:
    # Fallback for running script directly instead of as a module
    from ocr_service import extract_text_preprocessed


def async_to_sync(async_func):
    """Decorator to run async functions in a sync context."""
    @wraps(async_func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # If already in async context, schedule the task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return loop.run_in_executor(pool, lambda: asyncio.run(async_func(*args, **kwargs)))
        else:
            return loop.run_until_complete(async_func(*args, **kwargs))
    
    return wrapper


class IngestionService:
    """
    Handles all document ingestion operations including:
    - Loading documents from various file types (DOCX, PDF, images)
    - OCR processing for scanned documents (async)
    - Document chunking and deterministic deduplication
    - Persisting documents to vector database with traceability
    """
    
    def __init__(self, db_directory="./chroma_db", subject=None, chapter=None):
        self.db_directory = db_directory
        self.embedding_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
        
        # Metadata context
        self.subject = subject
        self.chapter = chapter
        
        # Configuration from environment variables with defaults
        self.MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", "1200"))
        
    def _get_db(self):
        """Internal helper to load the database with persistence."""
        return Chroma(
            persist_directory=self.db_directory,
            embedding_function=self.embedding_model,
            collection_name="rag_knowledge_base"
        )

    # ===========================
    # PUBLIC INGESTION API
    # ===========================
    
    def ingest(self, file_path):
        """
        Universal ingestion method that automatically routes to the correct handler
        based on file type.
        Supports: DOCX, PDF (text and scanned), and images (PNG, JPG, etc.)
        """
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found."
        
        # Get file extension
        _, file_ext = os.path.splitext(file_path)
        file_ext = file_ext.lower()
        
        # Route to appropriate handler based on extension
        if file_ext == '.docx':
            return self.ingest_docx(file_path)
        elif file_ext == '.pdf':
            return self.ingest_pdf(file_path)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']:
            return self.ingest_image(file_path)
        else:
            return f"Error: Unsupported file type '{file_ext}'. Supported types: .docx, .pdf, .png, .jpg, .jpeg, .bmp, .tiff, .webp"

    # ===========================
    # FILE TYPE HANDLERS
    # ===========================
    
    # ~~~ DOCX HANDLING ~~~
    
    def ingest_docx(self, file_path):
        """Loads a DOCX file, preserving page structure, chunks it, and saves to DB."""
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found."
            
        print(f"Loading {file_path}...")
        loader = UnstructuredWordDocumentLoader(file_path)
        documents = loader.load()
        
        if not documents:
            return f"Error: No content could be extracted from {file_path}."
        
        # Preserve per-document structure with metadata
        for i, doc in enumerate(documents):
            doc.metadata["source"] = file_path
            doc.metadata["page"] = i + 1
            doc.metadata["file_type"] = "docx"
            if self.subject:
                doc.metadata["subject"] = self.subject
            if self.chapter:
                doc.metadata["chapter"] = self.chapter
        
        return self._process_documents(documents, source=file_path)

    # ~~~ PDF HANDLING ~~~
    
    def ingest_pdf(self, file_path):
        """
        Loads a PDF file, chunks it, and saves to DB.
        Handles both text-based and scanned (image-based) PDFs.
        Uses async processing for improved performance.
        """
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found."
            
        print(f"Loading {file_path}...")
        
        # Check if PDF is scanned or text-based
        if self._is_scanned_pdf(file_path):
            print("Detected scanned PDF. Performing OCR on each page (async)...")
            return self._ingest_scanned_pdf_async(file_path)
        else:
            print("Detected text-based PDF. Extracting text directly...")
            return self._ingest_text_pdf(file_path)

    def _is_scanned_pdf(self, file_path):
        """
        Checks if a PDF is scanned (image-based) or text-based.
        Returns True if scanned, False if text-based.
        """
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                # Check if PDF has at least one page with extractable text
                for page in pdf_reader.pages[:3]:  # Check first 3 pages
                    text = page.extract_text()
                    if text and len(text.strip()) > 100:  # If we find substantial text
                        return False  # It's a text-based PDF
                
                return True  # It's scanned (no substantial text found)
        except Exception as e:
            print(f"Warning: Could not determine PDF type: {e}. Assuming scanned.")
            return True

    def _ingest_text_pdf(self, file_path):
        """Handles text-based PDFs using UnstructuredPDFLoader, preserving page structure."""
        try:
            loader = UnstructuredPDFLoader(file_path)
            documents = loader.load()
            
            if not documents:
                return f"Error: No text could be extracted from {file_path}."
            
            # Preserve per-page metadata
            for i, doc in enumerate(documents):
                doc.metadata["source"] = file_path
                doc.metadata["page"] = i + 1
                doc.metadata["file_type"] = "pdf_text"
                if self.subject:
                    doc.metadata["subject"] = self.subject
                if self.chapter:
                    doc.metadata["chapter"] = self.chapter
            
            return self._process_documents(documents, source=file_path)
        except Exception as e:
            return f"Failed to process text PDF: {str(e)}"

    def _ingest_scanned_pdf(self, file_path):
        """Handles scanned PDFs by performing OCR on each page (async wrapper)."""
        return self._ingest_scanned_pdf_async(file_path)

    @async_to_sync
    async def _ingest_scanned_pdf_async(self, file_path):
        """
        Async version: Handles scanned PDFs by performing OCR on each page asynchronously.
        Preserves structure and metadata.
        """
        try:
            print(f"Converting PDF pages to images...")
            images = convert_from_path(file_path)
            
            documents = []
            temp_dir = tempfile.mkdtemp()
            
            # Process pages concurrently
            tasks = [
                self._process_pdf_page_async(image, page_num, file_path, temp_dir)
                for page_num, image in enumerate(images, 1)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect successful results
            for result in results:
                if isinstance(result, Document):
                    documents.append(result)
                elif isinstance(result, Exception):
                    print(f"Warning: Failed to process page: {result}")
            
            # Clean up temp directory
            try:
                os.rmdir(temp_dir)
            except:
                pass
            
            if not documents:
                return "Warning: No text could be extracted from this scanned PDF."
            
            return self._process_documents(documents, source=file_path)
            
        except Exception as e:
            return f"Failed to process scanned PDF: {str(e)}"

    async def _process_pdf_page_async(self, image, page_num, file_path, temp_dir):
        """
        Async helper to process a single PDF page.
        Returns a Document if successful, None otherwise.
        """
        try:
            print(f"Processing page {page_num}...")
            
            # Save image temporarily
            temp_image_path = os.path.join(temp_dir, f"page_{page_num}.png")
            image.save(temp_image_path, "PNG")
            
            # Extract text using OCR (run in executor to avoid blocking)
            loop = asyncio.get_event_loop()
            page_text = await loop.run_in_executor(
                None, 
                extract_text_preprocessed, 
                temp_image_path
            )
            
            # Clean OCR output
            page_text = self._clean_ocr_text(page_text)
            
            if page_text.strip():
                doc = Document(
                    page_content=page_text,
                    metadata={
                        "source": file_path,
                        "page": page_num,
                        "file_type": "pdf_scanned",
                        "subject": self.subject,
                        "chapter": self.chapter
                    }
                )
                return doc
            
            return None
            
        except Exception as e:
            print(f"Warning: Failed to OCR page {page_num}: {e}")
            return e
        finally:
            if 'temp_image_path' in locals() and os.path.exists(temp_image_path):
                os.remove(temp_image_path)

    # ~~~ IMAGE HANDLING ~~~
    
    def ingest_image(self, image_path):
        """
        Uses OCR to extract text from an image and ingests to vector database.
        """
        if not os.path.exists(image_path):
            return f"Error: Image {image_path} not found."

        print(f"Starting OCR for {image_path}...")
        
        try:
            # Extract text using OCR service
            extracted_text = extract_text_preprocessed(image_path)
            
            # Clean OCR output
            extracted_text = self._clean_ocr_text(extracted_text)
            
            if not extracted_text.strip():
                return "Warning: No text could be extracted from this image."

            print(f"OCR Complete. Extracted {len(extracted_text)} characters.")

            # Create document with metadata
            doc = Document(
                page_content=extracted_text,
                metadata={
                    "source": image_path,
                    "page": 1,
                    "file_type": "image",
                    "subject": self.subject,
                    "chapter": self.chapter
                }
            )
            
            return self._process_documents([doc], source=image_path)

        except Exception as e:
            return f"Failed to process image: {str(e)}"

    # ===========================
    # CORE PROCESSING
    # ===========================
    
    def _clean_ocr_text(self, text):
        """
        Cleans OCR output by removing control characters only.
        Preserves non-ASCII symbols and Unicode characters for multilingual support.
        """
        # Remove only control characters ([\x00-\x1F\x7F]), not non-ASCII symbols
        text = re.sub(r'[\x00-\x1F\x7F]', ' ', text)
        
        # Remove hyphenation across lines
        text = re.sub(r'-\n', '', text)
        
        # Normalize multiple newlines
        text = re.sub(r'\n+', '\n', text)
        
        # Remove extra spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()

    def _process_documents(self, documents, source="unknown"):
        """
        Process documents: chunk, deduplicate, and save to DB.
        Assigns unique chunk_id for traceability and prefixes content for E5 embeddings.
        """
        print(f"Chunking {len(documents)} documents...")
        
        # Chunk each document separately to preserve structure
        all_chunks = []
        for doc in documents:
            chunks = self._chunk_document(doc)
            all_chunks.extend(chunks)
        
        print(f"Generated {len(all_chunks)} chunks before deduplication...")
        
        # Deduplicate chunks using deterministic SHA-256 hashing
        unique_chunks = self._deduplicate_chunks(all_chunks)
        print(f"After deduplication: {len(unique_chunks)} unique chunks")
        
        if not unique_chunks:
            return "Warning: No content to ingest after processing."
        
        # Add chunk_id and apply E5 passage prefix for embedding
        chunks_with_ids = []
        for chunk in unique_chunks:
            chunk.metadata["chunk_id"] = str(uuid.uuid4())
            # Prefix with "passage: " for E5 embedding model
            chunk.page_content = f"passage: {chunk.page_content}"
            chunks_with_ids.append(chunk)
        
        # Add to database
        print(f"Saving {len(chunks_with_ids)} chunks to Vector DB...")
        db = self._get_db()
        db.add_documents(chunks_with_ids)
        print("Database saved successfully (auto-persisted by Chroma).")
        
        return f"Successfully ingested {len(chunks_with_ids)} unique chunks from {source}."

    def _chunk_document(self, document):
        """
        Chunk a single document using semantic chunking with size limits.
        """
        text = document.page_content
        
        # Use semantic chunking with size constraints
        text_splitter = SemanticChunker(
            self.embedding_model,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=92
        )
        
        chunks = text_splitter.create_documents([text])
        
        # Post-process: enforce max size
        final_chunks = []
        for chunk in chunks:
            # If chunk exceeds max size, split further
            if len(chunk.page_content) > self.MAX_CHUNK_SIZE:
                sub_chunks = self._split_large_chunk(chunk)
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)
        
        # Preserve original metadata in all chunks
        for chunk in final_chunks:
            chunk.metadata.update(document.metadata)
        
        return final_chunks

    def _split_large_chunk(self, chunk):
        """
        Split a chunk that exceeds MAX_CHUNK_SIZE into smaller pieces.
        """
        text = chunk.page_content
        words = text.split()
        
        sub_chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            
            if current_size >= self.MAX_CHUNK_SIZE:
                sub_doc = Document(
                    page_content=" ".join(current_chunk),
                    metadata=chunk.metadata.copy()
                )
                sub_chunks.append(sub_doc)
                current_chunk = []
                current_size = 0
        
        # Add remaining words
        if current_chunk:
            sub_doc = Document(
                page_content=" ".join(current_chunk),
                metadata=chunk.metadata.copy()
            )
            sub_chunks.append(sub_doc)
        
        return sub_chunks

    def _deduplicate_chunks(self, chunks):
        """
        Remove duplicate chunks using deterministic SHA-256 hashing.
        Ensures reproducible and collision-safe deduplication.
        """
        unique_texts = set()
        unique_chunks = []
        
        for chunk in chunks:
            # Normalize text and compute SHA-256 hash
            normalized = chunk.page_content.strip().lower()
            text_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            
            if text_hash not in unique_texts:
                unique_texts.add(text_hash)
                unique_chunks.append(chunk)
        
        return unique_chunks
