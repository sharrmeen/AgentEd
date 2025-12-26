"""
AgentEd Backend - Main FastAPI Application.

Dual-layer architecture:
- Service Layer: Pure business logic (stateless, testable)
- Agent Layer: LangGraph orchestration for intelligent workflows

API Routes:
- /api/v1/* → Direct service calls (legacy)
- /api/v2/* → Agent workflows (intelligent)

Database:
- MongoDB: Structured data, cache
- ChromaDB: Vector embeddings for RAG
"""

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging

from app.core.config import settings
from app.core.database import db
from app.api import api_router
from app.schemas.common import HealthResponse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================
# LIFESPAN - App Startup/Shutdown
# ============================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage app lifecycle:
    - Connect to databases on startup
    - Initialize indexes
    - Cleanup on shutdown
    """
    logger.info("🚀 Starting AgentEd Backend...")
    
    try:
        # Connect to MongoDB
        await db.connect()
        logger.info("✅ MongoDB connected")
        
        # Initialize indexes
        await db.init_indexes()
        logger.info("✅ Indexes initialized")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down AgentEd Backend...")
    try:
        await db.close()
        logger.info("✅ MongoDB disconnected")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {str(e)}")

# ============================
# CREATE FASTAPI APP
# ============================

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered study companion with multi-agent orchestration",
    version=settings.APP_VERSION,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# ============================
# MIDDLEWARE
# ============================

# CORS - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["content-length", "content-range"]
)

# Trusted Host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.example.com"]
)

# ============================
# ROUTES
# ============================

# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Status and connection info
    """
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        database="connected"
    )

# Include versioned API routers
app.include_router(
    api_router,
    prefix="/api"
)

# ============================
# ERROR HANDLING
# ============================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
    
    return {
        "success": False,
        "message": "Internal server error",
        "detail": str(exc) if settings.DEBUG else "An error occurred"
    }

# ============================
# STARTUP MESSAGE
# ============================

@app.on_event("startup")
async def startup_message():
    logger.info(f"🎓 AgentEd Backend v{settings.APP_VERSION} is running")
    logger.info(f"📖 Docs available at http://localhost:8000/api/docs")
    logger.info(f"🔗 API endpoints: /api/v1 (services) and /api/v2 (agents)")