"""Child schemas for request/response validation."""

from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING, ForwardRef

from pydantic import BaseModel, field_validator

# Create forward references
StorySessionSummaryRef = ForwardRef('StorySessionSummary')
StoryResponseRef = ForwardRef('StoryResponse')


class ChildBase(BaseModel):
    """Base child schema."""
    name: str
    age: int
    language_preference: str = "english"
    reading_level: str = "beginner"
    interests: List[str] = []
    
    @field_validator('age')
    @classmethod
    @classmethod
    def validate_age(cls, v):
        """Validate child age."""
        if v < 7 or v > 12:
            raise ValueError('Child age must be between 7 and 12')
        return v
    
    @field_validator('language_preference')
    @classmethod
    def validate_language(cls, v):
        """Validate language preference."""
        if v not in ['hebrew', 'english']:
            raise ValueError('Language preference must be "hebrew" or "english"')
        return v
    
    @field_validator('reading_level')
    @classmethod
    def validate_reading_level(cls, v):
        """Validate reading level."""
        if v not in ['beginner', 'intermediate', 'advanced']:
            raise ValueError('Reading level must be "beginner", "intermediate", or "advanced"')
        return v
    
    @field_validator('interests')
    @classmethod
    def validate_interests(cls, v):
        """Validate interests list."""
        allowed_interests = [
            'animals', 'adventure', 'fantasy', 'science', 'mystery',
            'friendship', 'family', 'sports', 'music', 'art', 'nature'
        ]
        
        for interest in v:
            if interest not in allowed_interests:
                raise ValueError(f'Interest "{interest}" is not allowed. Allowed interests: {", ".join(allowed_interests)}')
        
        return v


class ChildCreate(ChildBase):
    """Schema for creating a new child profile."""
    pass


class ChildUpdate(BaseModel):
    """Schema for updating child information."""
    name: Optional[str] = None
    age: Optional[int] = None
    language_preference: Optional[str] = None
    reading_level: Optional[str] = None
    interests: Optional[List[str]] = None
    avatar_url: Optional[str] = None
    
    @field_validator('age')
    @classmethod
    def validate_age(cls, v):
        """Validate child age if provided."""
        if v is not None and (v < 7 or v > 12):
            raise ValueError('Child age must be between 7 and 12')
        return v
    
    @field_validator('language_preference')
    @classmethod
    def validate_language(cls, v):
        """Validate language preference if provided."""
        if v is not None and v not in ['hebrew', 'english']:
            raise ValueError('Language preference must be "hebrew" or "english"')
        return v
    
    @field_validator('reading_level')
    @classmethod
    def validate_reading_level(cls, v):
        """Validate reading level if provided."""
        if v is not None and v not in ['beginner', 'intermediate', 'advanced']:
            raise ValueError('Reading level must be "beginner", "intermediate", or "advanced"')
        return v


class ChildResponse(ChildBase):
    """Schema for child response."""
    id: int
    parent_id: int
    avatar_url: Optional[str] = None
    total_stories_completed: int
    total_reading_time: int
    current_reading_streak: int
    longest_reading_streak: int
    vocabulary_words_learned: int
    reading_level_score: int
    created_at: datetime
    updated_at: datetime
    last_active: datetime
    
    model_config = {"from_attributes": True}


class ChildWithProgress(ChildResponse):
    """Schema for child response with reading progress."""
    reading_preferences: Dict
    recent_sessions: List['StorySessionSummary'] = []
    
    model_config = {"from_attributes": True}


class ReadingLevelAssessment(BaseModel):
    """Schema for reading level assessment."""
    questions: List[Dict]
    answers: List[str]


class ReadingLevelResult(BaseModel):
    """Schema for reading level assessment result."""
    reading_level: str
    score: int
    recommendations: List[str]


class ChildDashboard(BaseModel):
    """Schema for child dashboard data."""
    child: ChildResponse
    current_story: Optional['StorySessionSummary'] = None
    recent_achievements: List[str] = []
    reading_streak: int
    stories_this_week: int
    reading_time_today: int
    recommended_stories: List['StoryResponse'] = []


# Resolve forward references after import
def _resolve_forward_refs():
    """Resolve forward references after all schemas are imported."""
    try:
        from app.schemas.story_session import StorySessionSummary
        from app.schemas.story import StoryResponse
        
        # Update forward references
        ChildWithProgress.model_rebuild()
        ChildDashboard.model_rebuild()
    except ImportError:
        # Handle gracefully if imports are not available yet
        pass

# Call resolution function
_resolve_forward_refs()
