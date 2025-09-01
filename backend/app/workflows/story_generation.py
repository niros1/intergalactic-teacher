"""LangGraph workflow for story generation with personalization and safety checks."""

from typing import Any, Dict, List, Optional, TypedDict
import json
import logging
import re
import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
# Removed unused LangSmith imports - tracing is handled automatically

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure LangSmith tracing if environment variables are set
if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
    logger.info("LangSmith tracing enabled for project: %s", os.getenv("LANGSMITH_PROJECT", "default"))
else:
    logger.info("LangSmith tracing is not enabled")


class StoryGenerationState(TypedDict):
    """State for story generation workflow."""
    # Input parameters
    child_preferences: Dict[str, Any]
    story_theme: str
    chapter_number: int
    previous_chapters: List[str]
    previous_choices: List[Dict]
    custom_user_input: Optional[str]  # New field for custom user messages
    
    # Generated content
    story_content: str
    choices: List[Dict[str, Any]]
    
    # Safety and quality checks
    safety_score: float
    content_approved: bool
    content_issues: List[str]
    
    # Metadata
    estimated_reading_time: int
    vocabulary_level: str
    educational_elements: List[str]


def create_story_summary(chapter_content: str, chapter_num: int = 0) -> str:
    """Create a structured summary of a chapter focusing on key story elements."""
    # Extract key information (simplified approach - could be enhanced with LLM summarization)
    words = chapter_content.split()
    
    # Take first and last portions to capture beginning and end events
    if len(words) <= 100:
        summary = chapter_content
    else:
        # Take first 60 words and last 40 words for beginning/end context
        beginning = ' '.join(words[:60])
        ending = ' '.join(words[-40:])
        summary = f"{beginning}... {ending}"
    
    return summary[:400]  # Limit to 400 chars for consistency


def generate_simple_fallback_choices(child_age: int = 9, language: str = 'english') -> list:
    """Generate simple fallback choices if LLM doesn't provide any."""
    if child_age <= 8:
        fallback_choices = [
            {"text": "Ask 'What happens next?'", "description": "Continue the magical story"},
            {"text": "Make a new discovery", "description": "Find something wonderful in the story"},
            {"text": "Be helpful and kind", "description": "Show kindness to the characters"}
        ]
    else:
        fallback_choices = [
            {"text": "Continue the adventure", "description": "See where the story leads next"},
            {"text": "Make a thoughtful decision", "description": "Think carefully about the best choice"},
            {"text": "Learn something new", "description": "Discover something interesting in the story"}
        ]
    
    # Translate to Hebrew if needed
    if language == 'hebrew':
        fallback_choices = translate_choices_to_hebrew(fallback_choices)
    
    return fallback_choices


def translate_choices_to_hebrew(choices: list) -> list:
    """Simple Hebrew translation for choices (in production, use proper translation service)."""
    translation_map = {
        "Go left": "לך שמאלה",
        "Go right": "לך ימינה", 
        "Look around first": "תסתכל מסביב קודם",
        "Enter through the door": "היכנס דרך הדלת",
        "Knock first": "תדפוק קודם",
        "Look for another way": "תחפש דרך אחרת",
        "Talk to them": "תדבר איתם",
        "Wave hello": "תנופף שלום",
        "Walk away quietly": "תלך בשקט",
        "Offer to help": "תציע לעזור",
        "Ask what happened": "תשאל מה קרה",
        "Find others to assist": "תמצא אחרים לעזור",
        "Pick it up": "תרים את זה",
        "Examine it closely": "תבדוק את זה מקרוב",
        "Leave it alone": "תשאיר את זה במקום",
        "Continue the adventure": "תמשיך את ההרפתקה",
        "Make a different choice": "תעשה בחירה אחרת",
        "What happens next?": "מה יקרה אחר כך?",
        "Make a new friend": "תכיר חבר חדש",
        "Be curious and explore": "תהיה סקרן ותחקור",
        "Ask 'What happens next?'": "שאל 'מה קורה אחר כך?'",
        "Make a new discovery": "גלה משהו חדש",
        "Be helpful and kind": "תהיה מועיל וחביב",
        "Make a thoughtful decision": "קבל החלטה מחושבת",
        "Learn something new": "למד משהו חדש"
    }
    
    translated_choices = []
    for choice in choices:
        hebrew_text = translation_map.get(choice["text"], choice["text"])
        translated_choices.append({
            "text": hebrew_text,
            "description": choice["description"]  # Keep English description for now
        })
    
    return translated_choices




