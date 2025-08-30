"""Stories management endpoints."""

import logging
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.story import (
    StoryCreate,
    StoryResponse,
    StoryWithChoices,
    StoryWithProgress,
    StoryGenerationRequest,
    StoryGenerationResponse,
    ChoiceSelectionRequest,
    StoryRecommendation,
    ContentSafetyCheck
)
from app.schemas.story_session import (
    StorySessionCreate,
    StorySessionResponse,
    StorySessionUpdate,
    ReadingProgress
)
from app.services.child_service import ChildService
from app.services.story_service import StoryService
from app.services.story_session_service import StorySessionService
from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[StoryWithProgress])
async def get_stories(
    child_id: Optional[int] = Query(None, description="Filter stories for specific child"),
    theme: Optional[str] = Query(None, description="Filter by story theme"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    language: Optional[str] = Query(None, description="Filter by language"),
    limit: int = Query(20, description="Maximum number of stories to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get stories, optionally filtered for a specific child."""
    try:
        story_service = StoryService(db)
        child_service = ChildService(db)
        
        if child_id:
            # Verify child belongs to current user
            if not child_service.check_child_access(child_id, current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this child profile"
                )
            
            child = child_service.get_child_by_id(child_id)
            if not child:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Child not found"
                )
            
            stories = story_service.get_stories_for_child(child, limit, theme)
        else:
            # Get general stories (could be enhanced with user preferences)
            stories = story_service.get_published_stories(
                language=language,
                theme=theme,
                difficulty=difficulty,
                limit=limit
            )
        
        logger.info(f"Retrieved {len(stories)} stories for user: {current_user.id}")
        return stories
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve stories"
        )


@router.get("/recommendations/{child_id}", response_model=StoryRecommendation)
async def get_story_recommendations(
    child_id: int,
    limit: int = Query(10, description="Number of recommendations"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get personalized story recommendations for a child."""
    try:
        story_service = StoryService(db)
        child_service = ChildService(db)
        
        # Check access
        if not child_service.check_child_access(child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        child = child_service.get_child_by_id(child_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Check cache first
        cache_key = f"recommendations:{child_id}:{limit}"
        cached_recommendations = await redis_client.get(cache_key)
        if cached_recommendations:
            logger.info(f"Returning cached recommendations for child: {child_id}")
            return cached_recommendations
        
        # Get recommendations
        recommended_stories = story_service.get_recommended_stories(child, limit)
        
        recommendation_data = StoryRecommendation(
            stories=recommended_stories,
            recommendation_reason=f"Based on {child.name}'s interests and reading level",
            personalized=True
        )
        
        # Cache recommendations for 30 minutes
        await redis_client.set(cache_key, recommendation_data.dict(), expire=1800)
        
        logger.info(f"Generated {len(recommended_stories)} recommendations for child: {child_id}")
        return recommendation_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations for child {child_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get story recommendations"
        )


@router.post("/generate")
async def generate_story(
    generation_request: StoryGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Generate a new personalized story for a child."""
    try:
        story_service = StoryService(db)
        child_service = ChildService(db)
        
        # Check access
        if not child_service.check_child_access(generation_request.child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        child = child_service.get_child_by_id(generation_request.child_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Rate limiting disabled for development
        
        # Generate the story
        result = story_service.generate_personalized_story(
            child=child,
            theme=generation_request.theme,
            chapter_number=generation_request.chapter_number,
            story_session=None,
            custom_user_input=None
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Story generation failed")
            )
        
        logger.info(f"Generated story for child: {generation_request.child_id}, theme: {generation_request.theme}")
        
        # Transform response to match frontend expectations
        # Split story content into paragraphs
        story_content = result.get("story_content", "")
        
        # Clean up any remaining JSON artifacts or meta text
        import re
        story_content = re.sub(r'```json.*?```', '', story_content, flags=re.DOTALL)
        story_content = re.sub(r'Here is Chapter \d+ of the story:', '', story_content)
        story_content = re.sub(r'Please let me know.*?continue.*?\.', '', story_content, flags=re.IGNORECASE)
        story_content = story_content.strip()
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in story_content.split('\n\n') if p.strip()]
        
        # Filter out any paragraphs that look like JSON
        clean_paragraphs = []
        for p in paragraphs:
            if not any(char in p for char in ['{', '}', '"story_content"', '```']):
                clean_paragraphs.append(p)
        
        if not clean_paragraphs:
            clean_paragraphs = [story_content] if story_content else ["Once upon a time..."]
        
        # Save story to database so choices can be persisted
        from app.models.story import Story, Choice, StoryBranch
        story = Story(
            title=generation_request.title or f"{generation_request.theme.capitalize()} Adventure",
            content=story_content,
            language=child.language_preference or "english",
            difficulty_level=child.reading_level or "beginner", 
            themes=[generation_request.theme],
            target_age_min=max(3, child.age - 2),
            target_age_max=min(18, child.age + 2),
            estimated_reading_time=result.get("estimated_reading_time", 5),
            total_chapters=3,
            has_choices=len(result.get("choices", [])) > 0,
            generated_by_ai=True,
            content_safety_score=result.get("safety_score", 1.0),
            is_published=True
        )
        
        db.add(story)
        db.flush()  # Get the story ID
        
        # Create Choice records for the generated choices
        choices_with_ids = []
        for i, choice_data in enumerate(result.get("choices", [])):
            choice = Choice(
                story_id=story.id,
                chapter_number=generation_request.chapter_number,
                position_in_chapter=i + 1,
                question="What would you like to do?",
                choices_data=[choice_data],  # Store the choice data
                default_choice_index=0,
                is_critical_choice=False
            )
            db.add(choice)
            db.flush()
            
            # Add database ID to choice data for frontend
            choice_with_id = {
                "id": str(choice.id),  # Convert to string for frontend
                "text": choice_data.get("text", "Continue"),
                "description": choice_data.get("description", ""),
                "impact": choice_data.get("description", "See what happens next")
            }
            choices_with_ids.append(choice_with_id)
            
            # Create StoryBranch for this choice option
            # For now, create a simple continuation branch
            story_branch = StoryBranch(
                story_id=story.id,
                choice_id=choice.id,
                choice_option_index=0,  # Single option per choice for now
                branch_name=f"Branch from choice {choice.id}",
                content=f"You chose: {choice_data.get('text', 'Continue')}. The story continues...",
                leads_to_chapter=generation_request.chapter_number + 1,
                is_ending=generation_request.chapter_number >= 3  # End after 3 chapters
            )
            db.add(story_branch)
        
        db.commit()
        
        # Create response matching frontend Story interface
        response = {
            "id": str(story.id),  # Use real database ID
            "title": story.title,
            "content": clean_paragraphs,  # Array of clean paragraphs
            "language": story.language,
            "readingLevel": story.difficulty_level,
            "theme": generation_request.theme,
            "choices": choices_with_ids,  # Choices with database IDs
            "isCompleted": False,
            "currentChapter": generation_request.chapter_number,
            "totalChapters": story.total_chapters,
            "createdAt": story.created_at.isoformat(),
            "success": result.get("success", True),
            "safety_score": result.get("safety_score", 1.0),
            "educational_elements": result.get("educational_elements", []),
            "estimated_reading_time": story.estimated_reading_time
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating story: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate story"
        )


@router.post("/create-with-ai", response_model=StoryResponse)
async def create_story_with_ai(
    story_create: StoryCreate,
    child_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create and save a new AI-generated story."""
    try:
        story_service = StoryService(db)
        child_service = ChildService(db)
        
        # Check access
        if not child_service.check_child_access(child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        child = child_service.get_child_by_id(child_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Create the story
        story = story_service.create_story_with_ai(
            child=child,
            theme=story_create.theme,
            title=story_create.title or f"A {story_create.theme.title()} Adventure",
            total_chapters=story_create.total_chapters
        )
        
        if not story:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create story"
            )
        
        logger.info(f"Created AI story: {story.id} for child: {child_id}")
        return story
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating AI story: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create story"
        )


@router.get("/{story_id}", response_model=StoryWithChoices)
async def get_story(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get a specific story with its choices."""
    try:
        story_service = StoryService(db)
        
        story = story_service.get_story_by_id(story_id)
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        if not story.is_published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Story is not published"
            )
        
        logger.info(f"Retrieved story: {story_id} for user: {current_user.id}")
        return story
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting story {story_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve story"
        )


@router.post("/{story_id}/check-safety", response_model=ContentSafetyCheck)
async def check_story_safety(
    story_id: int,
    child_age: int = Query(..., description="Age of the child reading the story"),
    language: str = Query("english", description="Language of the content"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Check the safety of a story for a specific child age."""
    try:
        story_service = StoryService(db)
        
        story = story_service.get_story_by_id(story_id)
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        # Run safety check
        safety_result = story_service.check_story_safety(
            story.content,
            child_age,
            language
        )
        
        logger.info(f"Safety check completed for story: {story_id}, age: {child_age}")
        return ContentSafetyCheck(**safety_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking story safety: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check story safety"
        )


# Story Session endpoints
@router.post("/{story_id}/sessions", response_model=StorySessionResponse)
async def start_story_session(
    story_id: int,
    session_create: StorySessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Start a new story reading session."""
    try:
        story_service = StoryService(db)
        child_service = ChildService(db)
        session_service = StorySessionService(db)
        
        # Check child access
        if not child_service.check_child_access(session_create.child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        # Check story exists
        story = story_service.get_story_by_id(story_id)
        if not story or not story.is_published:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found or not published"
            )
        
        # Create or resume session
        session = session_service.start_story_session(
            child_id=session_create.child_id,
            story_id=story_id
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start story session"
            )
        
        logger.info(f"Started story session: {session.id} for child: {session_create.child_id}")
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting story session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start story session"
        )


@router.put("/sessions/{session_id}/progress")
async def update_reading_progress(
    session_id: int,
    progress: ReadingProgress,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update reading progress for a story session."""
    try:
        session_service = StorySessionService(db)
        child_service = ChildService(db)
        
        # Get session and verify access
        session = session_service.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story session not found"
            )
        
        if not child_service.check_child_access(session.child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this story session"
            )
        
        # Update progress
        updated_session = session_service.update_reading_progress(session_id, progress)
        
        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update reading progress"
            )
        
        return {"message": "Reading progress updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reading progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reading progress"
        )


@router.post("/sessions/{session_id}/choices")
async def make_story_choice(
    session_id: int,
    choice_request: ChoiceSelectionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Make a choice in a story session."""
    try:
        session_service = StorySessionService(db)
        child_service = ChildService(db)
        story_service = StoryService(db)
        
        # Get session and verify access
        session = session_service.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story session not found"
            )
        
        if not child_service.check_child_access(session.child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this story session"
            )
        
        # Process the choice
        # Check if this is a custom user input choice
        custom_user_input = None
        if choice_request.choice_id == "custom-choice" and choice_request.custom_text:
            custom_user_input = choice_request.custom_text.strip()
        
        # Record the choice made (for context in next chapter generation)
        session = session_service.get_session_by_id(session_id)
        if session:
            # Convert string choice_id to integer if possible, otherwise use special handling
            try:
                choice_id_int = int(choice_request.choice_id)
                session.add_choice(choice_id_int, choice_request.option_index or 0)
            except ValueError:
                # Handle special choice IDs like "continue" or "custom-choice"
                if not session.choices_made:
                    session.choices_made = []
                
                choice_record = {
                    "choice_id": choice_request.choice_id,  # Keep as string for special choices
                    "option_index": choice_request.option_index or 0,
                    "timestamp": choice_request.timestamp or datetime.utcnow().isoformat(),
                }
                
                # For custom choices, record the user's text as the chosen option
                if choice_request.choice_id == "custom-choice" and choice_request.custom_text:
                    choice_record["chosen_option"] = choice_request.custom_text.strip()
                    choice_record["question"] = "Custom user input"
                
                session.choices_made.append(choice_record)
            
            # Commit the choice to database
            session_service.db.commit()
        
        # Use dynamic chapter generation, passing custom input if provided
        result = session_service.advance_to_next_chapter(session_id, custom_user_input)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to process choice")
            )
        
        logger.info(f"Choice made in session: {session_id}, choice: {choice_request.choice_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making story choice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to make story choice"
        )