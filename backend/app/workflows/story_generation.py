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
from app.utils.text_beautifier import beautify_story_text

logger = logging.getLogger(__name__)

# Configure LangSmith tracing if environment variables are set
if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
    logger.info("LangSmith tracing enabled for project: %s", os.getenv("LANGSMITH_PROJECT", "default"))
else:
    logger.info("LangSmith tracing is not enabled")


# Pydantic models for structured output
class Choice(BaseModel):
    """Model for story choices.
    
    IMPORTANT: The 'text' field should contain the actual choice action that will be displayed to the child.
    Example correct format:
        {"text": "Help the rabbit cross the river", "description": "This shows kindness"}
    
    Example WRONG format (DO NOT DO THIS):
        {"text": "A", "description": "Help the rabbit"}  # <- Wrong! Don't use letters
    """
    text: str = Field(
        ..., 
        description="The complete choice action/option that the child will see and click on. This should be a meaningful phrase like 'Help the rabbit' or 'Explore the cave', NOT a letter like 'A' or 'B'."
    )
    description: str = Field(
        "", 
        description="Optional additional context or consequences of this choice. Can be empty."
    )


class StoryContent(BaseModel):
    """Model for complete story generation output."""
    story_content: str = Field(..., description="The main story content for this chapter, written in direct storytelling voice")
    choice_question: str = Field(..., description="A personalized, contextual question that leads into the choices. Should be specific to the story situation (e.g., 'What should Luna do next?' or 'How will the friends continue their adventure?')")
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
    welcome_message: str
    story_content: str
    choice_question: str  # IMPORTANT: Contextual question from LLM
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
    """Create a structured summary of a chapter using LLM for better context preservation."""
    # For very short chapters, return as-is
    if len(chapter_content) <= 200:
        return chapter_content
    
    try:
        # Use LLM to create a meaningful summary
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3,  # Lower temp for consistent summarization
            num_predict=150,  # Concise summary
        )
        
        summary_prompt = f"""Summarize this story chapter in 2-3 sentences. Focus on:
- Main characters and their actions
- Key events and plot developments
- Important details that affect the story progression

Chapter {chapter_num}:
{chapter_content}

Provide a concise summary (2-3 sentences):"""

        response = llm.invoke([HumanMessage(content=summary_prompt)])
        summary = response.content.strip()
        
        logger.info(f"✨ Created LLM summary for chapter {chapter_num}: {summary[:80]}...")
        return summary
        
    except Exception as e:
        logger.error(f"Error creating LLM summary for chapter {chapter_num}: {e}")
        # Fallback to basic truncation
        words = chapter_content.split()
        if len(words) <= 100:
            return chapter_content
        else:
            beginning = ' '.join(words[:60])
            ending = ' '.join(words[-40:])
            return f"{beginning}... {ending}"[:400]


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
        "- Write 8-12 engaging paragraphs to create a substantial chapter",
        "- Aim for approximately 150-200 words total for a satisfying reading experience",
        "- Use vocabulary appropriate for the reading level with 2-3 challenging words",
        "- Include diverse characters and positive values (varied names, backgrounds, personalities)",
        "- Be creative with character names - avoid repeating the same names in different stories",
        "- Vary settings and scenarios within the theme (not every adventure needs to be in a forest!)",
        "- Make it naturally flow as if told by a storyteller",
        "",
        "CHILD-FRIENDLY FORMATTING (CRITICAL):",
        f"- Write in SHORT, SIMPLE sentences (aim for under 15 words per sentence)",
        f"- Break the story into TINY paragraphs (2-3 sentences maximum per paragraph)",
        f"- Use natural pauses between scenes and story beats",
        f"- Add breathing room - separate paragraphs with blank lines in your mind",
        f"- Keep it EASY to read and follow for young readers aged {prefs.get('age', 9)}",
        f"- Each paragraph should be ONE complete thought or action",
        f"- Example good paragraph: 'The hero looked around. Birds were singing. It was a beautiful day.'",
        f"- Example BAD paragraph: Long run-on sentences with multiple ideas crammed together",
        f"- Language: {prefs.get('language', 'english')} - Use clear, natural phrasing in this language",
    ]
    
    # Add enhanced context from previous chapters - OPTIMIZED FOR STORY CONTINUITY
    if state["previous_chapters"]:
        prompt_parts.extend([
            "",
            "📖 STORY CONTEXT - What happened before:",
            "Use this information to maintain perfect story continuity:"
        ])
        
        # Add pre-generated chapter summaries for context
        # Summaries are generated and saved after each chapter is created
        for chapter_summary in state["previous_chapters"]:
            prompt_parts.append(chapter_summary)
        
        logger.info(f"Using {len(state['previous_chapters'])} pre-generated chapter summaries")
        
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
        "IMPORTANT OUTPUT REQUIREMENTS:",
        "- Write ONLY the pure story text (no JSON, no field names, no markup)",
        "- Do NOT include field names like 'story_content:' or JSON structure",
        "- Write as if you are directly telling the story to the child",
        "- The system will automatically structure your output",
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
        "- Write 8-12 engaging paragraphs for story_content to create a substantial chapter",
        "- Aim for approximately 150-200 words total for a satisfying reading experience",
        "- Start immediately with the story (no meta-commentary)",
        "- Use vocabulary appropriate for the reading level with 2-3 challenging words",
        "- Include diverse characters and positive values (varied names, backgrounds, personalities)",
        "- Be creative with character names - avoid repeating the same names in different stories",
        "- Vary settings and scenarios within the theme (not every adventure needs to be in a forest!)",
        "- Create a personalized choice_question that relates to the current story situation",
        "  * Use character names from the story (e.g., 'What should Sarah do next?')",
        "  * Make it specific to the situation (e.g., 'How will they cross the river?')",
        "  * Avoid generic questions like 'What would you like to do?'",
        "- Provide 2-4 meaningful choices that advance the story",
        "",
        "CHOICE FORMAT (VERY IMPORTANT):",
        "- Each choice.text should be a complete, meaningful action phrase",
        "- Example CORRECT: {\"text\": \"Help the friend find their way home\", \"description\": \"\"}",
        "- Example CORRECT: {\"text\": \"Explore the mysterious cave\", \"description\": \"This is brave\"}",
        "- Example WRONG: {\"text\": \"A\", \"description\": \"Help the friend\"} <- DO NOT use letters!",
        "- Example WRONG: {\"text\": \"B\", \"description\": \"Explore the cave\"} <- DO NOT use letters!",
        "- The text field is what the child will SEE and CLICK on, so make it clear and engaging",
        "",
        "- IMPORTANT: Write PLAIN TEXT ONLY. Do NOT use HTML tags like <p>, <br>, <div>, etc.",
        "- Output pure story text without any markup or formatting tags",
        "",
        "CHILD-FRIENDLY FORMATTING (CRITICAL):",
        "- Write in SHORT, SIMPLE sentences (aim for under 15 words per sentence)",
        "- Break the story into TINY paragraphs (2-3 sentences maximum per paragraph)",
        "- Use natural pauses between scenes and story beats",
        "- Add breathing room - separate paragraphs with blank lines in your mind",
        "- Keep it EASY to read and follow for young readers",
        "- Think: 'Would a {}-year-old find this easy to follow?'".format(prefs.get('age', 9)),
        "- Each paragraph should be ONE complete thought or action",
        "- Example good paragraph: 'The hero looked around. Birds were singing. It was a beautiful day.'",
        "- Example BAD paragraph: Long run-on sentences with multiple ideas crammed together",
        "- Language: {} - Use clear, natural phrasing in this language".format(prefs.get('language', 'english')),
    ]
    
    # Add enhanced context from previous chapters
    if state["previous_chapters"]:
        prompt_parts.extend([
            "",
            "STORY CONTEXT - What happened before:",
        ])
        
        # Add pre-generated chapter summaries for context
        # Summaries are generated and saved after each chapter is created
        for chapter_summary in state["previous_chapters"]:
            prompt_parts.append(chapter_summary)
        
        logger.info(f"Using {len(state['previous_chapters'])} pre-generated chapter summaries")
        
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
        "IMPORTANT OUTPUT REQUIREMENTS:",
        "- Write ONLY the pure story text in story_content (no JSON, no field names, no markup)",
        "- The story_content field should contain ONLY the narrative text that the child will read",
        "- Do NOT include field names like 'story_content:' or JSON structure in your output",
        "- Write as if you are directly telling the story to the child",
        "- Ensure the story flows naturally from previous chapters",
        "- Reference characters, events, and settings established earlier",
        "- The system will automatically structure your output into the required format",
    ])

    return "\n".join(prompt_parts)


