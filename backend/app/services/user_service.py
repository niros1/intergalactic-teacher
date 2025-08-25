"""User service for managing user operations."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for user-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get multiple users with pagination."""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = self.get_user_by_email(user_create.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Hash the password
        hashed_password = get_password_hash(user_create.password)
        
        # Create user object
        db_user = User(
            email=user_create.email,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            is_active=True,
            is_verified=False,
        )
        
        # Save to database
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update user information."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Update fields if provided
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        
        if user_update.email is not None:
            # Check if email is already taken
            existing_user = self.get_user_by_email(user_update.email)
            if existing_user and existing_user.id != user_id:
                raise ValueError("Email is already taken")
            user.email = user_update.email
        
        if user_update.password is not None:
            user.hashed_password = get_password_hash(user_update.password)
        
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def deactivate_user(self, user_id: int) -> Optional[User]:
        """Deactivate a user account."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def activate_user(self, user_id: int) -> Optional[User]:
        """Activate a user account."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def verify_user(self, user_id: int) -> Optional[User]:
        """Mark user as verified."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user (hard delete)."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        
        return True