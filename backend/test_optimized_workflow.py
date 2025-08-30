#!/usr/bin/env python3
"""Test script for the optimized story generation workflow."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.story_generation import (
    StoryGenerationState, 
    create_chapter_summary,
    build_story_context,
    create_enhanced_story_prompt,
    story_workflow
)
from app.core.config import settings

def test_chapter_summary():
    """Test the intelligent chapter summarization."""
    print("=== Testing Chapter Summarization ===")
    
    sample_chapter = """
    Rohan walked through the enchanted forest, his heart pounding with excitement. 
    The tall trees whispered secrets in the wind, and magical creatures peeked out from behind moss-covered rocks. 
    Suddenly, he heard a soft crying sound coming from a nearby clearing. 
    "Someone needs help," he thought bravely, and decided to investigate. 
    There, sitting under a rainbow-colored mushroom, was a tiny fairy with a broken wing.
    """
    
    summary = create_chapter_summary(sample_chapter, 1, child_age=9)
    print(f"Original (len={len(sample_chapter)}):\n{sample_chapter}\n")
    print(f"Summary (len={len(summary)}):\n{summary}\n")


def test_story_context():
    """Test the structured story context builder."""
    print("=== Testing Story Context Builder ===")
    
    previous_chapters = [
        "Rohan discovered a magical forest filled with talking animals and enchanted creatures. He met Luna, a wise owl who became his guide.",
        "With Luna's help, Rohan learned to communicate with the forest animals. They warned him about a dark shadow threatening their home.",
        "Rohan and his new friends decided to work together to protect the forest from the mysterious shadow creature."
    ]
    
    previous_choices = [
        {"question": "How should Rohan enter the forest?", "chosen_option": "Walk quietly and respectfully"},
        {"question": "What should Rohan do about the threat?", "chosen_option": "Gather the animals to form a plan"}
    ]
    
    context = build_story_context(previous_chapters, previous_choices, chapter_number=4)
    
    for key, value in context.items():
        if value:
            print(f"{key.replace('_', ' ').title()}: {value}\n")


def test_enhanced_prompt():
    """Test the enhanced prompt creation."""
    print("=== Testing Enhanced Prompt Template ===")
    
    test_state = StoryGenerationState(
        child_preferences={
            "age": 9,
            "language": "english", 
            "reading_level": "intermediate",
            "interests": ["magic", "animals", "adventure"],
            "vocabulary_level": 70
        },
        story_theme="magical forest adventure",
        chapter_number=4,
        previous_chapters=[
            "Rohan discovered a magical forest with talking animals.",
            "He met Luna the owl and learned forest magic.",
            "Together they faced a mysterious shadow threat."
        ],
        previous_choices=[
            {"question": "How to approach the animals?", "chosen_option": "Speak gently and kindly"}
        ],
        custom_user_input="I want Rohan to find a magical sword!",
        story_content="",
        choices=[],
        safety_score=0.0,
        content_approved=False,
        content_issues=[],
        estimated_reading_time=0,
        vocabulary_level="",
        educational_elements=[]
    )
    
    prompt_template = create_enhanced_story_prompt(test_state)
    formatted = prompt_template.format_messages(
        age=9,
        language="english",
        reading_level="intermediate", 
        interests="magic, animals, adventure",
        vocabulary_level=70,
        theme="magical forest adventure",
        chapter_number=4
    )
    
    print("System Message:")
    print(formatted[0].content[:500] + "..." if len(formatted[0].content) > 500 else formatted[0].content)
    print("\nHuman Message:")  
    print(formatted[1].content[:800] + "..." if len(formatted[1].content) > 800 else formatted[1].content)


def test_full_workflow():
    """Test the complete optimized workflow."""
    print("\n=== Testing Complete Optimized Workflow ===")
    
    # Check if Ollama is available
    try:
        import requests
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            print("⚠️  Ollama is not available - skipping full workflow test")
            return
    except:
        print("⚠️  Ollama is not available - skipping full workflow test") 
        return
    
    test_state = StoryGenerationState(
        child_preferences={
            "age": 8,
            "language": "english",
            "reading_level": "beginner", 
            "interests": ["dragons", "friendship"],
            "vocabulary_level": 60
        },
        story_theme="dragon adventure",
        chapter_number=2,
        previous_chapters=[
            "Emma found a tiny dragon egg in her backyard. She decided to take care of it and named the dragon Sparkle when it hatched."
        ],
        previous_choices=[
            {"question": "What should Emma do with the dragon?", "chosen_option": "Keep it safe and be its friend"}
        ],
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
    
    try:
        print("Running optimized story generation workflow...")
        result = story_workflow.invoke(test_state)
        
        print(f"\n✅ Story Generated Successfully!")
        print(f"Story Content ({len(result['story_content'])} chars):")
        print(result['story_content'][:300] + "..." if len(result['story_content']) > 300 else result['story_content'])
        print(f"\nChoices: {len(result['choices'])}")
        for i, choice in enumerate(result['choices'][:2]):
            print(f"  {i+1}. {choice.get('text', 'N/A')}")
        print(f"\nEducational Elements: {result.get('educational_elements', [])}")
        print(f"Vocabulary Words: {result.get('vocabulary_words', [])}")
        print(f"Safety Score: {result.get('safety_score', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🔧 Testing Optimized Story Generation Workflow")
    print("=" * 60)
    
    test_chapter_summary()
    print()
    test_story_context() 
    print()
    test_enhanced_prompt()
    print()
    test_full_workflow()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")