def generate_welcome_message(state: StoryGenerationState) -> Dict[str, Any]:
    """Generate a personalized welcome message using LLM."""
    try:
        prefs = state["child_preferences"]
        theme = state["story_theme"]
        child_name = prefs.get('name', 'friend')
        child_age = prefs.get('age', 9)
        language = prefs.get('language', 'english')
        interests = prefs.get('interests', [])
        
        logger.info(f"Generating welcome message for {child_name}, theme: {theme}")
        
        # Initialize LLM
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.7,  # More creative for welcomes
            num_predict=150,  # Shorter for welcome messages
        )
        
        # Create personalized welcome prompt
        interests_text = f" who loves {', '.join(interests)}" if interests else ""
        
        if language == 'hebrew':
            welcome_prompt = f"""Create a warm, enthusiastic welcome message in Hebrew for a {child_age}-year-old child named {child_name}{interests_text}.

The message should:
- Greet {child_name} personally in Hebrew
- Express excitement about starting a {theme} story
- Be age-appropriate and engaging
- Be 1-2 sentences maximum
- Include a relevant emoji
- Match the {theme} theme naturally

Write ONLY the welcome message in Hebrew, nothing else."""
        else:
            welcome_prompt = f"""Create a warm, enthusiastic welcome message for a {child_age}-year-old child named {child_name}{interests_text}.

The message should:
- Greet {child_name} personally 
- Express excitement about starting a {theme} story/adventure
- Be age-appropriate and engaging
- Be 1-2 sentences maximum
- Include a relevant emoji
- Match the {theme} theme naturally (e.g., if it's animals, mention animals; if it's science, mention discoveries)

Write ONLY the welcome message, nothing else."""

        # Generate welcome message
        response = llm.invoke([HumanMessage(content=welcome_prompt)])
        welcome_text = response.content.strip()
        
        logger.info(f"Generated welcome message: {welcome_text[:100]}...")
        
        return {
            "welcome_message": welcome_text,
        }
        
    except Exception as e:
        logger.error(f"Error generating welcome message: {e}")
        # Fallback to simple message
        child_name = state["child_preferences"].get('name', 'friend')
        theme = state["story_theme"]
        language = state["child_preferences"].get('language', 'english')
        
        if language == 'hebrew':
            fallback = f"היי {child_name}! בואו נתחיל הרפתקה מדהימה! 🌟"
        else:  
            fallback = f"Hi {child_name}! Let's start an amazing {theme} adventure! 🌟"
            
        return {
            "welcome_message": fallback,
        }


