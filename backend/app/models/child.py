"""Child model."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Child(Base):
    """Child profile model."""
    
    __tablename__ = "children"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic Information
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    
    # Language and Reading Preferences
    language_preference = Column(
        Enum("hebrew", "english", name="language_enum"), 
        default="english"
    )
    reading_level = Column(
        Enum("beginner", "intermediate", "advanced", name="reading_level_enum"),
        default="beginner"
    )
    
    # Interests (stored as JSON array)
    interests = Column(JSON, default=list)  # ["animals", "adventure", "fantasy", "science"]
    
    # Profile customization
    avatar_url = Column(String)
    
    # Reading progress metrics
    total_stories_completed = Column(Integer, default=0)
    total_reading_time = Column(Integer, default=0)  # in minutes
    current_reading_streak = Column(Integer, default=0)  # days
    longest_reading_streak = Column(Integer, default=0)  # days
    
    # Learning analytics
    vocabulary_words_learned = Column(Integer, default=0)
    reading_level_score = Column(Integer, default=0)  # 0-100 scale
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = relationship("User", back_populates="children")
    story_sessions = relationship("StorySession", back_populates="child", cascade="all, delete-orphan")
    analytics = relationship("UserAnalytics", back_populates="child", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Child(id={self.id}, name='{self.name}', age={self.age})>"
    
    @property
    def reading_preferences(self) -> Dict:
        """Get child's reading preferences for personalization."""
        return {
            "age": self.age,
            "language": self.language_preference,
            "reading_level": self.reading_level,
            "interests": self.interests or [],
            "vocabulary_level": self.reading_level_score,
        }
    
    def update_reading_streak(self) -> None:
        """Update reading streak based on activity."""
        # This would be implemented with logic to check daily activity
        # For now, just a placeholder method
        pass