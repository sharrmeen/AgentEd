# backend/app/api/v1/auth.py

"""
Authentication endpoints - Admin-provisioned accounts, login, and profile management.
"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Query
from bson import ObjectId

from app.services.user_service import UserService
from app.schemas.auth import (
    AdminCreateUserRequest,
    UserLoginRequest,
    PasswordChangeRequest,
    ProfileUpdateRequest,
    ClassAssignmentRequest,
    UserResponse,
    TokenResponse,
    LearningProfileResponse
)
from app.api.deps import (
    get_current_user,
    create_access_token,
    get_user_id
)
from app.core.config import settings

router = APIRouter()


@router.post("/admin/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    request: AdminCreateUserRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a student or teacher account (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create users"
        )

    try:
        created_user = await UserService.create_user_by_admin(
            name=request.name,
            username=request.username,
            password=request.password,
            role=request.role,
            class_id=request.class_id,
            email=request.email,
            must_change_password=request.must_change_password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return UserResponse(
        id=str(created_user.id),
        name=created_user.name,
        username=created_user.username,
        email=created_user.email,
        role=created_user.role,
        class_id=created_user.class_id,
        must_change_password=created_user.must_change_password,
        is_active=created_user.is_active,
        learning_profile=None,
        created_at=created_user.created_at,
        last_login=created_user.last_login
    )


@router.get("/admin/users")
async def admin_list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    role: str | None = None,
    search: str | None = None,
    current_user: dict = Depends(get_current_user)
):
    """List users with optional role/search filters (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view users"
        )

    users, total = await UserService.list_users(
        skip=skip,
        limit=limit,
        role=role,
        search=search,
    )

    return {
        "users": [
            {
                "id": str(user.id),
                "name": user.name,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "class_id": user.class_id,
                "must_change_password": user.must_change_password,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "last_login": user.last_login,
            }
            for user in users
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest):
    """
    Login user with username and password.
    
    Args:
        request: Login credentials (email, password)
        
    Returns:
        JWT token and user info
    """
    # Get user by username
    user = await UserService.get_user_by_username(request.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    password_valid = await UserService.verify_password(
        request.password,
        user.password_hash
    )
    
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    await UserService.mark_last_login(ObjectId(user.id))
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=str(user.id),
        username=user.username,
        name=user.name,
        role=user.role,
        class_id=user.class_id,
        must_change_password=user.must_change_password,
    )


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Change password and clear first-login password reset requirement."""
    try:
        await UserService.update_password(
            user_id=ObjectId(current_user["id"]),
            current_password=request.current_password,
            new_password=request.new_password,
            email=request.email,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return {"success": True, "message": "Password updated successfully"}


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
        username=user.username,
        email=user.email,
        role=user.role,
        class_id=user.class_id,
        must_change_password=user.must_change_password,
        is_active=user.is_active,
        learning_profile=learning_profile_response,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    request: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update current authenticated user's profile fields."""
    try:
        updated_user = await UserService.update_profile(
            user_id=ObjectId(current_user["id"]),
            name=request.name,
            email=request.email,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    learning_profile_response = None
    if updated_user.learning_profile:
        learning_profile_response = LearningProfileResponse(
            subjects=updated_user.learning_profile.subjects or {},
            total_study_hours=updated_user.learning_profile.total_study_hours or 0.0,
            total_quizzes_completed=updated_user.learning_profile.total_quizzes_completed or 0,
            total_objectives_completed=updated_user.learning_profile.total_objectives_completed or 0,
            learning_style=updated_user.learning_profile.learning_style,
            difficulty_preference=updated_user.learning_profile.difficulty_preference,
            streak_days=updated_user.learning_profile.streak_days or 0,
            last_active=updated_user.learning_profile.last_active
        )

    return UserResponse(
        id=str(updated_user.id),
        name=updated_user.name,
        username=updated_user.username,
        email=updated_user.email,
        role=updated_user.role,
        class_id=updated_user.class_id,
        must_change_password=updated_user.must_change_password,
        is_active=updated_user.is_active,
        learning_profile=learning_profile_response,
        created_at=updated_user.created_at,
        last_login=updated_user.last_login
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


@router.patch("/admin/users/{target_user_id}/class", response_model=UserResponse)
async def assign_student_class(
    target_user_id: str,
    request: ClassAssignmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Assign or clear class_id for a student account (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign classes"
        )

    try:
        target_obj_id = ObjectId(target_user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    try:
        updated_user = await UserService.assign_class_to_student(
            user_id=target_obj_id,
            class_id=request.class_id
        )
    except ValueError as e:
        detail = str(e)
        status_code = status.HTTP_404_NOT_FOUND if detail == "User not found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail)

    return UserResponse(
        id=str(updated_user.id),
        name=updated_user.name,
        username=updated_user.username,
        email=updated_user.email,
        role=updated_user.role,
        class_id=updated_user.class_id,
        must_change_password=updated_user.must_change_password,
        is_active=updated_user.is_active,
        learning_profile=None,
        created_at=updated_user.created_at,
        last_login=updated_user.last_login
    )
