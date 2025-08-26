"""User schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, validator

from app.core.config import settings


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    name: str


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long')
        
        # Add more password validation rules as needed
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength if provided."""
        if v is None:
            return v
            
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        return v


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserWithChildren(UserResponse):
    """Schema for user response with children."""
    children: List['ChildResponse'] = []
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class AuthResponse(BaseModel):
    """Schema for authentication response with user data."""
    user: UserResponse
    access_token: str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        return v


# Import child schema for forward reference
from app.schemas.child import ChildResponse
UserWithChildren.update_forward_refs()