
import os
from app.services.rag_service import RAGService
from dotenv import load_dotenv
load_dotenv()

def main():
    # Initialize RAGService with subject and chapter context
    rag = RAGService(subject="Machine Learning", chapter="Module 3")

    # --- Ingest Documents ---
    documents_to_ingest = [
        "data/MODULE 3 NOTES.docx",
        # Add more documents here:
        # "data/scanned_book.pdf",
        # "data/handwritten_notes.png",
    ]

    print("--- Starting RAG Database Seeding ---")
    for doc_path in documents_to_ingest:
        if not os.path.exists(doc_path):
            print(f"Warning: Document not found at {doc_path}")
            continue
        print(f"\nIngesting: {doc_path}")
        ingestion_result = rag.ingest(doc_path)
        print(ingestion_result)

    print("\n--- Verifying Semantic Search ---")
    query = "What is the main difference between Bagging and Boosting?"

    # Query with all new features enabled
    relevant_results = rag.query(
        query,
        k=3,
        subject="Machine Learning",
        chapter="Module 3",
        include_neighbors=True
    )

    print(f"Query: '{query}'")
    print(f"Retrieved {len(relevant_results)} results for verification.")

    if relevant_results:
        print("\nExample of Retrieved Results:")
        for idx, result in enumerate(relevant_results):
            print(f"\nResult #{idx+1}:")
            print(f"Content: {result['content'][:300]}...")
            print(f"Metadata: {result['metadata']}")
            print(f"Confidence: {result.get('confidence')}")
            print(f"Chunk ID: {result.get('chunk_id')}")
            print(f"Is Neighbor: {result.get('is_neighbor', False)}")
    else:
        print("Verification failed: No results were retrieved.")

if __name__ == "__main__":
    main()