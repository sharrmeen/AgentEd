import os
from app.services.rag_service import RAGService

def main():

    rag = RAGService()
    
    # --- Ingest DOCX Notes ---

    docx_file_path = "data/MODULE 3 NOTES.docx"
    

    if not os.path.exists(docx_file_path):
        print(f"Error: Source document not found at {docx_file_path}")
        return

    print("--- Starting RAG Database Seeding ---")
    
    # Run the ingestion method 
    ingestion_result = rag.ingest_docx(docx_file_path)
    print(ingestion_result)
    
   
    print("\n--- Verifying Semantic Search ---")
    query = "What is the main difference between Bagging and Boosting?"
    relevant_chunks = rag.query(query)
    
    print(f"Query: '{query}'")
    print(f"Retrieved {len(relevant_chunks)} chunks for verification.")
    
    if relevant_chunks:
        print("\nExample of Retrieved Chunk:")
        print(relevant_chunks[0][:300] + "...") 
    else:
        print("Verification failed: No chunks were retrieved.")

if __name__ == "__main__":
    main()