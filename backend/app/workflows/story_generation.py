"""LangGraph workflow for story generation with personalization and safety checks."""

from typing import Any, Dict, List, TypedDict
import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

from app.core.config import settings

logger = logging.getLogger(__name__)


class StoryGenerationState(TypedDict):
    """State for story generation workflow."""
    # Input parameters
    child_preferences: Dict[str, Any]
    story_theme: str
    chapter_number: int
    previous_chapters: List[str]
    previous_choices: List[Dict]
    
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


def create_story_prompt(state: StoryGenerationState) -> str:
    """Create a personalized story generation prompt."""
    prefs = state["child_preferences"]
    theme = state["story_theme"]
    chapter_num = state["chapter_number"]
    
    # Base prompt structure
    prompt_parts = [
        f"You are a creative children's story writer specializing in interactive narratives for children aged {prefs.get('age', 9)}.",
        f"Create Chapter {chapter_num} of an engaging story with the theme: {theme}",
        "",
        "CHILD PROFILE:",
        f"- Age: {prefs.get('age')} years old",
        f"- Language: {prefs.get('language', 'english')}",
        f"- Reading Level: {prefs.get('reading_level', 'beginner')}",
        f"- Interests: {', '.join(prefs.get('interests', []))}",
        f"- Vocabulary Level: {prefs.get('vocabulary_level', 50)}/100",
        "",
        "STORY REQUIREMENTS:",
        "- Write 3-5 paragraphs appropriate for the child's reading level",
        "- Include vocabulary that matches their level with 2-3 slightly challenging words",
        "- Make it educational but fun and engaging",
        "- Include diverse characters and positive values",
        "- Ensure cultural sensitivity",
        "- End with a meaningful choice point for the child",
    ]
    
    # Add context from previous chapters
    if state["previous_chapters"]:
        prompt_parts.extend([
            "",
            "STORY CONTEXT (Previous chapters):",
            *[f"Chapter {i+1}: {chapter[:200]}..." for i, chapter in enumerate(state["previous_chapters"])]
        ])
    
    # Add choice context
    if state["previous_choices"]:
        prompt_parts.extend([
            "",
            "PREVIOUS CHOICES MADE:",
            *[f"- {choice['question']}: {choice['chosen_option']}" for choice in state["previous_choices"]]
        ])
    
    prompt_parts.extend([
        "",
        "OUTPUT FORMAT:",
        "Return a JSON object with:",
        "- story_content: The chapter text",
        "- choices: Array of 2-3 choice options, each with 'text' and 'description'",
        "- educational_elements: Array of learning opportunities in this chapter",
        "- vocabulary_words: Array of challenging words used",
        "",
        "Example choices format:",
        '[{"text": "Help the character", "description": "Show kindness and empathy"}, ...]'
    ])
    
    return "\n".join(prompt_parts)


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
        
        # Try to parse JSON response
        try:
            # Extract JSON from various formats the model might return
            json_content = content
            
            # Check if content has markdown code blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end > start:
                    json_content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end > start:
                    json_content = content[start:end].strip()
            
            # Try to find JSON object in the content
            if "{" in json_content:
                start = json_content.find("{")
                end = json_content.rfind("}") + 1
                if end > start:
                    json_content = json_content[start:end]
            
            story_data = json.loads(json_content)
            
            # Extract the actual story content and choices
            story_text = story_data.get("story_content", "")
            # Clean up any escape characters and formatting
            story_text = story_text.replace('\\n', '\n').replace('\\"', '"').strip()
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
                # Provide default choices if none are valid
                valid_choices = [
                    {"text": "Continue the adventure", "description": "See what happens next"},
                    {"text": "Make a different choice", "description": "Try a different path"}
                ]
            
            return {
                "story_content": story_text,
                "choices": valid_choices,
                "educational_elements": story_data.get("educational_elements", ["Reading comprehension", "Decision making"]),
                "vocabulary_words": story_data.get("vocabulary_words", []),
            }
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse JSON response: {e}, using fallback")
            # Extract any readable text from the content
            clean_content = content
            
            # Remove common JSON artifacts
            clean_content = clean_content.replace('```json', '').replace('```', '')
            clean_content = clean_content.replace('Here is Chapter 1 of the story:', '')
            clean_content = clean_content.replace('Please let me know if you\'d like me to continue', '')
            
            # Try to extract story_content value if present
            if "story_content" in clean_content:
                import re
                # Try to extract content between quotes after story_content
                match = re.search(r'"story_content"\s*:\s*"([^"]+)"', clean_content, re.DOTALL)
                if match:
                    clean_content = match.group(1)
                    clean_content = clean_content.replace('\\n', '\n').replace('\\"', '"')
            
            # Remove any remaining JSON structure
            clean_content = re.sub(r'[{}\[\]"]', '', clean_content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
            
            # If content is too messy, provide a simple fallback story
            if len(clean_content) < 50 or '{' in clean_content:
                clean_content = "Once upon a time in a magical forest, there lived a curious little rabbit named Rosie. She loved to explore and make new friends. Today was going to be a special adventure!"
            
            return {
                "story_content": clean_content[:1000],  # Reasonable length
                "choices": [
                    {"text": "Continue the adventure", "description": "See what happens next"},
                    {"text": "Make a different choice", "description": "Try a different path"}
                ],
                "educational_elements": ["Reading comprehension", "Decision making"],
                "vocabulary_words": [],
            }
            
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
    """Create the story generation workflow graph."""
    
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
    
    return workflow.compile()


# Create a singleton instance
story_workflow = create_story_generation_workflow()