def create_story_prompt(state: StoryGenerationState) -> str:
    """Create a personalized story generation prompt with enhanced previous chapters context."""
    prefs = state["child_preferences"]
    theme = state["story_theme"]
    chapter_num = state["chapter_number"]
    logger.info(f"Generating chapter {chapter_num} with {len(state['previous_chapters'])} previous chapters for context")
    
    # Base prompt structure
    prompt_parts = [
        f"You are a storyteller narrating directly to a child aged {prefs.get('age', 9)}. Write as if you are telling the story in person.",
        f"Continue the {theme} story. Write Chapter {chapter_num} naturally and engagingly, building upon the established story.",
        "",
        "CHILD PROFILE:",
        f"- Age: {prefs.get('age')} years old",
        f"- Language: {prefs.get('language', 'english')}",
        f"- Reading Level: {prefs.get('reading_level', 'beginner')}",
        f"- Interests: {', '.join(prefs.get('interests', []))}",
        f"- Vocabulary Level: {prefs.get('vocabulary_level', 50)}/100",
        "",
        "WRITING STYLE:",
        "- Write in direct storytelling voice (no meta-commentary like 'Here is Chapter X' or 'story_content:')",
        "- Start immediately with the story content",
        "- Write 3-5 engaging paragraphs",
        "- Use vocabulary appropriate for the reading level with 2-3 challenging words",
        "- Include diverse characters and positive values",
        "- Make it naturally flow as if told by a storyteller",
    ]
    
    # Add enhanced context from previous chapters - OPTIMIZED FOR STORY CONTINUITY
    if state["previous_chapters"]:
        prompt_parts.extend([
            "",
            "📖 STORY CONTEXT - What happened before:",
            "Use this information to maintain perfect story continuity:"
        ])
        
        # Add chapter summaries for context
        chapter_summaries = []
        for i, chapter in enumerate(state["previous_chapters"]):
            # Create focused summary
            summary = create_story_summary(chapter, i+1)
            chapter_summaries.append(f"Chapter {i+1}: {summary}")
        
        # Add chapter summaries
        prompt_parts.extend(chapter_summaries)
        
        prompt_parts.extend([
            "",
            "✨ CONTINUITY REQUIREMENTS:",
            "- Reference and build upon characters, relationships, and events from previous chapters",
            "- Maintain the established tone, world-building, and character personalities",
            "- Create natural story progression that acknowledges what came before",
            "- Use character names and reference previous events when relevant",
            f"- This is Chapter {chapter_num}, so the story should feel like a natural continuation"
        ])
    
    # Add choice context with enhanced formatting
    if state["previous_choices"]:
        prompt_parts.extend([
            "",
            "🎯 PREVIOUS STORY DECISIONS:",
            "The child made these choices that shaped the story:"
        ])
        
        for choice in state["previous_choices"]:
            prompt_parts.append(f"• {choice['question']}: '{choice['chosen_option']}'")
        
        prompt_parts.append("→ Continue the story honoring these decisions and their consequences.")
    
    # Add custom user input context
    if state.get("custom_user_input"):
        prompt_parts.extend([
            "",
            "CUSTOM USER INPUT:",
            f"The child has expressed: \"{state['custom_user_input']}\"",
            "Please incorporate this message naturally into the story progression and respond to it meaningfully.",
            "The story should acknowledge and build upon what the child has said or requested."
        ])
    
    prompt_parts.extend([
        "", 
        "⚠️ CRITICAL: The story_content must feel like a natural continuation of the previous chapters.",
        "Reference characters, events, and settings established earlier. Make the reader feel",
        "the story is building coherently toward something meaningful.",
        "",
        "OUTPUT FORMAT MUST BE JSON!!!",
        "JSON output example:",
        "{",
        "\"story_content\": \"ONLY the pure story text that continues seamlessly from previous chapters\",",
        "\"choices\": [\"Array of 2-3 SPECIFIC and CONTEXTUAL choice options based on the story content\"],",
        "\"educational_elements\": [\"Array of learning opportunities in this chapter\"],",
        "\"vocabulary_words\": [\"Array of challenging words used\"]",
        "}"
    ])
    
    # Ensure the prompt isn't too long for the LLM
    full_prompt = "\n".join(prompt_parts)
    
    # Log prompt length for debugging
    word_count = len(full_prompt.split())
    if word_count > 1500:
        logger.warning(f"Prompt is quite long ({word_count} words) - consider shortening for better performance")
    
    return full_prompt


