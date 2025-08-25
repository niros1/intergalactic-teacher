"""Analytics schemas for parent dashboard and reporting."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class ReadingMetrics(BaseModel):
    """Basic reading metrics."""
    total_reading_time: int  # in minutes
    stories_completed: int
    average_session_duration: int  # in minutes
    words_read: int
    reading_speed_wpm: int


class EngagementMetrics(BaseModel):
    """Child engagement metrics."""
    choice_interaction_rate: int  # percentage
    audio_usage_rate: int  # percentage
    session_completion_rate: int  # percentage
    return_visit_rate: int  # percentage
    average_attention_span: int  # in minutes
    reading_streak_current: int  # days
    reading_streak_longest: int  # days


class LearningProgress(BaseModel):
    """Learning progression metrics."""
    reading_level: str
    reading_level_score: int  # 0-100
    vocabulary_words_learned: int
    comprehension_average: float  # 0-100
    reading_level_progression: str  # "improving", "stable", "needs_attention"
    skill_areas_strong: List[str]
    skill_areas_improvement: List[str]


class WeeklyTrend(BaseModel):
    """Weekly trend data."""
    week_start: datetime
    reading_time: int
    stories_completed: int
    engagement_score: int


class ChildSummary(BaseModel):
    """Child summary for parent dashboard."""
    child_id: int
    name: str
    age: int
    reading_level: str
    stories_completed_this_week: int
    reading_time_this_week: int  # minutes
    current_streak: int
    last_active: Optional[datetime]


class ChildAnalytics(BaseModel):
    """Comprehensive child analytics."""
    child_id: int
    child_name: str
    period_days: int
    reading_metrics: ReadingMetrics
    engagement_metrics: EngagementMetrics
    learning_progress: LearningProgress
    weekly_trends: List[WeeklyTrend]
    favorite_themes: List[str]
    reading_schedule_insights: Dict[str, int]  # hour -> session_count


class ReadingProgressReport(BaseModel):
    """Reading progress report over time."""
    child_id: int
    child_name: str
    period: str
    start_date: datetime
    end_date: datetime
    initial_reading_level: str
    current_reading_level: str
    reading_level_improvement: float
    total_reading_time: int  # minutes
    stories_completed: int
    vocabulary_growth: int
    comprehension_trends: List[Dict[str, float]]  # date -> score
    reading_speed_trends: List[Dict[str, int]]  # date -> wpm
    recommendations: List[str]


class LearningOutcomes(BaseModel):
    """Learning outcomes and educational impact."""
    child_id: int
    child_name: str
    assessment_period: str
    vocabulary_acquisition: Dict[str, int]  # level -> count
    comprehension_improvement: float
    reading_fluency_improvement: float
    critical_thinking_development: int  # 1-10 scale
    creativity_indicators: List[str]
    educational_milestones: List[Dict[str, str]]
    areas_of_strength: List[str]
    growth_opportunities: List[str]


class ParentDashboard(BaseModel):
    """Complete parent dashboard data."""
    parent_name: str
    children_summary: List[ChildSummary]
    total_family_reading_time: int  # minutes this week
    total_stories_completed: int  # this week
    most_active_child: Optional[str]
    family_reading_streak: int  # days
    upcoming_milestones: List[Dict[str, str]]
    content_safety_alerts: List[Dict[str, str]]
    recommendations: List[str]
    recent_achievements: List[Dict[str, str]]


class SessionAnalytics(BaseModel):
    """Individual session analytics."""
    session_id: int
    child_id: int
    story_title: str
    date: datetime
    duration_minutes: int
    words_read: int
    choices_made: int
    completion_percentage: int
    engagement_score: int
    learning_elements: List[str]


class ThemePopularity(BaseModel):
    """Story theme popularity analytics."""
    theme: str
    story_count: int
    completion_rate: float
    average_engagement: float
    age_group_preference: Dict[str, float]  # age_range -> preference_score


class ContentAnalytics(BaseModel):
    """Content performance analytics."""
    total_stories: int
    average_safety_score: float
    popular_themes: List[ThemePopularity]
    content_effectiveness: Dict[str, float]
    user_feedback_summary: Dict[str, int]


class SystemInsights(BaseModel):
    """System-wide insights for platform improvement."""
    active_users: int
    daily_active_users: int
    average_session_duration: int
    story_generation_success_rate: float
    content_safety_flags: int
    user_satisfaction_score: float
    feature_usage_stats: Dict[str, int]