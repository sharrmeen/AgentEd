# backend/app/api/deps.py

"""
Dependency injection for FastAPI routes.

Provides:
- Database access
- Authentication (JWT)
- Current user
- Service instances
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from bson import ObjectId

from app.core.config import settings
from app.core.database import db
from app.services.user_service import UserService


# ============================
# JWT SECURITY
# ============================

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )


# ============================
# AUTHENTICATION DEPENDENCIES
# ============================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Get current authenticated user from JWT token.
    
    Returns:
        dict: User data with 'id', 'email', 'name'
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    payload = verify_token(token)
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Fetch user from database
    try:
        user = await UserService.get_user_by_id(ObjectId(user_id))
    except Exception:
        user = None
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role
    }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Ensure user is active."""
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None.
    Used for endpoints that support both authenticated and anonymous access.
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# ============================
# DATABASE DEPENDENCY
# ============================

def get_database():
    """Get database instance."""
    return db.get_db()


# ============================
# OBJECT ID CONVERSION
# ============================

def to_object_id(id_str: str) -> ObjectId:
    """Convert string to ObjectId with validation."""
    if not ObjectId.is_valid(id_str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID format: {id_str}"
        )
    return ObjectId(id_str)


def get_user_id(current_user: dict = Depends(get_current_user)) -> ObjectId:
    """Get current user's ObjectId."""
    return ObjectId(current_user["id"])
