"""Story session service for managing reading sessions."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.child import Child
from app.models.story import Story, Choice, StoryBranch
from app.models.story_session import StorySession
from app.schemas.story_session import ReadingProgress

logger = logging.getLogger(__name__)


class StorySessionService:
    """Service for story session operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_session_by_id(self, session_id: int) -> Optional[StorySession]:
        """Get story session by ID."""
        return self.db.query(StorySession).filter(StorySession.id == session_id).first()
    
    def get_active_sessions_for_child(self, child_id: int) -> List[StorySession]:
        """Get active (incomplete) sessions for a child."""
        return (
            self.db.query(StorySession)
            .filter(
                StorySession.child_id == child_id,
                StorySession.is_completed == False
            )
            .order_by(StorySession.last_accessed.desc())
            .all()
        )
    
    def get_completed_sessions_for_child(self, child_id: int, limit: int = 10) -> List[StorySession]:
        """Get completed sessions for a child."""
        return (
            self.db.query(StorySession)
            .filter(
                StorySession.child_id == child_id,
                StorySession.is_completed == True
            )
            .order_by(StorySession.completed_at.desc())
            .limit(limit)
            .all()
        )
    
    def start_story_session(self, child_id: int, story_id: int) -> Optional[StorySession]:
        """Start a new story session or resume existing one."""
        try:
            # Check if there's already an active session for this story
            existing_session = (
                self.db.query(StorySession)
                .filter(
                    StorySession.child_id == child_id,
                    StorySession.story_id == story_id,
                    StorySession.is_completed == False
                )
                .first()
            )
            
            if existing_session:
                # Resume existing session
                existing_session.last_accessed = datetime.utcnow()
                self.db.commit()
                self.db.refresh(existing_session)
                logger.info(f"Resumed existing session: {existing_session.id}")
                return existing_session
            
            # Create new session
            session = StorySession(
                child_id=child_id,
                story_id=story_id,
                current_chapter=1,
                choices_made=[],
                is_completed=False,
                is_bookmarked=False,
                completion_percentage=0,
                session_duration=0,
                words_read=0,
                audio_playback_used=False,
                audio_playback_duration=0,
                choices_engagement_rate=0,
                reading_speed_wpm=0,
                pause_count=0,
                vocabulary_encountered=[],
                started_at=datetime.utcnow(),
                last_accessed=datetime.utcnow()
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            logger.info(f"Started new story session: {session.id}")
            return session
            
        except Exception as e:
            logger.error(f"Error starting story session: {e}")
            self.db.rollback()
            return None
    
    def update_reading_progress(
        self,
        session_id: int,
        progress: ReadingProgress
    ) -> Optional[StorySession]:
        """Update reading progress for a session."""
        try:
            session = self.get_session_by_id(session_id)
            if not session:
                return None
            
            # Update reading metrics
            session.words_read = progress.words_read
            session.session_duration += progress.reading_time
            
            if progress.audio_playback_time:
                session.audio_playback_used = True
                session.audio_playback_duration += progress.audio_playback_time
            
            if progress.pause_count:
                session.pause_count += progress.pause_count
            
            # Calculate reading speed (words per minute)
            if session.session_duration > 0:
                session.reading_speed_wpm = int(
                    (session.words_read * 60) / session.session_duration
                )
            
            # Update completion percentage based on current position
            if hasattr(progress, 'current_position') and progress.current_position:
                # Simple percentage calculation - can be enhanced
                total_story = session.story
                if total_story and total_story.total_chapters:
                    chapter_progress = (session.current_chapter - 1) / total_story.total_chapters
                    session.completion_percentage = min(100, int(chapter_progress * 100))
            
            session.last_accessed = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(session)
            
            # Update child's reading progress
            self._update_child_progress(session)
            
            return session
            
        except Exception as e:
            logger.error(f"Error updating reading progress: {e}")
            self.db.rollback()
            return None
    
    def make_story_choice(
        self,
        session_id: int,
        choice_id: int,
        option_index: int
    ) -> Dict:
        """Process a story choice and advance the story."""
        try:
            session = self.get_session_by_id(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Get the choice
            choice = self.db.query(Choice).filter(Choice.id == choice_id).first()
            if not choice:
                return {"success": False, "error": "Choice not found"}
            
            # Validate option index
            if option_index >= len(choice.choices_data):
                return {"success": False, "error": "Invalid choice option"}
            
            # Record the choice
            session.add_choice(choice_id, option_index)
            
            # Get the story branch for this choice
            branch = (
                self.db.query(StoryBranch)
                .filter(
                    StoryBranch.choice_id == choice_id,
                    StoryBranch.choice_option_index == option_index
                )
                .first()
            )
            
            if not branch:
                return {"success": False, "error": "Story branch not found"}
            
            # Generate branch content if needed
            if not branch.content:
                from app.services.story_service import StoryService
                story_service = StoryService(self.db)
                branch_content = story_service.generate_branch_content(
                    branch, session.child, session
                )
                if not branch_content:
                    return {"success": False, "error": "Failed to generate story content"}
            
            # Update session progress
            if branch.leads_to_chapter:
                session.current_chapter = branch.leads_to_chapter
            
            if branch.is_ending:
                session.is_completed = True
                session.completion_percentage = 100
                session.completed_at = datetime.utcnow()
            
            # Update choice engagement rate
            session.choices_engagement_rate = session.calculate_engagement_rate()
            
            session.last_accessed = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(session)
            
            # Update child progress if story completed
            if session.is_completed:
                self._update_child_progress(session, story_completed=True)
            
            result = {
                "success": True,
                "branch_content": branch.content,
                "is_ending": branch.is_ending,
                "next_chapter": branch.leads_to_chapter,
                "completion_percentage": session.completion_percentage
            }
            
            logger.info(f"Choice processed for session: {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing story choice: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def bookmark_session(self, session_id: int, bookmarked: bool = True) -> Optional[StorySession]:
        """Bookmark or unbookmark a story session."""
        try:
            session = self.get_session_by_id(session_id)
            if not session:
                return None
            
            session.is_bookmarked = bookmarked
            session.last_accessed = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(session)
            
            return session
            
        except Exception as e:
            logger.error(f"Error bookmarking session: {e}")
            self.db.rollback()
            return None
    
    def complete_session(self, session_id: int) -> Optional[StorySession]:
        """Mark a session as completed."""
        try:
            session = self.get_session_by_id(session_id)
            if not session:
                return None
            
            session.is_completed = True
            session.completion_percentage = 100
            session.completed_at = datetime.utcnow()
            session.last_accessed = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(session)
            
            # Update child progress
            self._update_child_progress(session, story_completed=True)
            
            return session
            
        except Exception as e:
            logger.error(f"Error completing session: {e}")
            self.db.rollback()
            return None
    
    def get_session_analytics(self, session_id: int) -> Optional[Dict]:
        """Get analytics data for a session."""
        try:
            session = self.get_session_by_id(session_id)
            if not session:
                return None
            
            return {
                "session_id": session.id,
                "duration_minutes": session.session_duration // 60,
                "words_read": session.words_read,
                "reading_speed_wpm": session.reading_speed_wpm,
                "choices_made": len(session.choices_made or []),
                "choices_engagement_rate": session.choices_engagement_rate,
                "audio_usage_percentage": (
                    (session.audio_playback_duration / session.session_duration * 100)
                    if session.session_duration > 0 else 0
                ),
                "pause_frequency": (
                    (session.pause_count / session.session_duration * 60)
                    if session.session_duration > 0 else 0
                ),
                "vocabulary_encountered": len(session.vocabulary_encountered or []),
                "completion_percentage": session.completion_percentage,
                "is_completed": session.is_completed,
            }
            
        except Exception as e:
            logger.error(f"Error getting session analytics: {e}")
            return None
    
    def _update_child_progress(
        self,
        session: StorySession,
        story_completed: bool = False
    ) -> None:
        """Update child's overall reading progress."""
        try:
            from app.services.child_service import ChildService
            child_service = ChildService(self.db)
            
            child_service.update_reading_progress(
                child_id=session.child_id,
                reading_time=session.session_duration,
                words_read=session.words_read,
                story_completed=story_completed
            )
            
        except Exception as e:
            logger.error(f"Error updating child progress: {e}")
    
    def get_child_session_history(
        self,
        child_id: int,
        limit: int = 20
    ) -> List[StorySession]:
        """Get session history for a child."""
        return (
            self.db.query(StorySession)
            .filter(StorySession.child_id == child_id)
            .order_by(StorySession.last_accessed.desc())
            .limit(limit)
            .all()
        )