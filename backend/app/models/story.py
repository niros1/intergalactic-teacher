"""Story models."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Story(Base):
    """Story model."""
    
    __tablename__ = "stories"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Story content
    title = Column(String, nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)  # Main story content
    
    # Story metadata
    language = Column(
        Enum("hebrew", "english", name="story_language_enum"),
        nullable=False
    )
    difficulty_level = Column(
        Enum("beginner", "intermediate", "advanced", name="story_difficulty_enum"),
        nullable=False
    )
    
    # Classification
    themes = Column(JSON, default=list)  # ["adventure", "friendship", "animals"]
    target_age_min = Column(Integer, default=7)
    target_age_max = Column(Integer, default=12)
    estimated_reading_time = Column(Integer, default=10)  # in minutes
    
    # Story structure
    total_chapters = Column(Integer, default=1)
    has_choices = Column(Boolean, default=True)
    
    # AI Generation metadata
    generated_by_ai = Column(Boolean, default=True)
    generation_prompt = Column(Text)  # Store the prompt used to generate
    content_safety_score = Column(Float, default=1.0)  # 0-1, higher is safer
    
    # Publishing
    is_published = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)  # For story templates
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    choices = relationship("Choice", back_populates="story", cascade="all, delete-orphan")
    branches = relationship("StoryBranch", back_populates="story", cascade="all, delete-orphan")
    sessions = relationship("StorySession", back_populates="story")
    chapters = relationship("StoryChapter", back_populates="story", cascade="all, delete-orphan", order_by="StoryChapter.chapter_number")
    
    def __repr__(self) -> str:
        return f"<Story(id={self.id}, title='{self.title[:30]}...')>"


class Choice(Base):
    """Story choice points model."""
    
    __tablename__ = "choices"
    
    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    
    # Choice metadata
    chapter_number = Column(Integer, default=1)
    position_in_chapter = Column(Integer, default=1)  # Where in the chapter this choice appears
    
    # Choice content
    question = Column(Text, nullable=False)  # The choice prompt/question
    choices_data = Column(JSON, nullable=False)  # Array of choice options
    
    # Choice logic
    default_choice_index = Column(Integer, default=0)
    is_critical_choice = Column(Boolean, default=False)  # Affects story outcome significantly
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    story = relationship("Story", back_populates="choices")
    branches = relationship("StoryBranch", back_populates="choice", foreign_keys="StoryBranch.choice_id")
    
    def __repr__(self) -> str:
        return f"<Choice(id={self.id}, story_id={self.story_id})>"


class StoryBranch(Base):
    """Story branches based on choices."""
    
    __tablename__ = "story_branches"
    
    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    choice_id = Column(Integer, ForeignKey("choices.id"), nullable=False)
    
    # Branch identification
    choice_option_index = Column(Integer, nullable=False)  # Which choice option leads here
    branch_name = Column(String)  # Optional name for the branch
    
    # Branch content
    content = Column(Text, nullable=False)  # Content for this branch
    
    # Branch flow
    leads_to_chapter = Column(Integer)  # Next chapter number
    leads_to_choice_id = Column(Integer, ForeignKey("choices.id"))  # Next choice
    is_ending = Column(Boolean, default=False)  # Is this a story ending?
    
    # Branch metadata
    difficulty_modifier = Column(Float, default=1.0)  # Difficulty adjustment for this branch
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    story = relationship("Story", back_populates="branches")
    choice = relationship("Choice", back_populates="branches", foreign_keys=[choice_id])
    next_choice = relationship("Choice", foreign_keys=[leads_to_choice_id], overlaps="branches")
    
    def __repr__(self) -> str:
        return f"<StoryBranch(id={self.id}, choice_id={self.choice_id}, option={self.choice_option_index})>"