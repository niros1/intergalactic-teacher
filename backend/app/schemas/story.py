"""Story schemas for request/response validation."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class StoryBase(BaseModel):
    """Base story schema."""
    title: str
    description: Optional[str] = None
    language: str = "english"
    difficulty_level: str = "beginner"
    themes: List[str] = []
    
    @validator('language')
    def validate_language(cls, v):
        """Validate language."""
        if v not in ['hebrew', 'english']:
            raise ValueError('Language must be "hebrew" or "english"')
        return v
    
    @validator('difficulty_level')
    def validate_difficulty_level(cls, v):
        """Validate difficulty level."""
        if v not in ['beginner', 'intermediate', 'advanced']:
            raise ValueError('Difficulty level must be "beginner", "intermediate", or "advanced"')
        return v


class StoryCreate(BaseModel):
    """Schema for creating a story."""
    theme: str
    title: Optional[str] = None
    total_chapters: int = 3
    
    @validator('total_chapters')
    def validate_chapters(cls, v):
        """Validate chapter count."""
        if v < 1 or v > 10:
            raise ValueError('Total chapters must be between 1 and 10')
        return v


class StoryResponse(StoryBase):
    """Schema for story response."""
    id: int
    content: str
    target_age_min: int
    target_age_max: int
    estimated_reading_time: int
    total_chapters: int
    has_choices: bool
    generated_by_ai: bool
    content_safety_score: float
    is_published: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class StoryWithChoices(StoryResponse):
    """Schema for story with choices."""
    choices: List['ChoiceResponse'] = []
    
    class Config:
        from_attributes = True


class SimpleChoice(BaseModel):
    """Simplified choice schema for frontend."""
    id: str
    text: str
    impact: str = "normal"
    nextChapter: Optional[int] = None
    
    class Config:
        from_attributes = True


class StoryWithProgress(StoryResponse):
    """Schema for story with reading progress."""
    choices: List[SimpleChoice] = []
    current_chapter: int = 1
    is_completed: bool = False
    completion_percentage: int = 0
    
    class Config:
        from_attributes = True


class ChoiceBase(BaseModel):
    """Base choice schema."""
    question: str
    choices_data: List[Dict[str, str]]


class ChoiceResponse(ChoiceBase):
    """Schema for choice response."""
    id: int
    story_id: int
    chapter_number: int
    position_in_chapter: int
    default_choice_index: int
    is_critical_choice: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class StoryBranchResponse(BaseModel):
    """Schema for story branch response."""
    id: int
    story_id: int
    choice_id: int
    choice_option_index: int
    branch_name: Optional[str]
    content: str
    leads_to_chapter: Optional[int]
    leads_to_choice_id: Optional[int]
    is_ending: bool
    
    class Config:
        from_attributes = True


class StoryGenerationRequest(BaseModel):
    """Schema for story generation request."""
    child_id: int = Field(alias="childId")
    theme: str
    title: Optional[str] = None
    chapter_number: int = Field(default=1, alias="chapterNumber")
    
    class Config:
        populate_by_name = True


class StoryGenerationResponse(BaseModel):
    """Schema for story generation response."""
    success: bool
    story_content: str
    choices: List[Dict[str, str]]
    educational_elements: List[str]
    estimated_reading_time: int
    safety_score: float
    error: Optional[str] = None


class ChoiceSelectionRequest(BaseModel):
    """Schema for making a story choice."""
    choice_id: str = Field(alias="choiceId")
    timestamp: Optional[str] = None
    option_index: Optional[int] = Field(default=0, alias="optionIndex")
    
    class Config:
        populate_by_name = True


class StoryRecommendation(BaseModel):
    """Schema for story recommendations."""
    stories: List[StoryResponse]
    recommendation_reason: str
    personalized: bool


class ContentSafetyCheck(BaseModel):
    """Schema for content safety check response."""
    is_safe: bool
    safety_score: float
    issues: List[Dict[str, str]]
    recommendations: List[str]
    needs_review: bool


# Forward references
StoryWithChoices.update_forward_refs()