"""Story session service for managing reading sessions."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.child import Child
from app.models.story import Choice, Story, StoryBranch
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
            
            # Get new choices for the next chapter if available
            new_choices = []
            if branch.leads_to_chapter and not branch.is_ending:
                choices_query = self.db.query(Choice).filter(
                    Choice.story_id == session.story_id,
                    Choice.chapter_number == branch.leads_to_chapter
                ).all()

                for choice in choices_query:
                    if choice.choices_data:
                        for option_index, option_data in enumerate(choice.choices_data):
                            if isinstance(option_data, dict) and 'text' in option_data:
                                new_choices.append({
                                    'id': str(choice.id),
                                    'option_index': option_index,
                                    'text': option_data.get('text', ''),
                                    'impact': option_data.get('impact', 'normal'),
                                    'description': option_data.get('description', ''),
                                    'choice_question': choice.question  # Include the contextual question
                                })
            
            result = {
                "success": True,
                "branch_content": branch.content,
                "is_ending": branch.is_ending,
                "next_chapter": branch.leads_to_chapter,
                "completion_percentage": session.completion_percentage,
                "new_choices": new_choices
            }
            
            logger.info(f"Choice processed for session: {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing story choice: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def advance_to_next_chapter(self, session_id: int, custom_user_input: Optional[str] = None) -> Dict:
        """Advance to the next chapter without making a specific choice."""
        try:
            session = self.get_session_by_id(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Check if there are more chapters available
            if session.current_chapter >= session.story.total_chapters:
                # Story is complete
                session.is_completed = True
                session.completion_percentage = 100
                session.completed_at = datetime.utcnow()
                self.db.commit()
                
                return {
                    "success": True,
                    "branch_content": "You have completed the entire story!",
                    "is_ending": True,
                    "next_chapter": session.current_chapter,
                    "completion_percentage": 100,
                    "new_choices": []
                }
            
            # Advance to the next chapter
            next_chapter = session.current_chapter + 1
            
            # Generate content for the next chapter
            from app.services.story_service import StoryService
            story_service = StoryService(self.db)
            
            generation_result = story_service.generate_personalized_story(
                child=session.child,
                theme=session.story.themes[0] if session.story.themes else "adventure",
                chapter_number=next_chapter,
                story_session=session,
                custom_user_input=custom_user_input
            )
            
            if not generation_result["success"]:
                return {"success": False, "error": "Failed to generate next chapter content"}
            
            # Create the new chapter
            from app.models.story_chapter import StoryChapter
            new_chapter = StoryChapter(
                story_id=session.story_id,
                chapter_number=next_chapter,
                title=f"Chapter {next_chapter}",
                content=generation_result["story_content"],
                is_ending=next_chapter >= session.story.total_chapters,
                is_published=True,
                estimated_reading_time=generation_result.get("estimated_reading_time", 5),
                word_count=len(generation_result["story_content"].split()) if generation_result["story_content"] else 0
            )
            
            self.db.add(new_chapter)
            
            # Create choices for the new chapter if any were generated and it's not the ending
            new_choices = []
            if generation_result.get("choices", []) and not new_chapter.is_ending:
                # Get the choice_question from the LLM generation result
                choice_question = generation_result.get("choice_question")

                # Pass the choice_question to _create_story_choices
                story_service._create_story_choices(
                    session.story_id,
                    next_chapter,
                    generation_result["choices"],
                    choice_question
                )

                # Get the created choices to return to frontend
                choices_query = self.db.query(Choice).filter(
                    Choice.story_id == session.story_id,
                    Choice.chapter_number == next_chapter
                ).all()

                for choice in choices_query:
                    if choice.choices_data:
                        for option_index, option_data in enumerate(choice.choices_data):
                            if isinstance(option_data, dict) and 'text' in option_data:
                                new_choices.append({
                                    'id': str(choice.id),
                                    'option_index': option_index,
                                    'text': option_data.get('text', ''),
                                    'impact': option_data.get('impact', 'normal'),
                                    'description': option_data.get('description', ''),
                                    'choice_question': choice.question  # Include the contextual question
                                })
            
            # Update session
            session.current_chapter = next_chapter
            if new_chapter.is_ending:
                session.is_completed = True
                session.completion_percentage = 100
                session.completed_at = datetime.utcnow()
            else:
                # Update completion percentage based on chapters
                session.completion_percentage = int((next_chapter - 1) / session.story.total_chapters * 100)
            
            session.last_accessed = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(session)
            
            # Update child progress if story completed
            if session.is_completed:
                self._update_child_progress(session, story_completed=True)
            
            result = {
                "success": True,
                "branch_content": generation_result["story_content"],
                "is_ending": new_chapter.is_ending,
                "next_chapter": next_chapter,
                "completion_percentage": session.completion_percentage,
                "new_choices": new_choices
            }
            
            logger.info(f"Advanced to chapter {next_chapter} for session: {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error advancing to next chapter: {e}")
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