def generate_story_content(state: StoryGenerationState) -> Dict[str, Any]:
    """Generate story content using Ollama with structured output."""
    try:
        # Initialize the base LLM WITHOUT structured output for better streaming
        # We'll parse the JSON manually to enable token-by-token streaming
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=settings.OLLAMA_TEMPERATURE,
            num_predict=settings.OLLAMA_MAX_TOKENS,
            format="json"  # Ask Ollama to return JSON format
        )
        
        # Create the personalized prompt
        prompt_text = create_story_prompt_for_structured_output(state)
        
        # Create prompt that requests JSON output with clear structure
        # Note: Double braces {{ }} escape the braces so LangChain doesn't treat them as variables
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert children's story writer. You MUST respond with valid JSON in this exact format:

{{
  "story_content": "The pure narrative story text here",
  "choice_question": "A question for the child",
  "choices": [
    {{"text": "Choice 1", "description": "Description 1"}},
    {{"text": "Choice 2", "description": "Description 2"}}
  ],
  "educational_elements": ["element1", "element2"],
  "vocabulary_words": ["word1", "word2"]
}}

CRITICAL RULES:
1. The "story_content" field must contain ONLY the narrative story text that the child will read
2. DO NOT include the choice_question in the story_content field
3. DO NOT include the choices JSON in the story_content field
4. The story_content should END with the story narrative, NOT with the question or choices
5. Put the question in "choice_question" and the choices in the "choices" array SEPARATELY