def generate_story_content(state: StoryGenerationState) -> Dict[str, Any]:
    """Generate story content using Ollama."""
    try:
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=settings.OLLAMA_TEMPERATURE,
            num_predict=settings.OLLAMA_MAX_TOKENS,
        )
        
        # Create the prompt
        prompt = create_story_prompt(state)
        
        # Generate content
        messages = [
            SystemMessage(content="You are an expert children's story writer creating educational, engaging, and safe content."),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        content = response.content.strip()
        logger.info(f"LLM raw response: {content}")
        
        # Try to parse JSON response - DEBUG MODE: No fallbacks, raise errors
        try:
            # Extract JSON from various formats the model might return
            json_content = content
            
            # Check if content has markdown code blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end > start:
                    json_content = content[start:end].strip()
                    logger.info(f"Extracted from ```json blocks: {json_content}")
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end > start:
                    json_content = content[start:end].strip()
                    logger.info(f"Extracted from ``` blocks: {json_content}")
            
            # Try to find JSON object in the content
            if "{" in json_content:
                start = json_content.find("{")
                end = json_content.rfind("}") + 1
                if end > start:
                    json_content = json_content[start:end]
                    logger.info(f"Extracted JSON object: {json_content}")
            
            logger.info(f"Final JSON content to parse: {json_content}")
            story_data = json.loads(json_content)
            
            # Extract the actual story content and choices
            story_text = story_data.get("story_content", "")
            # Clean up any escape characters, formatting, and prefixes
            story_text = story_text.replace('\\n', '\n').replace('\\"', '"').strip()
            
            # Remove prefixes even from successful JSON parsing
            story_text = re.sub(r'Here is Chapter \d+ of.*?:', '', story_text)
            story_text = re.sub(r'Chapter \d+:', '', story_text)
            story_text = re.sub(r'story_content:\s*`', '', story_text)
            story_text = re.sub(r'^story_content:', '', story_text)
            story_text = story_text.replace('Here is the story:', '')
            story_text = story_text.replace('Here\'s the story:', '')
            story_text = story_text.strip()
            choices = story_data.get("choices", [])
            
            # Ensure choices is a proper list
            if not isinstance(choices, list):
                choices = []
            
            # Validate choice structure
            valid_choices = []
            for choice in choices:
                if isinstance(choice, dict) and "text" in choice:
                    valid_choices.append({
                        "text": choice.get("text", ""),
                        "description": choice.get("description", "")
                    })
            
            if not valid_choices:
                # Use simple fallback choices if LLM doesn't provide any
                child_age = state["child_preferences"].get("age", 9)
                language = state["child_preferences"].get("language", "english")
                valid_choices = generate_simple_fallback_choices(child_age, language)
            
            return {
                "story_content": story_text,
                "choices": valid_choices,
                "educational_elements": story_data.get("educational_elements", ["Reading comprehension", "Decision making"]),
                "vocabulary_words": story_data.get("vocabulary_words", []),
            }
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"JSON parsing failed! Raw content: {content}")
            logger.error(f"Attempted to parse: {json_content}")
            logger.error(f"JSON error: {str(e)}")
            # DEBUG MODE: Raise the error instead of using fallbacks
            raise ValueError(f"LLM returned invalid JSON. Raw response: {content[:500]}... Error: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error generating story content: {e}")
        raise


def check_content_safety(state: StoryGenerationState) -> Dict[str, Any]:
    """Check content safety using simple keyword-based checks (Ollama mode)."""
    try:
        # Since we're using Ollama instead of OpenAI, 
        # implement a simple keyword-based safety check
        safety_score = 1.0  # Start with perfect score
        content_issues = []
        
        # Additional custom checks for children's content
        content_lower = state["story_content"].lower()
        
        # Check for inappropriate themes
        inappropriate_themes = ["violence", "scary", "horror", "death", "war"]
        for theme in inappropriate_themes:
            if theme in content_lower:
                content_issues.append(f"Contains {theme} theme")
                safety_score = min(safety_score, 0.7)
        
        # Check for age appropriateness
        child_age = state["child_preferences"].get("age", 9)
        if child_age < 8 and any(word in content_lower for word in ["afraid", "worried", "scared"]):
            content_issues.append("May be too intense for younger children")
            safety_score = min(safety_score, 0.8)
        
        content_approved = safety_score >= settings.CONTENT_SAFETY_THRESHOLD
        
        return {
            "safety_score": safety_score,
            "content_approved": content_approved,
            "content_issues": content_issues,
        }
        
    except Exception as e:
        logger.error(f"Error in content safety check: {e}")
        # Default to safe but flag for manual review
        return {
            "safety_score": 0.5,
            "content_approved": False,
            "content_issues": ["Safety check failed - manual review required"],
        }


