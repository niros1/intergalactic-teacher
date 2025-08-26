"""Authentication endpoints."""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_db, get_refresh_token_user_id
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password_reset_token,
    generate_password_reset_token
)
from app.schemas.user import (
    LoginRequest,
    TokenResponse,
    AuthResponse,
    UserCreate,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    RefreshTokenRequest
)
from app.services.user_service import UserService
from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """Register a new user."""
    try:
        user_service = UserService(db)
        
        # Check rate limiting
        client_ip = "unknown"  # Would get from request in real implementation
        is_allowed, remaining = await redis_client.rate_limit_check(
            f"register:{client_ip}",
            limit=5,  # 5 registrations per hour
            window=3600
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many registration attempts. Please try again later."
            )
        
        # Create the user
        user = user_service.create_user(user_data)
        
        # Generate tokens for the new user
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        # Store refresh token in Redis
        await redis_client.set(
            f"refresh_token:{user.id}",
            refresh_token,
            expire=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        )
        
        # Cache user session
        await redis_client.cache_user_session(
            user.id,
            {
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "last_login": None,
            }
        )
        
        logger.info(f"New user registered: {user.email}")
        
        # Convert User model to UserResponse
        user_response = UserResponse.model_validate(user)
        
        # Return AuthResponse with user data
        auth_response = AuthResponse(
            user=user_response,
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        return auth_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> Any:
    """Authenticate user and return tokens."""
    try:
        user_service = UserService(db)
        
        # Check rate limiting
        is_allowed, remaining = await redis_client.rate_limit_check(
            f"login:{login_data.email}",
            limit=200,  # 200 login attempts per hour
            window=3600
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        # Authenticate user
        user = user_service.authenticate_user(login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        # Store refresh token in Redis
        await redis_client.set(
            f"refresh_token:{user.id}",
            refresh_token,
            expire=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        )
        
        # Cache user session
        await redis_client.cache_user_session(
            user.id,
            {
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "last_login": user.last_login.isoformat() if user.last_login else None,
            }
        )
        
        logger.info(f"User logged in: {user.email}")
        
        # Convert User model to UserResponse
        user_response = UserResponse.model_validate(user)
        
        # Return AuthResponse with user data
        auth_response = AuthResponse(
            user=user_response,
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        return auth_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed for {login_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    """Refresh access token using refresh token."""
    try:
        # Validate refresh token and get user ID
        from app.core.security import verify_token
        user_id_str = verify_token(refresh_data.refresh_token, "refresh")
        
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = int(user_id_str)
        
        # Verify user still exists and is active
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        tokens = create_token_response(user.id)
        
        # Update cached session
        await redis_client.cache_user_session(
            user.id,
            {
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "last_login": datetime.utcnow().isoformat(),
            }
        )
        
        logger.info(f"Token refreshed for user: {user.email}")
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    user_id: int = Depends(get_refresh_token_user_id)
) -> Any:
    """Logout user and invalidate session."""
    try:
        # Invalidate cached session
        await redis_client.invalidate_user_session(user_id)
        
        logger.info(f"User logged out: {user_id}")
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout failed for user {user_id}: {e}")
        # Don't raise exception for logout - return success anyway
        return {"message": "Logged out"}


@router.post("/forgot-password")
async def forgot_password(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> Any:
    """Send password reset email."""
    try:
        user_service = UserService(db)
        
        # Check rate limiting
        is_allowed, remaining = await redis_client.rate_limit_check(
            f"password_reset:{reset_data.email}",
            limit=3,  # 3 reset attempts per hour
            window=3600
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many password reset attempts. Please try again later."
            )
        
        # Check if user exists
        user = user_service.get_user_by_email(reset_data.email)
        
        if user:
            # Generate reset token
            reset_token = generate_password_reset_token(reset_data.email)
            
            # In a real implementation, send email with reset token
            # For now, just log it (or return it in development)
            logger.info(f"Password reset token generated for {reset_data.email}: {reset_token}")
            
            # Cache the reset token for validation
            await redis_client.set(
                f"password_reset_token:{reset_data.email}",
                reset_token,
                expire=86400  # 24 hours
            )
        
        # Always return success to prevent email enumeration
        return {"message": "If the email exists, a password reset link has been sent"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed for {reset_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> Any:
    """Reset password using reset token."""
    try:
        # Verify reset token
        email = verify_password_reset_token(reset_data.token)
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Verify token is in cache (additional security)
        cached_token = await redis_client.get(f"password_reset_token:{email}")
        if cached_token != reset_data.token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        user_service = UserService(db)
        user = user_service.get_user_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        user.hashed_password = get_password_hash(reset_data.new_password)
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Clear reset token from cache
        await redis_client.delete(f"password_reset_token:{email}")
        
        # Invalidate all user sessions
        await redis_client.invalidate_user_session(user.id)
        
        logger.info(f"Password reset successful for: {email}")
        return {"message": "Password reset successful"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirmation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )