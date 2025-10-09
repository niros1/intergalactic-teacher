"""LangGraph workflow for story generation with personalization and safety checks."""

from typing import Any, Dict, List, Optional, TypedDict
import logging
import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
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


# Pydantic models for structured output
class Choice(BaseModel):
    """Model for story choices."""
    text: str = Field(..., description="The choice text that the child will see")
    description: str = Field("", description="Optional description providing more context about the choice")


class StoryContent(BaseModel):
    """Model for complete story generation output."""
    story_content: str = Field(..., description="The main story content for this chapter, written in direct storytelling voice")
    choices: List[Choice] = Field(..., description="List of 2-4 choices for the child to make to continue the story")
    educational_elements: List[str] = Field(
        default=["Reading comprehension", "Decision making"], 
        description="Educational elements present in this chapter"
    )
    vocabulary_words: List[str] = Field(
        default=[], 
        description="List of challenging or educational vocabulary words used in this chapter"
    )


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


# JSON formatting helper functions removed - no longer needed with structured output


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
        "---------",
        "OUTPUT FORMAT MUST BE VALID JSON !!!",
        "Follow this JSON output example:",
        "{",
        "\"story_content\": \"ONLY the pure story text that continues seamlessly from previous chapters\",",
        "\"choices\": [",
        "  {\"text\": \"Choice 1 text\", \"description\": \"Optional description\"},",
        "  {\"text\": \"Choice 2 text\", \"description\": \"Optional description\"},",
        "  {\"text\": \"Choice 3 text\", \"description\": \"Optional description\"}",
        "]",
        "}"
    ])
    
    # Ensure the prompt isn't too long for the LLM
    full_prompt = "\n".join(prompt_parts)
    
    # Log prompt length for debugging
    word_count = len(full_prompt.split())
    if word_count > 1500:
        logger.warning(f"Prompt is quite long ({word_count} words) - consider shortening for better performance")
    
    return full_prompt


def create_story_prompt_for_structured_output(state: StoryGenerationState) -> str:
    """Create a personalized story generation prompt optimized for structured output."""
    prefs = state["child_preferences"]
    theme = state["story_theme"]
    chapter_num = state["chapter_number"]
    logger.info(f"Generating structured prompt for chapter {chapter_num} with {len(state['previous_chapters'])} previous chapters for context")
    
    # Base prompt structure - optimized for structured output
    prompt_parts = [
        f"Create Chapter {chapter_num} of a {theme} story for a {prefs.get('age', 9)}-year-old child.",
        f"Write as if you are telling the story directly to the child in person.",
        "",
        "CHILD PROFILE:",
        f"- Age: {prefs.get('age')} years old",
        f"- Language: {prefs.get('language', 'english')}",
        f"- Reading Level: {prefs.get('reading_level', 'beginner')}",
        f"- Interests: {', '.join(prefs.get('interests', []))}",
        f"- Vocabulary Level: {prefs.get('vocabulary_level', 50)}/100",
        "",
        "STORY REQUIREMENTS:",
        "- Write 3-5 engaging paragraphs for story_content",
        "- Start immediately with the story (no meta-commentary)",
        "- Use vocabulary appropriate for the reading level with 2-3 challenging words",
        "- Include diverse characters and positive values",
        "- Provide 2-4 meaningful choices that advance the story",
    ]
    
    # Add enhanced context from previous chapters
    if state["previous_chapters"]:
        prompt_parts.extend([
            "",
            "STORY CONTEXT - What happened before:",
        ])
        
        # Add chapter summaries for context
        for i, chapter in enumerate(state["previous_chapters"]):
            summary = create_story_summary(chapter, i+1)
            prompt_parts.append(f"Chapter {i+1}: {summary}")
        
        prompt_parts.extend([
            "",
            "CONTINUITY REQUIREMENTS:",
            "- Reference and build upon characters, relationships, and events from previous chapters",
            "- Maintain established tone, world-building, and character personalities",
            "- Create natural story progression that acknowledges what came before",
            f"- This is Chapter {chapter_num}, continue the established narrative"
        ])
    
    # Add choice context
    if state["previous_choices"]:
        prompt_parts.extend([
            "",
            "PREVIOUS STORY DECISIONS:",
        ])
        
        for choice in state["previous_choices"]:
            prompt_parts.append(f"• {choice['question']}: '{choice['chosen_option']}'")
        
        prompt_parts.append("→ Honor these decisions and their consequences in the story.")
    
    # Add custom user input context
    if state.get("custom_user_input"):
        prompt_parts.extend([
            "",
            "CUSTOM USER INPUT:",
            f"The child has expressed: \"{state['custom_user_input']}\"",
            "Incorporate this naturally into the story progression and respond meaningfully.",
        ])
    
    prompt_parts.extend([
        "", 
        "IMPORTANT: Ensure story_content flows naturally from previous chapters.",
        "Reference characters, events, and settings established earlier.",
        "The response will be automatically structured with the required fields.",
    ])
    
    return "\n".join(prompt_parts)


