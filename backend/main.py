from fastapi import FastAPI
from pydantic import BaseModel

# Import your existing RAG service
from app.services.rag_service import RAGService
rag_service = RAGService()


app = FastAPI(
    title="AgentEd Backend",
    description="Backend API for AgentEd AI system",
    version="0.1.0"
)

# -------------------------
# Request / Response Models
# -------------------------

class QueryRequest(BaseModel):
    user_id: str
    query: str

class QueryResponse(BaseModel):
    response: str


# -------------------------
# Health Check
# -------------------------

@app.get("/")
def health_check():
    return {"status": "AgentEd backend is running"}


# -------------------------
# Main Query Endpoint
# -------------------------

@app.post("/query")
def handle_query(request: QueryRequest):
    docs = rag_service.query(request.query)
    return {"response": docs}

"""
    Temporary direct call to RAG pipeline.
    Later this will be replaced by LangGraph orchestration.
    """