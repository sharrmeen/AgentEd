import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.core.database import db
from app.api import api_router
from app.schemas.common import HealthResponse
from app.services.user_service import UserService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AgentEd Backend...")
    
    try:
        await db.connect()
        logger.info("MongoDB connected")
        
        await db.init_indexes()
        logger.info("Indexes initialized")

        await UserService.ensure_default_admin()
        logger.info("Default admin account ensured")

        logger.info(f"AgentEd Backend v{settings.APP_VERSION} is running")
        logger.info("Docs available at /api/docs")
        logger.info("API endpoints: /api/v1 (user-facing chat, notes, quiz, etc.)")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    
    yield
    
    logger.info("Shutting down AgentEd Backend...")
    try:
        await db.close()
        logger.info("MongoDB disconnected")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered study companion with multi-agent orchestration",
    version=settings.APP_VERSION,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["content-length", "content-range"]
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS or ["*"]
)

@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        database="connected"
    )

app.include_router(
    api_router,
    prefix="/api"
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
    
    return JSONResponse(status_code=500, content={
        "success": False,
        "message": "Internal server error",
        "detail": str(exc) if settings.DEBUG else "An error occurred"
    })