def generate_story_content(state: StoryGenerationState) -> Dict[str, Any]:
    """Generate story content using Ollama with structured output."""
    try:
        # Initialize the base LLM
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=settings.OLLAMA_TEMPERATURE,
            num_predict=settings.OLLAMA_MAX_TOKENS,
        )
        
        # Create structured LLM that auto-guides to JSON matching StoryContent schema
        structured_llm = llm.with_structured_output(StoryContent)
        
        # Create the personalized prompt
        prompt_text = create_story_prompt_for_structured_output(state)
        
        # Create a structured prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert children's story writer creating educational, engaging, and safe content. You must respond with the exact fields specified in the schema."),
            ("user", "{prompt}")
        ])
        
        # Create the chain: prompt -> structured_llm
        chain = prompt_template | structured_llm
        
        # Invoke the chain to get structured output
        logger.info("Generating story content with structured output...")
        result: StoryContent = chain.invoke({"prompt": prompt_text})
        
        logger.info(f"Generated structured story content successfully")
        logger.info(f"Story content length: {len(result.story_content)} characters")
        logger.info(f"Number of choices: {len(result.choices)}")
        
        # Convert to dictionary format expected by the workflow
        return {
            "story_content": result.story_content,
            "choices": [choice.dict() for choice in result.choices],
            "educational_elements": result.educational_elements,
            "vocabulary_words": result.vocabulary_words,
        }
        
    except Exception as e:
        logger.error(f"Error generating story content with structured output: {e}")
        # Log the full error for debugging
        logger.error(f"Full error details: {str(e)}")
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


def format_story_content(content: str, language: str = "english") -> str:
    """Format story content with paragraph breaks and contextual emojis for better readability."""

    # Define emoji mappings based on keywords for different languages
    emoji_map_en = {
        # Characters & Actions
        "happy": "😊", "smiled": "😊", "laughed": "😄", "giggled": "😆",
        "excited": "🤗", "surprised": "😮", "amazed": "😲", "wondered": "🤔",
        "brave": "💪", "strong": "💪", "hero": "🦸", "friend": "👫",

        # Nature & Places
        "forest": "🌳", "tree": "🌲", "flowers": "🌸", "garden": "🏡",
        "mountain": "⛰️", "ocean": "🌊", "river": "🏞️", "beach": "🏖️",
        "sun": "☀️", "moon": "🌙", "star": "⭐", "rainbow": "🌈",
        "cloud": "☁️", "rain": "🌧️", "snow": "❄️",

        # Animals
        "dog": "🐕", "cat": "🐱", "bird": "🐦", "butterfly": "🦋",
        "rabbit": "🐰", "lion": "🦁", "elephant": "🐘", "dragon": "🐉",
        "unicorn": "🦄", "fish": "🐟",

        # Objects & Activities
        "book": "📚", "treasure": "💎", "magic": "✨", "crown": "👑",
        "castle": "🏰", "house": "🏠", "school": "🏫", "rocket": "🚀",
        "car": "🚗", "bicycle": "🚲", "balloon": "🎈", "gift": "🎁",

        # Emotions & Events
        "celebration": "🎉", "party": "🎊", "success": "🎯", "victory": "🏆",
        "music": "🎵", "dance": "💃", "game": "🎮", "adventure": "🗺️",
    }

    emoji_map_he = {
        # תווים ופעולות
        "שמח": "😊", "חייך": "😊", "צחק": "😄", "התרגש": "🤗",
        "הופתע": "😮", "אמיץ": "💪", "גיבור": "🦸", "חבר": "👫",

        # טבע ומקומות
        "יער": "🌳", "עץ": "🌲", "פרחים": "🌸", "גן": "🏡",
        "הר": "⛰️", "ים": "🌊", "נהר": "🏞️", "חוף": "🏖️",
        "שמש": "☀️", "ירח": "🌙", "כוכב": "⭐", "קשת": "🌈",

        # חיות
        "כלב": "🐕", "חתול": "🐱", "ציפור": "🐦", "פרפר": "🦋",
        "ארנב": "🐰", "אריה": "🦁", "פיל": "🐘", "דרקון": "🐉",

        # חפצים ופעילויות
        "ספר": "📚", "אוצר": "💎", "קסם": "✨", "כתר": "👑",
        "טירה": "🏰", "בית": "🏠", "בית ספר": "🏫", "חלל": "🚀",
    }

    emoji_map = emoji_map_he if language == "hebrew" else emoji_map_en

    # Split into sentences
    sentences = []
    current_sentence = []
    words = content.split()

    for word in words:
        current_sentence.append(word)
        # Check for sentence endings
        if word.endswith(('.', '!', '?', '。', '！', '？')):
            sentence_text = ' '.join(current_sentence)

            # Add contextual emoji at the end of sentence if keyword found
            sentence_lower = sentence_text.lower()
            for keyword, emoji in emoji_map.items():
                if keyword in sentence_lower and emoji not in sentence_text:
                    sentence_text += f" {emoji}"
                    break  # Only add one emoji per sentence

            sentences.append(sentence_text)
            current_sentence = []

    # Add any remaining words as a sentence
    if current_sentence:
        sentences.append(' '.join(current_sentence))

    # Group sentences into paragraphs (3-4 sentences each)
    paragraphs = []
    paragraph_sentences = []

    for i, sentence in enumerate(sentences):
        paragraph_sentences.append(sentence)

        # Create new paragraph every 3-4 sentences
        if len(paragraph_sentences) >= 3 or i == len(sentences) - 1:
            paragraph_text = ' '.join(paragraph_sentences)
            paragraphs.append(paragraph_text)
            paragraph_sentences = []

    # Join paragraphs with double line breaks for visual separation
    formatted_content = '\n\n'.join(paragraphs)

    return formatted_content


def calculate_reading_metrics(state: StoryGenerationState) -> Dict[str, Any]:
    """Calculate reading time and difficulty metrics, and format the story content."""
    content = state["story_content"]
    child_age = state["child_preferences"].get("age", 9)
    reading_level = state["child_preferences"].get("reading_level", "beginner")
    language = state["child_preferences"].get("language", "english")

    # Format the story content with paragraphs and emojis
    formatted_content = format_story_content(content, language)

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
        "story_content": formatted_content,  # Return formatted content
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