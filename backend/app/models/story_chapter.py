"""Story chapter model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base


class StoryChapter(Base):
    """Story chapter model for storing individual chapters."""
    
    __tablename__ = "story_chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False, index=True)
    
    # Chapter metadata
    chapter_number = Column(Integer, nullable=False)
    title = Column(String, nullable=True)  # Optional chapter title
    content = Column(Text, nullable=False)  # Chapter content
    
    # Generation metadata
    created_from_choice_id = Column(Integer, ForeignKey("choices.id"), nullable=True)
    created_from_branch_id = Column(Integer, ForeignKey("story_branches.id"), nullable=True)
    
    # Chapter state
    is_ending = Column(Boolean, default=False)  # Is this a story ending?
    is_published = Column(Boolean, default=True)  # Is chapter available to read?
    
    # Reading time estimate
    estimated_reading_time = Column(Integer, default=5)  # in minutes
    word_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    story = relationship("Story", back_populates="chapters")
    created_from_choice = relationship("Choice", foreign_keys=[created_from_choice_id])
    created_from_branch = relationship("StoryBranch", foreign_keys=[created_from_branch_id])
    
    def __repr__(self) -> str:
        return f"<StoryChapter(id={self.id}, story_id={self.story_id}, chapter={self.chapter_number})>"
    
    @property
    def word_count_actual(self) -> int:
        """Calculate actual word count from content."""
        if self.content:
            return len(self.content.split())
        return 0