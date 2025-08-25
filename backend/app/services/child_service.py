"""Child service for managing child profiles and operations."""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.child import Child
from app.models.user import User
from app.schemas.child import ChildCreate, ChildUpdate

logger = logging.getLogger(__name__)


class ChildService:
    """Service for child-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_child_by_id(self, child_id: int) -> Optional[Child]:
        """Get child by ID."""
        return self.db.query(Child).filter(Child.id == child_id).first()
    
    def get_children_by_parent(self, parent_id: int) -> List[Child]:
        """Get all children for a parent."""
        return self.db.query(Child).filter(Child.parent_id == parent_id).all()
    
    def create_child(self, parent_id: int, child_data: ChildCreate) -> Child:
        """Create a new child profile."""
        try:
            # Create child record
            child = Child(
                parent_id=parent_id,
                name=child_data.name,
                age=child_data.age,
                language_preference=child_data.language_preference,
                reading_level=child_data.reading_level,
                interests=child_data.interests or [],
                total_stories_completed=0,
                total_reading_time=0,
                current_reading_streak=0,
                longest_reading_streak=0,
                vocabulary_words_learned=0,
                reading_level_score=self._calculate_initial_reading_score(child_data)
            )
            
            self.db.add(child)
            self.db.commit()
            self.db.refresh(child)
            
            logger.info(f"Created child profile: {child.name} (ID: {child.id}) for parent: {parent_id}")
            return child
            
        except Exception as e:
            logger.error(f"Error creating child profile: {e}")
            self.db.rollback()
            raise
    
    def update_child(self, child_id: int, child_update: ChildUpdate) -> Optional[Child]:
        """Update child profile."""
        try:
            child = self.get_child_by_id(child_id)
            if not child:
                return None
            
            # Update fields if provided
            if child_update.name is not None:
                child.name = child_update.name
            
            if child_update.age is not None:
                child.age = child_update.age
            
            if child_update.language_preference is not None:
                child.language_preference = child_update.language_preference
            
            if child_update.reading_level is not None:
                old_level = child.reading_level
                child.reading_level = child_update.reading_level
                
                # Update reading level score if level changed
                if old_level != child_update.reading_level:
                    child.reading_level_score = self._update_reading_level_score(
                        child.reading_level_score,
                        old_level,
                        child_update.reading_level
                    )
            
            if child_update.interests is not None:
                child.interests = child_update.interests
            
            if child_update.avatar_url is not None:
                child.avatar_url = child_update.avatar_url
            
            child.updated_at = datetime.utcnow()
            child.last_active = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(child)
            
            logger.info(f"Updated child profile: {child.name} (ID: {child.id})")
            return child
            
        except Exception as e:
            logger.error(f"Error updating child profile {child_id}: {e}")
            self.db.rollback()
            raise
    
    def delete_child(self, child_id: int) -> bool:
        """Delete a child profile."""
        try:
            child = self.get_child_by_id(child_id)
            if not child:
                return False
            
            self.db.delete(child)
            self.db.commit()
            
            logger.info(f"Deleted child profile: {child.name} (ID: {child.id})")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting child profile {child_id}: {e}")
            self.db.rollback()
            return False
    
    def check_child_access(self, child_id: int, parent_id: int) -> bool:
        """Check if parent has access to child profile."""
        child = self.get_child_by_id(child_id)
        return child is not None and child.parent_id == parent_id
    
    def update_reading_progress(
        self,
        child_id: int,
        reading_time: int,
        words_read: int = 0,
        story_completed: bool = False
    ) -> Optional[Child]:
        """Update child's reading progress."""
        try:
            child = self.get_child_by_id(child_id)
            if not child:
                return None
            
            # Update reading metrics
            child.total_reading_time += reading_time
            
            if story_completed:
                child.total_stories_completed += 1
            
            # Update reading streak
            child.last_active = datetime.utcnow()
            # TODO: Implement proper streak calculation based on daily activity
            
            self.db.commit()
            self.db.refresh(child)
            
            return child
            
        except Exception as e:
            logger.error(f"Error updating reading progress for child {child_id}: {e}")
            self.db.rollback()
            return None
    
    def conduct_reading_assessment(
        self,
        child_id: int,
        assessment_results: dict
    ) -> Optional[Child]:
        """Conduct reading level assessment and update child profile."""
        try:
            child = self.get_child_by_id(child_id)
            if not child:
                return None
            
            # Calculate new reading level based on assessment
            new_reading_level = self._calculate_reading_level_from_assessment(
                assessment_results,
                child.age
            )
            
            # Update reading level if different
            if new_reading_level != child.reading_level:
                old_level = child.reading_level
                child.reading_level = new_reading_level
                child.reading_level_score = self._update_reading_level_score(
                    child.reading_level_score,
                    old_level,
                    new_reading_level
                )
                
                logger.info(f"Reading level updated for {child.name}: {old_level} -> {new_reading_level}")
            
            child.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(child)
            
            return child
            
        except Exception as e:
            logger.error(f"Error conducting reading assessment for child {child_id}: {e}")
            self.db.rollback()
            return None
    
    def get_child_dashboard_data(self, child_id: int) -> Optional[dict]:
        """Get dashboard data for a child."""
        try:
            child = self.get_child_by_id(child_id)
            if not child:
                return None
            
            # Get recent story sessions
            from app.models.story_session import StorySession
            recent_sessions = (
                self.db.query(StorySession)
                .filter(StorySession.child_id == child_id)
                .order_by(StorySession.last_accessed.desc())
                .limit(5)
                .all()
            )
            
            # Calculate this week's reading stats
            from datetime import datetime, timedelta
            week_start = datetime.utcnow() - timedelta(days=7)
            
            weekly_sessions = (
                self.db.query(StorySession)
                .filter(
                    StorySession.child_id == child_id,
                    StorySession.started_at >= week_start
                )
                .all()
            )
            
            stories_this_week = len([s for s in weekly_sessions if s.is_completed])
            reading_time_this_week = sum(s.session_duration for s in weekly_sessions) // 60  # minutes
            
            return {
                "child": child,
                "recent_sessions": [s.session_summary for s in recent_sessions],
                "reading_streak": child.current_reading_streak,
                "stories_this_week": stories_this_week,
                "reading_time_this_week": reading_time_this_week,
                "total_stories": child.total_stories_completed,
                "total_reading_hours": child.total_reading_time // 60,
                "vocabulary_learned": child.vocabulary_words_learned,
                "reading_level_score": child.reading_level_score,
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data for child {child_id}: {e}")
            return None
    
    def _calculate_initial_reading_score(self, child_data: ChildCreate) -> int:
        """Calculate initial reading level score based on child data."""
        base_scores = {
            "beginner": 30,
            "intermediate": 60,
            "advanced": 85
        }
        
        score = base_scores.get(child_data.reading_level, 30)
        
        # Adjust based on age
        age_adjustment = max(0, (child_data.age - 7) * 5)
        score += age_adjustment
        
        # Adjust based on interests (more interests = higher engagement potential)
        interest_bonus = min(10, len(child_data.interests or []) * 2)
        score += interest_bonus
        
        return min(100, score)
    
    def _update_reading_level_score(
        self,
        current_score: int,
        old_level: str,
        new_level: str
    ) -> int:
        """Update reading level score when level changes."""
        level_scores = {
            "beginner": 30,
            "intermediate": 60,
            "advanced": 85
        }
        
        old_base = level_scores.get(old_level, 30)
        new_base = level_scores.get(new_level, 30)
        
        # Adjust current score relative to the change
        score_diff = current_score - old_base
        new_score = new_base + score_diff
        
        return max(0, min(100, new_score))
    
    def _calculate_reading_level_from_assessment(
        self,
        assessment_results: dict,
        child_age: int
    ) -> str:
        """Calculate reading level from assessment results."""
        score = assessment_results.get("score", 0)
        total_questions = assessment_results.get("total_questions", 10)
        
        # Calculate percentage score
        percentage = (score / total_questions) * 100 if total_questions > 0 else 0
        
        # Adjust thresholds based on age
        age_adjustment = (child_age - 7) * 5  # Older children need higher scores
        
        beginner_threshold = 40 + age_adjustment
        intermediate_threshold = 70 + age_adjustment
        
        if percentage < beginner_threshold:
            return "beginner"
        elif percentage < intermediate_threshold:
            return "intermediate"
        else:
            return "advanced"