IMPORTANT: Output ONLY valid JSON, no other text before or after."""),
            ("user", "{prompt}")
        ])

        # Create the chain
        chain = prompt_template | llm

        # Invoke the chain to get JSON response
        logger.info("Generating story content with JSON format...")
        response = chain.invoke({"prompt": prompt_text})

        # Parse the JSON response
        import json
        response_text = response.content if hasattr(response, 'content') else str(response)
        result_json = json.loads(response_text)

        # Extract fields from JSON
        story_content = result_json.get("story_content", "")
        choice_question = result_json.get("choice_question", "")
        choices_data = result_json.get("choices", [])
        educational_elements = result_json.get("educational_elements", [])
        vocabulary_words = result_json.get("vocabulary_words", [])

        logger.info(f"Generated story content successfully")
        logger.info(f"Story content length: {len(story_content)} characters")
        logger.info(f"Number of choices: {len(choices_data)}")

        # Convert to dictionary format expected by the workflow
        return {
            "story_content": story_content,
            "choice_question": choice_question,
            "choices": choices_data,
            "educational_elements": educational_elements,
            "vocabulary_words": vocabulary_words,
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

    # Remove any HTML tags that the LLM might have added
    import re
    content = re.sub(r'<[^>]+>', '', content)

    # Remove common HTML entities
    content = content.replace('&nbsp;', ' ')
    content = content.replace('&amp;', '&')
    content = content.replace('&lt;', '<')
    content = content.replace('&gt;', '>')
    content = content.replace('&quot;', '"')
    content = content.replace('&#39;', "'")

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
        "story_content": formatted_content,  # Return formatted content (emojis added)
        "estimated_reading_time": estimated_reading_time,
        "vocabulary_level": vocabulary_level,
    }


def beautify_content(state: StoryGenerationState) -> Dict[str, Any]:
    """Apply text beautification - add line breaks after each sentence for easier reading."""
    content = state["story_content"]
    language = state["child_preferences"].get("language", "english")
    
    # Apply text beautification - add line breaks after each sentence
    beautified_content = beautify_story_text(content, language)
    logger.info(f"✨ Beautification node: Applied line breaks after sentences - language: {language}")
    
    return {
        "story_content": beautified_content,
    }


def should_regenerate_content(state: StoryGenerationState) -> str:
    """Determine if content should be regenerated."""
    if not state["content_approved"]:
        if state["safety_score"] < 0.3:
            return "regenerate"  # Too unsafe, regenerate completely
        else:
            return "enhance"  # Borderline, try enhancement
    return "finalize"


# Helper function to determine if we should generate welcome message
def should_generate_welcome(state: StoryGenerationState) -> str:
    """Determine if we should generate a welcome message (only for chapter 1)."""
    if state["chapter_number"] == 1:
        return "generate_welcome"
    return "generate_content"


# Create the workflow graph
def create_story_generation_workflow():
    """Create the story generation workflow graph with LangSmith tracing."""
    
    workflow = StateGraph(StoryGenerationState)
    
    # Add nodes
    workflow.add_node("check_chapter", lambda state: state)  # Passthrough node for routing
    workflow.add_node("generate_welcome", generate_welcome_message)
    workflow.add_node("generate_content", generate_story_content)
    workflow.add_node("safety_check", check_content_safety) 
    workflow.add_node("enhance_content", enhance_content_if_needed)
    workflow.add_node("calculate_metrics", calculate_reading_metrics)
    workflow.add_node("beautify_content", beautify_content)  # Dedicated beautification node
    
    # Add edges - conditionally generate welcome message only for chapter 1
    workflow.set_entry_point("check_chapter")
    workflow.add_conditional_edges(
        "check_chapter",
        should_generate_welcome,
        {
            "generate_welcome": "generate_welcome",
            "generate_content": "generate_content",
        }
    )
    workflow.add_edge("generate_welcome", "generate_content")
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
    workflow.add_edge("calculate_metrics", "beautify_content")  # Beautify after metrics
    workflow.add_edge("beautify_content", END)  # End after beautification
    
    # Compile with checkpointer for better tracing
    compiled_workflow = workflow.compile()
    
    # Add metadata for LangSmith tracing
    if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
        compiled_workflow.name = "story_generation_workflow"
        logger.info("Story generation workflow compiled with LangSmith tracing")
    
    return compiled_workflow


# Create a singleton instance
story_workflow = create_story_generation_workflow()