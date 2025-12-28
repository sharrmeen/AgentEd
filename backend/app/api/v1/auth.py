# backend/app/api/v1/auth.py

"""
Authentication endpoints - User registration, login, and profile management.
"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId

from app.services.user_service import UserService
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    LearningProfileResponse
)
from app.api.deps import (
    get_current_user,
    create_access_token,
    get_optional_user,
    get_user_id
)
from app.core.config import settings

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest):
    """
    Register a new user.
    
    Args:
        request: Registration data (name, email, password)
        
    Returns:
        JWT token and user info
    """
    try:
        user = await UserService.create_user(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=str(user.id),
        email=user.email,
        name=user.name
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest):
    """
    Login user with email and password.
    
    Args:
        request: Login credentials (email, password)
        
    Returns:
        JWT token and user info
    """
    # Get user by email
    user = await UserService.get_user_by_email(request.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    password_valid = await UserService.verify_password(
        request.password,
        user.password_hash
    )
    
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=str(user.id),
        email=user.email,
        name=user.name
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's profile.
    
    Returns:
        User profile including learning profile
    """
    user = await UserService.get_user_by_id(ObjectId(current_user["id"]))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Convert LearningProfile to LearningProfileResponse
    learning_profile_response = None
    if user.learning_profile:
        learning_profile_response = LearningProfileResponse(
            subjects=user.learning_profile.subjects or {},
            total_study_hours=user.learning_profile.total_study_hours or 0.0,
            total_quizzes_completed=user.learning_profile.total_quizzes_completed or 0,
            total_objectives_completed=user.learning_profile.total_objectives_completed or 0,
            learning_style=user.learning_profile.learning_style,
            difficulty_preference=user.learning_profile.difficulty_preference,
            streak_days=user.learning_profile.streak_days or 0,
            last_active=user.learning_profile.last_active
        )
    
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        learning_profile=learning_profile_response,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.get("/profile/learning", response_model=LearningProfileResponse)
async def get_learning_profile(
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Get user's learning profile with performance analytics.
    
    Returns:
        Comprehensive learning profile
    """
    profile = await UserService.get_learning_profile(user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning profile not found"
        )
    
    return LearningProfileResponse(**profile.dict())
