"""Story service for managing story operations and AI generation."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.child import Child
from app.models.story import Choice, Story, StoryBranch
from app.models.story_session import StorySession
from app.workflows.story_generation import story_workflow, StoryGenerationState
from app.workflows.content_safety import content_safety_workflow, ContentSafetyState

logger = logging.getLogger(__name__)


class StoryService:
    """Service for story-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_personalized_story(
        self, 
        child: Child, 
        theme: str,
        chapter_number: int = 1,
        story_session: Optional[StorySession] = None
    ) -> Dict:
        """Generate a personalized story for a child using LangGraph workflow."""
        try:
            # Prepare the state for story generation
            previous_chapters = []
            previous_choices = []
            
            if story_session and story_session.story:
                # Get previous chapters
                story_content = story_session.story.content
                if story_content:
                    # Split story into chapters (simple implementation)
                    chapters = story_content.split("\n\n---\n\n")
                    previous_chapters = chapters[:chapter_number-1]
                
                # Get previous choices
                if story_session.choices_made:
                    previous_choices = story_session.choices_made
            
            initial_state = StoryGenerationState(
                child_preferences=child.reading_preferences,
                story_theme=theme,
                chapter_number=chapter_number,
                previous_chapters=previous_chapters,
                previous_choices=previous_choices,
                story_content="",
                choices=[],
                safety_score=0.0,
                content_approved=False,
                content_issues=[],
                estimated_reading_time=0,
                vocabulary_level="",
                educational_elements=[]
            )
            
            # Run the story generation workflow
            result = story_workflow.invoke(initial_state)
            
            return {
                "success": True,
                "story_content": result["story_content"],
                "choices": result["choices"],
                "educational_elements": result.get("educational_elements", []),
                "estimated_reading_time": result.get("estimated_reading_time", 5),
                "safety_score": result.get("safety_score", 1.0),
                "content_approved": result.get("content_approved", True),
                "vocabulary_level": result.get("vocabulary_level", child.reading_level)
            }
            
        except Exception as e:
            logger.error(f"Error generating story: {e}")
            return {
                "success": False,
                "error": str(e),
                "story_content": "",
                "choices": []
            }
    
    def create_story_with_ai(
        self,
        child: Child,
        theme: str,
        title: str,
        total_chapters: int = 3
    ) -> Optional[Story]:
        """Create a new story with AI-generated content."""
        try:
            # Generate the first chapter
            generation_result = self.generate_personalized_story(child, theme, 1)
            
            if not generation_result["success"]:
                logger.error(f"Failed to generate story: {generation_result.get('error')}")
                return None
            
            # Create the story record
            story = Story(
                title=title,
                content=generation_result["story_content"],
                language=child.language_preference,
                difficulty_level=child.reading_level,
                themes=[theme],
                target_age_min=max(7, child.age - 1),
                target_age_max=min(12, child.age + 1),
                estimated_reading_time=generation_result.get("estimated_reading_time", 5),
                total_chapters=total_chapters,
                has_choices=len(generation_result["choices"]) > 0,
                generated_by_ai=True,
                content_safety_score=generation_result.get("safety_score", 1.0),
                is_published=generation_result.get("content_approved", True)
            )
            
            # Save to database
            self.db.add(story)
            self.db.commit()
            self.db.refresh(story)
            
            # Create choices if any
            choices = generation_result.get("choices", [])
            if choices:
                self._create_story_choices(story.id, 1, choices)
            
            return story
            
        except Exception as e:
            logger.error(f"Error creating AI story: {e}")
            self.db.rollback()
            return None
    
    def _create_story_choices(
        self,
        story_id: int,
        chapter_number: int,
        choices_data: List[Dict]
    ) -> None:
        """Create choice records for a story chapter."""
        try:
            # Create the choice point
            choice = Choice(
                story_id=story_id,
                chapter_number=chapter_number,
                position_in_chapter=1,
                question="What should happen next?",
                choices_data=choices_data,
                default_choice_index=0,
                is_critical_choice=True
            )
            
            self.db.add(choice)
            self.db.commit()
            self.db.refresh(choice)
            
            # Create story branches for each choice option
            for i, choice_option in enumerate(choices_data):
                branch = StoryBranch(
                    story_id=story_id,
                    choice_id=choice.id,
                    choice_option_index=i,
                    branch_name=choice_option.get("text", f"Option {i+1}"),
                    content="",  # Will be generated when chosen
                    leads_to_chapter=chapter_number + 1,
                    is_ending=False
                )
                
                self.db.add(branch)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating story choices: {e}")
            self.db.rollback()
    
    def get_story_by_id(self, story_id: int) -> Optional[Story]:
        """Get story by ID."""
        return self.db.query(Story).filter(Story.id == story_id).first()
    
    def get_stories_for_child(
        self,
        child: Child,
        limit: int = 20,
        theme: Optional[str] = None
    ) -> List[Story]:
        """Get stories appropriate for a child."""
        query = self.db.query(Story).filter(
            Story.is_published == True,
            Story.language == child.language_preference,
            Story.target_age_min <= child.age,
            Story.target_age_max >= child.age
        )
        
        if theme:
            query = query.filter(Story.themes.contains([theme]))
        
        # Order by content safety score and creation date
        query = query.order_by(
            Story.content_safety_score.desc(),
            Story.created_at.desc()
        )
        
        return query.limit(limit).all()
    
    def get_published_stories(
        self,
        language: Optional[str] = None,
        theme: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 20
    ) -> List[Story]:
        """Get published stories with optional filters."""
        query = self.db.query(Story).filter(Story.is_published == True)
        
        if language:
            query = query.filter(Story.language == language)
        
        if theme:
            query = query.filter(Story.themes.contains([theme]))
        
        if difficulty:
            query = query.filter(Story.difficulty_level == difficulty)
        
        return query.order_by(
            Story.content_safety_score.desc(),
            Story.created_at.desc()
        ).limit(limit).all()
    
    def get_recommended_stories(self, child: Child, limit: int = 10) -> List[Story]:
        """Get recommended stories based on child's preferences and history."""
        # Get child's interests and reading history
        interests = child.interests or []
        
        # Build query for recommendations
        query = self.db.query(Story).filter(
            Story.is_published == True,
            Story.language == child.language_preference,
            Story.target_age_min <= child.age,
            Story.target_age_max >= child.age,
            Story.difficulty_level == child.reading_level
        )
        
        # Filter by interests if available
        if interests:
            # Simple implementation - can be enhanced with better matching
            for interest in interests:
                query = query.filter(Story.themes.contains([interest]))
        
        # Order by safety score and recent creation
        stories = query.order_by(
            Story.content_safety_score.desc(),
            Story.created_at.desc()
        ).limit(limit * 2).all()  # Get more to allow for filtering
        
        # TODO: Implement more sophisticated recommendation algorithm
        # For now, return the first `limit` stories
        return stories[:limit]
    
    def check_story_safety(self, story_content: str, child_age: int, language: str) -> Dict:
        """Check story safety using the content safety workflow."""
        try:
            initial_state = ContentSafetyState(
                content=story_content,
                child_age=child_age,
                language=language,
                context="story",
                moderation_result={},
                age_appropriateness_score=0.0,
                cultural_sensitivity_score=0.0,
                educational_value_score=0.0,
                safety_issues=[],
                recommendations=[],
                overall_safety_score=0.0,
                is_approved=False,
                needs_review=False
            )
            
            # Run the safety workflow
            result = content_safety_workflow.invoke(initial_state)
            
            return {
                "is_safe": result["is_approved"],
                "safety_score": result["overall_safety_score"],
                "issues": result.get("safety_issues", []),
                "recommendations": result.get("recommendations", []),
                "needs_review": result.get("needs_review", False)
            }
            
        except Exception as e:
            logger.error(f"Error in safety check: {e}")
            return {
                "is_safe": False,
                "safety_score": 0.0,
                "issues": [{"type": "system", "issue": "Safety check failed", "severity": "high"}],
                "recommendations": ["Manual review required"],
                "needs_review": True
            }
    
    def get_story_choices(self, story_id: int, chapter_number: int = 1) -> List[Choice]:
        """Get choices for a story chapter."""
        return self.db.query(Choice).filter(
            Choice.story_id == story_id,
            Choice.chapter_number == chapter_number
        ).all()
    
    def get_story_branch(
        self,
        story_id: int,
        choice_id: int,
        option_index: int
    ) -> Optional[StoryBranch]:
        """Get a specific story branch."""
        return self.db.query(StoryBranch).filter(
            StoryBranch.story_id == story_id,
            StoryBranch.choice_id == choice_id,
            StoryBranch.choice_option_index == option_index
        ).first()
    
    def generate_branch_content(
        self,
        story_branch: StoryBranch,
        child: Child,
        story_session: StorySession
    ) -> Optional[str]:
        """Generate content for a story branch."""
        try:
            # If branch already has content, return it
            if story_branch.content:
                return story_branch.content
            
            # Generate new content for this branch
            choice = self.db.query(Choice).filter(Choice.id == story_branch.choice_id).first()
            if not choice:
                return None
            
            # Get the choice option text
            choice_data = choice.choices_data
            if not choice_data or story_branch.choice_option_index >= len(choice_data):
                return None
            
            chosen_option = choice_data[story_branch.choice_option_index]
            
            # Generate continuation based on the choice
            generation_result = self.generate_personalized_story(
                child=child,
                theme=story_session.story.themes[0] if story_session.story.themes else "adventure",
                chapter_number=story_branch.leads_to_chapter or choice.chapter_number + 1,
                story_session=story_session
            )
            
            if generation_result["success"]:
                # Save the generated content
                story_branch.content = generation_result["story_content"]
                self.db.commit()
                
                return story_branch.content
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating branch content: {e}")
            return None