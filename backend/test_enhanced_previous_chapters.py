#!/usr/bin/env python3
"""
Test script to verify the enhanced previous_chapters context handling.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.workflows.story_generation import create_story_prompt, create_story_summary, extract_story_elements, StoryGenerationState

def test_story_summary():
    """Test the story summary function."""
    sample_chapter = """
    Rohan was a brave 9-year-old boy who lived in a small village near the Whispering Woods. 
    One sunny morning, he decided to explore the mysterious forest that had always fascinated him. 
    As he ventured deeper into the woods, he met Luna, a wise talking owl with silver feathers who became his guide. 
    Luna warned him about the ancient magic that protected the forest and told him that only those with pure hearts could see the forest's true wonders. 
    Together, they discovered a hidden clearing where magical flowers glowed with their own light. 
    Rohan felt amazed by the beautiful sight and promised Luna he would protect the forest.
    """
    
    summary = create_story_summary(sample_chapter, 1)
    print("=== STORY SUMMARY TEST ===")
    print(f"Original length: {len(sample_chapter)} characters")
    print(f"Summary length: {len(summary)} characters")
    print(f"Summary: {summary}")
    print()
    
    return summary

def test_story_elements_extraction():
    """Test story elements extraction."""
    sample_chapter = """
    In the Enchanted Forest, young Rohan met Luna the owl and Pip the fairy. 
    They discovered that an evil Shadow Creature had been stealing magical crystals from the Crystal Cave. 
    Rohan decided to help his new friends by embarking on a quest to the Mountain of Whispers. 
    Along the way, they learned about the ancient magic that protected their world.
    """
    
    elements = extract_story_elements(sample_chapter)
    print("=== STORY ELEMENTS EXTRACTION TEST ===")
    print(f"Characters: {elements['characters']}")
    print(f"Locations: {elements['locations']}")
    print(f"Key Events: {elements['key_events']}")
    print()
    
    return elements

def test_enhanced_prompt():
    """Test the enhanced prompt generation."""
    # Sample previous chapters
    previous_chapters = [
        """Rohan was a brave 9-year-old boy who lived in a small village near the Whispering Woods. 
        One sunny morning, he decided to explore the mysterious forest that had always fascinated him. 
        As he ventured deeper into the woods, he met Luna, a wise talking owl with silver feathers who became his guide. 
        Luna warned him about the ancient magic that protected the forest and told him that only those with pure hearts could see the forest's true wonders. 
        Together, they discovered a hidden clearing where magical flowers glowed with their own light.""",
        
        """In the enchanted clearing, Rohan and Luna encountered Pip, a mischievous fairy who lived in the glowing flowers. 
        Pip explained that the forest was in danger - a shadow creature had been stealing the light from the magical flowers, causing parts of the forest to wither. 
        The fairy asked Rohan to help save the forest by finding three special crystals hidden throughout the woods. 
        Each crystal held the power of different elements: earth, water, and air. 
        Rohan accepted the quest, knowing that his new friends were counting on him."""
    ]
    
    # Sample previous choices
    previous_choices = [
        {"question": "What should Rohan do when he meets Luna?", "chosen_option": "Listen carefully to Luna's wisdom"},
        {"question": "How should Rohan respond to Pip's request for help?", "chosen_option": "Eagerly accept the quest to save the forest"}
    ]
    
    # Child preferences
    child_preferences = {
        "age": 9,
        "language": "english",
        "reading_level": "intermediate",
        "interests": ["adventure", "magic", "animals"],
        "vocabulary_level": 65
    }
    
    # Create state
    state = StoryGenerationState(
        child_preferences=child_preferences,
        story_theme="magical adventure",
        chapter_number=3,
        previous_chapters=previous_chapters,
        previous_choices=previous_choices,
        custom_user_input=None,
        story_content="",
        choices=[],
        safety_score=0.0,
        content_approved=False,
        content_issues=[],
        estimated_reading_time=0,
        vocabulary_level="",
        educational_elements=[]
    )
    
    # Generate the enhanced prompt
    prompt = create_story_prompt(state)
    
    print("=== ENHANCED PROMPT TEST ===")
    print(prompt)
    print("\n" + "="*80 + "\n")
    
    # Analyze improvements
    print("=== PROMPT ANALYSIS ===")
    
    # Check for emojis and better structure
    if "📖 STORY CONTEXT" in prompt:
        print("✓ Enhanced story context section with emojis")
    
    if "🎭 KEY CHARACTERS:" in prompt:
        print("✓ Characters extraction and highlighting")
    
    if "🗺️ STORY LOCATIONS:" in prompt:
        print("✓ Location extraction and highlighting")
    
    if "✨ CONTINUITY REQUIREMENTS:" in prompt:
        print("✓ Explicit continuity requirements")
    
    if "🎯 PREVIOUS STORY DECISIONS:" in prompt:
        print("✓ Enhanced previous choices formatting")
    
    # Check prompt length
    word_count = len(prompt.split())
    print(f"Prompt length: {word_count} words")
    
    if word_count < 800:
        print("✓ Prompt length is optimized")
    elif word_count < 1200:
        print("⚠️ Prompt length is reasonable but could be shorter")
    else:
        print("❌ Prompt might be too long")
    
    # Check for continuity emphasis
    continuity_keywords = ["continue", "build upon", "reference", "maintain", "natural continuation"]
    continuity_count = sum(1 for keyword in continuity_keywords if keyword.lower() in prompt.lower())
    print(f"Continuity emphasis: {continuity_count} continuity keywords found")
    
    if continuity_count >= 3:
        print("✓ Strong emphasis on story continuity")
    else:
        print("⚠️ Could use more emphasis on continuity")
    
    return prompt

def run_all_tests():
    """Run all tests."""
    print("🧪 TESTING ENHANCED PREVIOUS_CHAPTERS FUNCTIONALITY")
    print("="*60)
    
    # Test individual components
    test_story_summary()
    test_story_elements_extraction()
    
    # Test the full enhanced prompt
    test_enhanced_prompt()
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    run_all_tests()