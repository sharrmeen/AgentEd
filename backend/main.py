from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager  # <--- NEW IMPORT

#from dotenv import load_dotenv
# backend/app/main.py
from dotenv import load_dotenv
import os

load_dotenv()

# Import your existing RAG service
from app.services.rag_service import RAGService

# --- NEW IMPORTS FOR DATABASE ---
from app.core.database import db
from app.core.models import StudentProfile
from app.services.user_service import save_profile, get_profile

rag_service = RAGService()

# -------------------------
# 1. Lifespan (The Connection Manager)
# -------------------------
# This code runs before the app starts and after it stops.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB
    db.connect()
    yield
    # Shutdown: Close DB
    db.close()

app = FastAPI(
    title="AgentEd Backend",
    description="Backend API for AgentEd AI system",
    version="0.1.0",
    lifespan=lifespan  # <--- CRITICAL: Attach the lifespan here
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
# 2. NEW: User Setup Endpoints
# -------------------------
# Note: These must be 'async def' because database calls are async.

@app.post("/user/setup")
async def create_user(profile: StudentProfile):
    """
    Creates or updates a user profile in MongoDB.
    Passes the Pydantic model 'StudentProfile' directly to the service.
    """
    await save_profile(profile)
    return {"status": "success", "message": f"Profile saved for {profile.student_id}"}

@app.get("/user/{student_id}")
async def get_user(student_id: str):
    """Retrieves a user profile to verify it was saved."""
    profile = await get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


# -------------------------
# Main Query Endpoint
# -------------------------

@app.post("/query")
def handle_query(request: QueryRequest):
    """
    Temporary direct call to RAG pipeline.
    Later this will be replaced by LangGraph orchestration.
    """
    docs = rag_service.query(request.query)
    return {"response": docs}