"""Story session schemas for request/response validation."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, validator


class StorySessionBase(BaseModel):
    """Base story session schema."""
    child_id: int
    story_id: int


class StorySessionCreate(StorySessionBase):
    """Schema for creating a story session."""
    pass


class StorySessionUpdate(BaseModel):
    """Schema for updating a story session."""
    current_chapter: Optional[int] = None
    choices_made: Optional[List[Dict]] = None
    is_completed: Optional[bool] = None
    is_bookmarked: Optional[bool] = None
    completion_percentage: Optional[int] = None
    
    @validator('completion_percentage')
    def validate_completion_percentage(cls, v):
        """Validate completion percentage."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Completion percentage must be between 0 and 100')
        return v


class StorySessionResponse(StorySessionBase):
    """Schema for story session response."""
    id: int
    current_chapter: int
    current_choice_id: Optional[int]
    choices_made: List[Dict]
    is_completed: bool
    is_bookmarked: bool
    completion_percentage: int
    session_duration: int
    words_read: int
    audio_playback_used: bool
    audio_playback_duration: int
    choices_engagement_rate: int
    reading_speed_wpm: int
    pause_count: int
    vocabulary_encountered: List[str]
    comprehension_score: Optional[int]
    started_at: datetime
    last_accessed: datetime
    completed_at: Optional[datetime]
    
    class Config:
        orm_mode = True


class StorySessionWithStory(StorySessionResponse):
    """Schema for story session with story details."""
    story: 'StoryResponse'
    
    class Config:
        orm_mode = True


class StorySessionSummary(BaseModel):
    """Schema for story session summary."""
    session_id: int
    story_title: str
    completion_percentage: int
    duration_minutes: int
    words_read: int
    choices_made: int
    audio_used: bool
    completed: bool
    date: Optional[str]


class ReadingProgress(BaseModel):
    """Schema for reading progress tracking."""
    session_id: int
    words_read: int
    reading_time: int
    current_position: str
    audio_playback_time: Optional[int] = 0
    pause_count: Optional[int] = 0


class ComprehensionQuiz(BaseModel):
    """Schema for comprehension quiz."""
    session_id: int
    questions: List[Dict[str, str]]
    answers: List[str]


class ComprehensionResult(BaseModel):
    """Schema for comprehension quiz result."""
    score: int
    correct_answers: int
    total_questions: int
    feedback: List[str]


# Forward references
from app.schemas.story import StoryResponse
StorySessionWithStory.update_forward_refs()