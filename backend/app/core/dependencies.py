"""FastAPI dependencies for authentication and database access."""

from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.db.base import get_db
from app.models.user import User
from app.services.user_service import UserService

# HTTP Bearer token scheme
security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """Get current user ID from JWT token."""
    token = credentials.credentials
    
    user_id_str = verify_token(token, "access")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


def get_current_user(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
) -> User:
    """Get current authenticated user."""
    user_service = UserService(db)
    user = user_service.get_user_by_id(current_user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (alias for consistency)."""
    return current_user


def get_refresh_token_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """Get user ID from refresh token."""
    token = credentials.credentials
    
    user_id_str = verify_token(token, "refresh")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


class ChildAccessDependency:
    """Dependency to check if user can access a child profile."""
    
    def __init__(self, child_id: int):
        self.child_id = child_id
    
    def __call__(
        self,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if user can access the child profile."""
        # Check if the child belongs to the current user
        child_ids = [child.id for child in current_user.children]
        
        if self.child_id not in child_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this child profile"
            )
        
        return current_user


def get_child_access_dependency(child_id: int) -> ChildAccessDependency:
    """Factory function to create child access dependency."""
    return ChildAccessDependency(child_id)