"""User analytics model."""

from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import JSON, Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserAnalytics(Base):
    """User analytics and learning progress model."""
    
    __tablename__ = "user_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    
    # Date tracking
    date = Column(Date, nullable=False)  # Date of the analytics record
    
    # Daily reading metrics
    sessions_count = Column(Integer, default=0)
    total_reading_time = Column(Integer, default=0)  # in seconds
    words_read = Column(Integer, default=0)
    stories_completed = Column(Integer, default=0)
    stories_started = Column(Integer, default=0)
    
    # Engagement metrics
    average_session_duration = Column(Integer, default=0)  # in seconds
    choices_made = Column(Integer, default=0)
    audio_playback_time = Column(Integer, default=0)  # in seconds
    pause_frequency = Column(Float, default=0.0)  # pauses per minute
    
    # Learning progress
    reading_speed_wpm = Column(Integer, default=0)  # words per minute
    comprehension_score = Column(Float, default=0.0)  # 0-100 average
    vocabulary_words_learned = Column(Integer, default=0)
    reading_level_improvement = Column(Float, default=0.0)  # change from baseline
    
    # Content preferences (derived from choices)
    preferred_themes = Column(JSON, default=list)  # themes child gravitates toward
    preferred_difficulty = Column(String)  # current comfort level
    
    # Behavioral insights
    best_reading_time = Column(String)  # "morning", "afternoon", "evening"
    attention_span_minutes = Column(Integer, default=0)
    return_likelihood = Column(Float, default=0.0)  # 0-1 probability
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    child = relationship("Child", back_populates="analytics")
    
    def __repr__(self) -> str:
        return f"<UserAnalytics(id={self.id}, child_id={self.child_id}, date={self.date})>"
    
    @property
    def engagement_level(self) -> str:
        """Calculate engagement level based on metrics."""
        # Simple engagement calculation
        if self.average_session_duration >= 900:  # 15+ minutes
            return "high"
        elif self.average_session_duration >= 300:  # 5+ minutes
            return "medium"
        else:
            return "low"
    
    @property
    def learning_velocity(self) -> str:
        """Calculate learning velocity."""
        if self.reading_level_improvement > 0.1:
            return "accelerating"
        elif self.reading_level_improvement > 0:
            return "steady"
        else:
            return "needs_attention"
    
    def to_dashboard_summary(self) -> Dict:
        """Convert to dashboard-friendly summary."""
        return {
            "date": self.date.isoformat() if self.date else None,
            "reading_time_minutes": self.total_reading_time // 60,
            "stories_completed": self.stories_completed,
            "engagement_level": self.engagement_level,
            "reading_speed": self.reading_speed_wpm,
            "comprehension_score": round(self.comprehension_score, 1),
            "vocabulary_learned": self.vocabulary_words_learned,
            "preferred_themes": self.preferred_themes or [],
            "learning_velocity": self.learning_velocity,
        }