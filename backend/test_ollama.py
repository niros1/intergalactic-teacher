#!/usr/bin/env python3
"""Test script to verify Ollama integration with the story generation workflow."""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, '/Users/niro/dev/playground/intergalactic-teacher/backend')

from app.core.config import settings
from app.workflows.story_generation import StoryGenerationState, generate_story_content

async def test_story_generation():
    """Test the story generation workflow with Ollama."""
    
    print("🧪 Testing Ollama Integration with Story Generation Workflow")
    print(f"📡 Ollama Base URL: {settings.OLLAMA_BASE_URL}")
    print(f"🤖 Ollama Model: {settings.OLLAMA_MODEL}")
    print("-" * 60)
    
    # Create test state
    test_state = StoryGenerationState(
        child_preferences={
            "age": 8,
            "interests": ["space", "adventure", "robots"],
            "reading_level": "beginner",
            "language": "english"
        },
        story_theme="space adventure with friendly robots",
        chapter_number=1,
        previous_chapters=[],
        previous_choices=[],
        story_content="",
        choices=[],
        safety_score=0.0,
        content_approved=False,
        content_issues=[],
        estimated_reading_time=0,
        vocabulary_level="beginner",
        educational_elements=[]
    )
    
    print("🚀 Generating story with Ollama...")
    print("⏳ This may take a moment...")
    
    try:
        # Generate story content
        result = generate_story_content(test_state)
        
        print("\n✅ Story Generation Successful!")
        print("-" * 60)
        print("📖 Generated Story:")
        print(result.get("story_content", "No content generated"))
        
        if result.get("choices"):
            print("\n🎯 Generated Choices:")
            for i, choice in enumerate(result["choices"], 1):
                print(f"   {i}. {choice}")
        
        print(f"\n📊 Metadata:")
        print(f"   📚 Reading Time: {result.get('estimated_reading_time', 'Unknown')} minutes")
        print(f"   🎓 Vocabulary Level: {result.get('vocabulary_level', 'Unknown')}")
        print(f"   📖 Educational Elements: {result.get('educational_elements', [])}")
        
    except Exception as e:
        print(f"\n❌ Story Generation Failed!")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_story_generation())