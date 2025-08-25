"""Story session model."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class StorySession(Base):
    """Story reading session model."""
    
    __tablename__ = "story_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    
    # Session progress
    current_chapter = Column(Integer, default=1)
    current_choice_id = Column(Integer, ForeignKey("choices.id"))
    choices_made = Column(JSON, default=list)  # Array of choice selections
    
    # Session state
    is_completed = Column(Boolean, default=False)
    is_bookmarked = Column(Boolean, default=False)
    completion_percentage = Column(Integer, default=0)  # 0-100
    
    # Reading metrics for this session
    session_duration = Column(Integer, default=0)  # in seconds
    words_read = Column(Integer, default=0)
    audio_playback_used = Column(Boolean, default=False)
    audio_playback_duration = Column(Integer, default=0)  # in seconds
    
    # Engagement metrics
    choices_engagement_rate = Column(Integer, default=0)  # percentage of choices engaged with
    reading_speed_wpm = Column(Integer, default=0)  # words per minute
    pause_count = Column(Integer, default=0)  # how many times reading was paused
    
    # Learning outcomes
    vocabulary_encountered = Column(JSON, default=list)  # New words encountered
    comprehension_score = Column(Integer)  # 0-100 if quiz taken
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    child = relationship("Child", back_populates="story_sessions")
    story = relationship("Story", back_populates="sessions")
    current_choice = relationship("Choice", foreign_keys=[current_choice_id])
    
    def __repr__(self) -> str:
        return f"<StorySession(id={self.id}, child_id={self.child_id}, story_id={self.story_id})>"
    
    @property
    def session_summary(self) -> Dict:
        """Get session summary for analytics."""
        return {
            "session_id": self.id,
            "story_title": self.story.title if self.story else "Unknown",
            "completion_percentage": self.completion_percentage,
            "duration_minutes": self.session_duration // 60,
            "words_read": self.words_read,
            "choices_made": len(self.choices_made or []),
            "audio_used": self.audio_playback_used,
            "completed": self.is_completed,
            "date": self.started_at.date() if self.started_at else None,
        }
    
    def add_choice(self, choice_id: int, option_index: int) -> None:
        """Add a choice to the session."""
        if not self.choices_made:
            self.choices_made = []
        
        choice_data = {
            "choice_id": choice_id,
            "option_index": option_index,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.choices_made.append(choice_data)
    
    def calculate_engagement_rate(self) -> int:
        """Calculate engagement rate based on choices made vs available."""
        # This would calculate based on story structure
        # For now, placeholder implementation
        return min(100, len(self.choices_made or []) * 20)