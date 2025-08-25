"""User management endpoints."""

import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserWithChildren
from app.services.user_service import UserService
from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserWithChildren)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get current user profile with children."""
    try:
        # Check cache first
        cached_profile = await redis_client.get_user_session(current_user.id)
        if cached_profile:
            logger.info(f"Returning cached profile for user: {current_user.id}")
        
        return current_user
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update current user profile."""
    try:
        user_service = UserService(db)
        
        # Update the user
        updated_user = user_service.update_user(current_user.id, user_update)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Invalidate cached session
        await redis_client.invalidate_user_session(current_user.id)
        
        logger.info(f"User profile updated: {current_user.id}")
        return updated_user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.delete("/me")
async def delete_current_user_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete current user account (soft delete - deactivate)."""
    try:
        user_service = UserService(db)
        
        # Deactivate user instead of hard delete for data integrity
        deactivated_user = user_service.deactivate_user(current_user.id)
        
        if not deactivated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Invalidate all user sessions
        await redis_client.invalidate_user_session(current_user.id)
        
        logger.info(f"User account deactivated: {current_user.id}")
        return {"message": "Account successfully deactivated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )


@router.post("/me/reactivate", response_model=UserResponse)
async def reactivate_user_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Reactivate a deactivated user account."""
    try:
        user_service = UserService(db)
        
        # Activate user
        activated_user = user_service.activate_user(current_user.id)
        
        if not activated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User account reactivated: {current_user.id}")
        return activated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reactivating user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate account"
        )