def enhance_content_if_needed(state: StoryGenerationState) -> Dict[str, Any]:
    """Enhance content if safety score is borderline."""
    if not state["content_approved"] and state["safety_score"] > 0.3:
        try:
            llm = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.3,  # Lower temperature for safety enhancement
            )
            
            enhancement_prompt = f"""
            Please review and enhance this children's story content to make it more appropriate and safe:
            
            Original content: {state["story_content"]}
            
            Issues identified: {', '.join(state["content_issues"])}
            Child age: {state["child_preferences"].get("age")} years
            
            Please:
            1. Remove or soften any inappropriate content
            2. Ensure age-appropriate language and themes
            3. Maintain the educational and engaging aspects
            4. Keep the same story structure and choice points
            
            Return only the enhanced story content.
            """
            
            messages = [
                SystemMessage(content="You are a content safety specialist for children's educational materials."),
                HumanMessage(content=enhancement_prompt)
            ]
            
            response = llm.invoke(messages)
            enhanced_content = response.content.strip()
            
            return {"story_content": enhanced_content}
            
        except Exception as e:
            logger.error(f"Error enhancing content: {e}")
            return {}
    
    return {}


def calculate_reading_metrics(state: StoryGenerationState) -> Dict[str, Any]:
    """Calculate reading time and difficulty metrics."""
    content = state["story_content"]
    child_age = state["child_preferences"].get("age", 9)
    reading_level = state["child_preferences"].get("reading_level", "beginner")
    
    # Estimate reading time based on word count and reading level
    word_count = len(content.split())
    
    # Words per minute by age and reading level
    wpm_map = {
        "beginner": {7: 80, 8: 90, 9: 100, 10: 110, 11: 120, 12: 130},
        "intermediate": {7: 100, 8: 120, 9: 140, 10: 160, 11: 180, 12: 200},
        "advanced": {7: 120, 8: 150, 9: 180, 10: 210, 11: 240, 12: 270},
    }
    
    wpm = wpm_map.get(reading_level, {}).get(child_age, 120)
    estimated_reading_time = max(1, round(word_count / wpm))
    
    # Determine vocabulary level based on content
    vocabulary_level = reading_level
    
    return {
        "estimated_reading_time": estimated_reading_time,
        "vocabulary_level": vocabulary_level,
    }


def should_regenerate_content(state: StoryGenerationState) -> str:
    """Determine if content should be regenerated."""
    if not state["content_approved"]:
        if state["safety_score"] < 0.3:
            return "regenerate"  # Too unsafe, regenerate completely
        else:
            return "enhance"  # Borderline, try enhancement
    return "finalize"


# Create the workflow graph
def create_story_generation_workflow():
    """Create the story generation workflow graph with LangSmith tracing."""
    
    workflow = StateGraph(StoryGenerationState)
    
    # Add nodes
    workflow.add_node("generate_content", generate_story_content)
    workflow.add_node("safety_check", check_content_safety) 
    workflow.add_node("enhance_content", enhance_content_if_needed)
    workflow.add_node("calculate_metrics", calculate_reading_metrics)
    
    # Add edges
    workflow.set_entry_point("generate_content")
    workflow.add_edge("generate_content", "safety_check")
    
    # Conditional routing based on safety check
    workflow.add_conditional_edges(
        "safety_check",
        should_regenerate_content,
        {
            "regenerate": "generate_content",  # Loop back to regenerate
            "enhance": "enhance_content",
            "finalize": "calculate_metrics",
        }
    )
    
    workflow.add_edge("enhance_content", "safety_check")  # Re-check after enhancement
    workflow.add_edge("calculate_metrics", END)
    
    # Compile with checkpointer for better tracing
    compiled_workflow = workflow.compile()
    
    # Add metadata for LangSmith tracing
    if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
        compiled_workflow.name = "story_generation_workflow"
        logger.info("Story generation workflow compiled with LangSmith tracing")
    
    return compiled_workflow


# Create a singleton instance
story_workflow = create_story_generation_workflow()