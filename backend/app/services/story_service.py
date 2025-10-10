"""Story service for managing story operations and AI generation."""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.child import Child
from app.models.story import Choice, Story, StoryBranch
from app.models.story_chapter import StoryChapter
from app.models.story_session import StorySession
from app.workflows.story_generation import story_workflow, StoryGenerationState
from app.workflows.content_safety import content_safety_workflow, ContentSafetyState
from app.utils.sse_formatter import (
    format_content_chunk,
    format_safety_check_event,
    format_metadata_event,
    format_complete_event,
    format_error_event,
    format_node_event,
)

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
        story_session: Optional[StorySession] = None,
        custom_user_input: Optional[str] = None
    ) -> Dict:
        """Generate a personalized story for a child using LangGraph workflow."""
        try:
            # Prepare the state for story generation
            previous_chapters = []
            previous_choices = []
            
            if story_session and story_session.story:
                # Get previous chapters from story_chapters table
                previous_chapter_records = self.db.query(StoryChapter).filter(
                    StoryChapter.story_id == story_session.story_id,
                    StoryChapter.chapter_number < chapter_number
                ).order_by(StoryChapter.chapter_number).all()
                
                # Extract chapter content with better context management
                previous_chapters = []
                for chapter_record in previous_chapter_records:
                    # Clean and prepare chapter content for context
                    content = chapter_record.content.strip()
                    if content:
                        # Ensure content is readable and not too fragmented
                        previous_chapters.append(content)
                
                logger.info(f"✅ Found {len(previous_chapter_records)} previous chapters for story continuity")
                
                # Log context info for debugging
                if previous_chapters:
                    total_context_chars = sum(len(ch) for ch in previous_chapters)
                    logger.info(f"Providing {len(previous_chapters)} previous chapters, {total_context_chars} total chars for story continuity")
                
                # Get ONLY the last choice made (for the previous chapter) for context
                # Don't accumulate all choices from all chapters
                if story_session.choices_made and len(story_session.choices_made) > 0:
                    # Get only the most recent choice for story continuity
                    last_choice_data = story_session.choices_made[-1]
                    choice_id = last_choice_data.get("choice_id")
                    option_index = last_choice_data.get("option_index", 0)
                    
                    # Handle custom user input choices differently
                    if choice_id == "custom-choice" and "chosen_option" in last_choice_data:
                        previous_choices = [{
                            "question": last_choice_data.get("question", "Custom user input"),
                            "chosen_option": last_choice_data["chosen_option"]
                        }]
                    elif choice_id and str(choice_id).isdigit():
                        # Handle database stored choices
                        choice = self.db.query(Choice).filter(Choice.id == int(choice_id)).first()
                        if choice and choice.choices_data and option_index < len(choice.choices_data):
                            chosen_option_text = choice.choices_data[option_index].get("text", "")
                            if chosen_option_text:  # Only add if there's actual text
                                previous_choices = [{
                                    "question": choice.question,
                                    "chosen_option": chosen_option_text
                                }]
                            else:
                                previous_choices = []
                        else:
                            previous_choices = []
                    else:
                        previous_choices = []
                else:
                    previous_choices = []
            
            initial_state = StoryGenerationState(
                child_preferences=child.reading_preferences,
                story_theme=theme,
                chapter_number=chapter_number,
                previous_chapters=previous_chapters,
                previous_choices=previous_choices,
                custom_user_input=custom_user_input,
                story_content="",
                choice_question="",  # Will be filled by generate_story_content
                choices=[],
                safety_score=0.0,
                content_approved=False,
                content_issues=[],
                estimated_reading_time=0,
                vocabulary_level="",
                educational_elements=[]
            )
            
            # Log context information for debugging
            logger.info(f"Story generation for chapter {chapter_number}: {len(previous_chapters)} previous chapters, {len(previous_choices)} previous choices")
            
            # Run the story generation workflow with tracing metadata
            result = story_workflow.invoke(
                initial_state,
                config={
                    "metadata": {
                        "child_id": child.id,
                        "child_name": child.name,
                        "theme": theme,
                        "chapter_number": chapter_number,
                        "has_custom_input": bool(custom_user_input),
                        "previous_chapters_count": len(previous_chapters),
                        "previous_choices_count": len(previous_choices)
                    },
                    "tags": ["story_generation", f"chapter_{chapter_number}", theme]
                }
            )
            
            return {
                "success": True,
                "story_content": result["story_content"],
                "choices": result["choices"],
                "choice_question": result.get("choice_question"),  # Include the contextual question
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

    async def generate_personalized_story_stream(
        self,
        child: Child,
        theme: str,
        chapter_number: int = 1,
        story_session: Optional[StorySession] = None,
        custom_user_input: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a personalized story with streaming support.

        Yields SSE-formatted events as the story is being generated:
        - node_event: Workflow node progress (generate_content, safety_check, etc.)
        - content: Story content chunks as they're generated
        - safety_check: Content safety validation results
        - metadata: Reading time, vocabulary level, etc.
        - complete: Final story with all data
        - error: Any errors that occur

        Args:
            child: Child profile for personalization
            theme: Story theme
            chapter_number: Chapter number being generated
            story_session: Optional existing story session for context
            custom_user_input: Optional custom user input to incorporate

        Yields:
            SSE-formatted event strings
        """
        try:
            # Prepare context from previous chapters and choices
            previous_chapters = []
            previous_choices = []

            if story_session and story_session.story:
                # Get previous chapters from story_chapters table
                previous_chapter_records = self.db.query(StoryChapter).filter(
                    StoryChapter.story_id == story_session.story_id,
                    StoryChapter.chapter_number < chapter_number
                ).order_by(StoryChapter.chapter_number).all()

                previous_chapters = [
                    chapter_record.content.strip()
                    for chapter_record in previous_chapter_records
                    if chapter_record.content.strip()
                ]

                logger.info(f"✅ Streaming: Found {len(previous_chapter_records)} previous chapters for context")

                # Get the most recent choice for context
                if story_session.choices_made and len(story_session.choices_made) > 0:
                    last_choice_data = story_session.choices_made[-1]
                    choice_id = last_choice_data.get("choice_id")
                    option_index = last_choice_data.get("option_index", 0)

                    if choice_id == "custom-choice" and "chosen_option" in last_choice_data:
                        previous_choices = [{
                            "question": last_choice_data.get("question", "Custom user input"),
                            "chosen_option": last_choice_data["chosen_option"]
                        }]
                    elif choice_id and str(choice_id).isdigit():
                        choice = self.db.query(Choice).filter(Choice.id == int(choice_id)).first()
                        if choice and choice.choices_data and option_index < len(choice.choices_data):
                            chosen_option_text = choice.choices_data[option_index].get("text", "")
                            if chosen_option_text:
                                previous_choices = [{
                                    "question": choice.question,
                                    "chosen_option": chosen_option_text
                                }]

            # Prepare initial state
            initial_state = StoryGenerationState(
                child_preferences=child.reading_preferences,
                story_theme=theme,
                chapter_number=chapter_number,
                previous_chapters=previous_chapters,
                previous_choices=previous_choices,
                custom_user_input=custom_user_input,
                story_content="",
                choice_question="",
                choices=[],
                safety_score=0.0,
                content_approved=False,
                content_issues=[],
                estimated_reading_time=0,
                vocabulary_level="",
                educational_elements=[]
            )

            logger.info(f"Starting streaming story generation for chapter {chapter_number}")

            # Track accumulated state for final event
            final_state = {}
            current_content = []

            # Buffer for cleaning streaming tokens
            token_buffer = ""
            inside_json = False
            json_depth = 0

            # Stream events from the workflow
            # NOTE: This requires the workflow to be modified to support streaming
            # The langchain-langgraph-expert should implement .astream_events() on the workflow

            # Yield initial start event
            yield format_node_event("workflow", "started", {
                "chapter_number": chapter_number,
                "theme": theme
            })

            # Use astream_events to get detailed streaming from LangGraph
            # This will emit events for each node and token generation
            try:
                async for event in story_workflow.astream_events(
                    initial_state,
                    config={
                        "metadata": {
                            "child_id": child.id,
                            "child_name": child.name,
                            "theme": theme,
                            "chapter_number": chapter_number,
                            "has_custom_input": bool(custom_user_input),
                            "previous_chapters_count": len(previous_chapters),
                            "previous_choices_count": len(previous_choices)
                        },
                        "tags": ["story_generation", f"chapter_{chapter_number}", theme]
                    },
                    version="v2"  # Use v2 for better event streaming
                ):
                    event_type = event.get("event")
                    event_name = event.get("name", "")
                    event_data = event.get("data", {})

                    logger.debug(f"Stream event: {event_type} - {event_name}")

                    # Handle different event types
                    if event_type == "on_chain_start":
                        # Node started
                        if "generate_content" in event_name:
                            yield format_node_event("generate_content", "started")
                        elif "safety_check" in event_name:
                            yield format_node_event("safety_check", "started")
                        elif "calculate_metrics" in event_name:
                            yield format_node_event("calculate_metrics", "started")

                    elif event_type == "on_chain_end":
                        # Node completed - extract state updates
                        output = event_data.get("output", {})

                        if "generate_content" in event_name:
                            # Content generation completed
                            if "story_content" in output:
                                content = output["story_content"]
                                choice_question = output.get("choice_question", "")

                                # CRITICAL: Clean JSON structure from story content
                                # The LLM might return JSON structure even with .with_structured_output()
                                import re
                                import json

                                cleaned_content = content

                                # Check if the story_content contains JSON structure
                                if '{' in cleaned_content and '"story_content"' in cleaned_content:
                                    logger.warning("⚠️ LLM returned JSON in streaming output - cleaning it up")

                                    try:
                                        # Try to parse as JSON and extract story_content field
                                        json_start = cleaned_content.find('{')
                                        json_end = cleaned_content.rfind('}') + 1

                                        if json_start >= 0 and json_end > json_start:
                                            json_str = cleaned_content[json_start:json_end]
                                            parsed_json = json.loads(json_str)

                                            # Extract fields
                                            if 'story_content' in parsed_json:
                                                cleaned_content = parsed_json['story_content'].strip()
                                                logger.info("✅ Extracted clean story_content from JSON")

                                            # Also extract choice_question if it's in the JSON
                                            if 'choice_question' in parsed_json and parsed_json['choice_question']:
                                                choice_question = parsed_json['choice_question'].strip()
                                                logger.info("✅ Extracted choice_question from JSON")

                                    except json.JSONDecodeError:
                                        logger.warning("Failed to parse JSON - using regex cleanup")
                                        # Regex fallback
                                        cleaned_content = re.sub(r'^\s*\{.*?"story_content"\s*:\s*"', '', cleaned_content, flags=re.DOTALL)
                                        cleaned_content = re.sub(r'"\s*,\s*"choice_question".*?\}\s*$', '', cleaned_content, flags=re.DOTALL)
                                        cleaned_content = cleaned_content.replace('\\n', '\n')
                                        cleaned_content = re.sub(r'^\s*[\{\}"\']\s*', '', cleaned_content)
                                        cleaned_content = re.sub(r'\s*[\{\}"\']\s*$', '', cleaned_content)

                                cleaned_content = cleaned_content.strip()

                                # Store cleaned content
                                current_content.append(cleaned_content)
                                final_state["story_content"] = cleaned_content
                                final_state["choices"] = output.get("choices", [])
                                final_state["choice_question"] = choice_question

                                # Stream story_content AND choice_question naturally together
                                # Split content by paragraphs for streaming
                                paragraphs = cleaned_content.split("\n\n")
                                for para in paragraphs:
                                    if para.strip():
                                        yield format_content_chunk(para.strip())
                                        await asyncio.sleep(0.05)  # Small delay for streaming effect

                                # Stream the choice_question as a natural continuation if it exists
                                if choice_question:
                                    # Add a small pause before the question
                                    await asyncio.sleep(0.1)
                                    yield format_content_chunk("\n\n" + choice_question)

                                # DON'T stream the choices array - that will be sent in the complete event

                            yield format_node_event("generate_content", "completed")

                        elif "safety_check" in event_name:
                            # Safety check completed
                            safety_score = output.get("safety_score", 1.0)
                            content_approved = output.get("content_approved", True)
                            content_issues = output.get("content_issues", [])

                            final_state["safety_score"] = safety_score
                            final_state["content_approved"] = content_approved
                            final_state["content_issues"] = content_issues

                            yield format_safety_check_event(
                                approved=content_approved,
                                score=safety_score,
                                issues=content_issues
                            )
                            yield format_node_event("safety_check", "completed")

                        elif "calculate_metrics" in event_name:
                            # Metrics calculation completed
                            estimated_time = output.get("estimated_reading_time", 5)
                            vocab_level = output.get("vocabulary_level", "")
                            educational_elements = output.get("educational_elements", [])

                            final_state["estimated_reading_time"] = estimated_time
                            final_state["vocabulary_level"] = vocab_level
                            final_state["educational_elements"] = educational_elements

                            yield format_metadata_event(
                                estimated_reading_time=estimated_time,
                                vocabulary_level=vocab_level,
                                educational_elements=educational_elements
                            )
                            yield format_node_event("calculate_metrics", "completed")

                    elif event_type == "on_chat_model_stream":
                        # Token-level streaming from LLM
                        chunk = event_data.get("chunk")
                        if chunk and hasattr(chunk, "content") and chunk.content:
                            token = chunk.content

                            # Stream tokens directly - we'll handle JSON structure on frontend
                            # or wait for complete response
                            yield format_content_chunk(token)

                # Workflow completed - NOW SAVE TO DATABASE
                logger.info("Streaming story generation completed successfully - saving to database")

                # Save story to database (similar to POST /generate endpoint)
                story_content = final_state.get("story_content", "")
                choices = final_state.get("choices", [])
                choice_question = final_state.get("choice_question", "")

                # Create Story record
                story = Story(
                    title=f"{theme.capitalize()} Adventure",
                    language=child.language_preference or "english",
                    difficulty_level=child.reading_level or "beginner",
                    themes=[theme],
                    target_age_min=max(3, child.age - 2),
                    target_age_max=min(18, child.age + 2),
                    estimated_reading_time=final_state.get("estimated_reading_time", 5),
                    total_chapters=3,
                    has_choices=len(choices) > 0,
                    generated_by_ai=True,
                    content_safety_score=final_state.get("safety_score", 1.0),
                    is_published=True
                )

                self.db.add(story)
                self.db.flush()  # Get the story ID

                # Create StoryChapter record for the generated content
                chapter = StoryChapter(
                    story_id=story.id,
                    chapter_number=chapter_number,
                    title=f"Chapter {chapter_number}",
                    content=story_content,
                    is_ending=False,
                    is_published=True,
                    estimated_reading_time=final_state.get("estimated_reading_time", 5),
                    word_count=len(story_content.split()) if story_content else 0
                )
                self.db.add(chapter)
                self.db.flush()

                # Create Choice records with database IDs
                choices_with_ids = []
                if choices and choice_question:
                    for i, choice_data in enumerate(choices):
                        choice = Choice(
                            story_id=story.id,
                            chapter_number=chapter_number,
                            position_in_chapter=i + 1,
                            question=choice_question,
                            choices_data=[choice_data],
                            default_choice_index=0,
                            is_critical_choice=False
                        )
                        self.db.add(choice)
                        self.db.flush()

                        # Add database ID to choice data
                        choice_with_id = {
                            "id": str(choice.id),
                            "text": choice_data.get("text", ""),
                            "description": choice_data.get("description", ""),
                            "impact": choice_data.get("description", ""),
                            "choice_question": choice_question
                        }

                        if choice_with_id["text"]:
                            choices_with_ids.append(choice_with_id)

                        # Create StoryBranch for this choice
                        story_branch = StoryBranch(
                            story_id=story.id,
                            choice_id=choice.id,
                            choice_option_index=0,
                            branch_name=f"Branch from choice {choice.id}",
                            content=f"You chose: {choice_data.get('text', 'Continue')}. The story continues...",
                            leads_to_chapter=chapter_number + 1,
                            is_ending=chapter_number >= 3
                        )
                        self.db.add(story_branch)

                self.db.commit()
                self.db.refresh(story)

                logger.info(f"Story saved to database with ID: {story.id}")

                # Clean up story content for frontend
                import re
                story_content_clean = re.sub(r'```json.*?```', '', story_content, flags=re.DOTALL)
                story_content_clean = re.sub(r'Here is Chapter \d+ of the story:', '', story_content_clean)
                story_content_clean = re.sub(r'Please let me know.*?continue.*?\.', '', story_content_clean, flags=re.IGNORECASE)
                story_content_clean = story_content_clean.strip()

                # Split into paragraphs
                paragraphs = [p.strip() for p in story_content_clean.split('\n\n') if p.strip()]
                clean_paragraphs = [p for p in paragraphs if not any(char in p for char in ['{', '}', '"story_content"', '```'])]

                # Validate story content - DO NOT use hardcoded fallbacks
                if not clean_paragraphs:
                    logger.error(f"Story generation failed - no clean content generated. story_content: {story_content[:200] if story_content else 'None'}")
                    yield format_error_event(
                        error_message="Story generation failed: LLM did not generate valid story content",
                        error_code="EMPTY_CONTENT"
                    )
                    return

                logger.info(f"📨 Sending complete event with story ID: {story.id}, choices: {len(choices_with_ids)}")

                # Build final story response with REAL database ID
                yield format_complete_event({
                    "id": str(story.id),  # Real database ID (integer)
                    "success": True,
                    "title": story.title,
                    "content": clean_paragraphs,  # Array of clean paragraphs
                    "story_content": story_content,  # Keep for backward compatibility
                    "choices": choices_with_ids,  # Choices with real database IDs
                    "choice_question": choice_question,
                    "language": story.language,
                    "readingLevel": story.difficulty_level,
                    "theme": theme,
                    "educational_elements": final_state.get("educational_elements", []),
                    "estimated_reading_time": story.estimated_reading_time,
                    "safety_score": final_state.get("safety_score", 1.0),
                    "content_approved": final_state.get("content_approved", True),
                    "vocabulary_level": final_state.get("vocabulary_level", child.reading_level),
                    "isCompleted": False,
                    "currentChapter": chapter_number,
                    "totalChapters": story.total_chapters,
                    "createdAt": story.created_at.isoformat()
                })

            except Exception as stream_error:
                logger.error(f"Error during workflow streaming: {stream_error}")
                yield format_error_event(
                    error_message=f"Story generation failed: {str(stream_error)}",
                    error_code="WORKFLOW_ERROR"
                )

        except Exception as e:
            logger.error(f"Error in streaming story generation: {e}", exc_info=True)
            yield format_error_event(
                error_message=f"Failed to start story generation: {str(e)}",
                error_code="INITIALIZATION_ERROR"
            )

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
            generation_result = self.generate_personalized_story(child, theme, 1, None, None)
            
            if not generation_result["success"]:
                logger.error(f"Failed to generate story: {generation_result.get('error')}")
                return None
            
            # Create the story record (content now stored in chapters table)
            story = Story(
                title=title,
                # content field removed - now using story_chapters table
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
            
            # Create the first chapter record
            chapter = StoryChapter(
                story_id=story.id,
                chapter_number=1,
                title=f"Chapter 1",
                content=generation_result["story_content"],
                is_ending=False,
                is_published=True,
                estimated_reading_time=generation_result.get("estimated_reading_time", 5),
                word_count=len(generation_result["story_content"].split()) if generation_result["story_content"] else 0
            )
            
            self.db.add(chapter)
            self.db.commit()
            self.db.refresh(chapter)
            
            # Create choices if any
            choices = generation_result.get("choices", [])
            if choices:
                choice_question = generation_result.get("choice_question")
                self._create_story_choices(story.id, 1, choices, choice_question)
            
            return story
            
        except Exception as e:
            logger.error(f"Error creating AI story: {e}")
            self.db.rollback()
            return None
    
    def _create_story_choices(
        self,
        story_id: int,
        chapter_number: int,
        choices_data: List[Dict],
        choice_question: Optional[str] = None
    ) -> None:
        """Create choice records for a story chapter."""
        try:
            # IMPORTANT: The LLM MUST generate a contextual choice question
            # We do not use hardcoded fallback questions
            if not choice_question:
                logger.error(f"Missing choice_question for story {story_id}, chapter {chapter_number}")
                raise ValueError("Choice question is required - LLM must generate a contextual question")

            # Create the choice point
            choice = Choice(
                story_id=story_id,
                chapter_number=chapter_number,
                position_in_chapter=1,
                question=choice_question,
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
    ) -> List[Dict]:
        """Get stories appropriate for a child with their reading progress."""
        # Get stories appropriate for the child
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
        
        stories = query.limit(limit).all()
        
        # Enhance stories with session progress
        enhanced_stories = []
        for story in stories:
            # Get the most recent session for this child and story
            session = self.db.query(StorySession).filter(
                StorySession.child_id == child.id,
                StorySession.story_id == story.id
            ).order_by(StorySession.last_accessed.desc()).first()
            
            # Get the content for ALL chapters from chapters table
            current_chapter = session.current_chapter if session else 1
            
            # Get all existing chapters for this story (for display in chat interface)
            # This allows users to see the full story context when they refresh
            all_chapters = self.db.query(StoryChapter).filter(
                StoryChapter.story_id == story.id
            ).order_by(StoryChapter.chapter_number).all()
            
            # Build content array with all chapters from story_chapters table
            all_content = []
            if all_chapters:
                # Use chapters from database - this is now the primary source for all chapters
                for chapter in all_chapters:
                    all_content.append(chapter.content)
            else:
                # No chapters found in story_chapters table
                all_content = ["Chapter content not available"]
            
            
            # Get choices for current chapter if they exist
            choices_data = []
            if story.has_choices and story.choices:
                # Get choices for the current chapter
                for choice in story.choices:
                    if choice.chapter_number == current_chapter:
                        # Add individual choice options if they exist
                        if choice.choices_data and isinstance(choice.choices_data, list):
                            # choices_data is a JSON array of choice options
                            for idx, option in enumerate(choice.choices_data):
                                if isinstance(option, dict) and 'text' in option:
                                    choices_data.append({
                                        'id': f"{choice.id}_{idx}",
                                        'text': option.get('text', ''),
                                        'impact': option.get('impact', 'normal'),
                                        'nextChapter': current_chapter + 1 if current_chapter < story.total_chapters else None
                                    })
                                elif isinstance(option, str):
                                    # If option is just a string, use it as text
                                    choices_data.append({
                                        'id': f"{choice.id}_{idx}",
                                        'text': option,
                                        'impact': 'normal',
                                        'nextChapter': current_chapter + 1 if current_chapter < story.total_chapters else None
                                    })
                        elif not choice.choices_data:
                            # If no choices_data array, use the question as single choice
                            choices_data.append({
                                'id': str(choice.id),
                                'text': choice.question,
                                'impact': 'normal',
                                'nextChapter': current_chapter + 1 if current_chapter < story.total_chapters else None
                            })
            
            # Convert to dict and add progress information
            story_dict = {
                'id': story.id,
                'title': story.title,
                'description': story.description,
                'content': all_content,  # Now returns ALL chapters as array
                'language': story.language,
                'difficulty_level': story.difficulty_level,
                'themes': story.themes,
                'target_age_min': story.target_age_min,
                'target_age_max': story.target_age_max,
                'estimated_reading_time': story.estimated_reading_time,
                'total_chapters': story.total_chapters,
                'has_choices': story.has_choices,
                'generated_by_ai': story.generated_by_ai,
                'content_safety_score': story.content_safety_score,
                'is_published': story.is_published,
                'created_at': story.created_at,
                'choices': choices_data,  # Now includes actual choices
                'current_chapter': session.current_chapter if session else 1,
                'is_completed': session.is_completed if session else False,
                'completion_percentage': session.completion_percentage if session else 0,
            }
            
            enhanced_stories.append(story_dict)
        
        return enhanced_stories
    
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
                story_session=story_session,
                custom_user_input=None
            )
            
            if generation_result["success"]:
                # Save the generated content in the branch
                story_branch.content = generation_result["story_content"]
                
                # Also create a chapter record if this leads to a new chapter
                target_chapter = story_branch.leads_to_chapter or choice.chapter_number + 1
                existing_chapter = self.db.query(StoryChapter).filter(
                    StoryChapter.story_id == story_session.story_id,
                    StoryChapter.chapter_number == target_chapter
                ).first()
                
                if not existing_chapter:
                    # Create new chapter record
                    new_chapter = StoryChapter(
                        story_id=story_session.story_id,
                        chapter_number=target_chapter,
                        title=f"Chapter {target_chapter}",
                        content=generation_result["story_content"],
                        created_from_choice_id=story_branch.choice_id,
                        created_from_branch_id=story_branch.id,
                        is_ending=story_branch.is_ending,
                        is_published=True,
                        estimated_reading_time=generation_result.get("estimated_reading_time", 5),
                        word_count=len(generation_result["story_content"].split()) if generation_result["story_content"] else 0
                    )
                    
                    self.db.add(new_chapter)
                    
                    # Create choices for the new chapter if any were generated
                    new_choices = generation_result.get("choices", [])
                    if new_choices and not story_branch.is_ending:
                        choice_question = generation_result.get("choice_question")
                        self._create_story_choices(story_session.story_id, target_chapter, new_choices, choice_question)
                
                self.db.commit()
                
                return story_branch.content
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating branch content: {e}")
            return None