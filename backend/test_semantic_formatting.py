"""Test script for semantic content generation with child-friendly formatting."""

import asyncio
import time
import sys
import os
from typing import Dict

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.workflows.story_generation import story_workflow, StoryGenerationState
from app.core.config import settings

async def test_english_story():
    """Test story generation with English content."""
    print("\n" + "="*80)
    print("🧪 TEST 1: ENGLISH STORY GENERATION")
    print("="*80 + "\n")
    
    # Create initial state
    initial_state: StoryGenerationState = {
        "child_preferences": {
            "name": "Emma",
            "age": 9,
            "language": "english",
            "reading_level": "intermediate",
            "interests": ["adventure", "animals"],
            "vocabulary_level": 60
        },
        "story_theme": "adventure",
        "chapter_number": 1,
        "previous_chapters": [],
        "previous_choices": [],
        "custom_user_input": None,
        "welcome_message": "",
        "story_content": "",
        "choice_question": "",
        "choices": [],
        "safety_score": 0.0,
        "content_approved": False,
        "content_issues": [],
        "estimated_reading_time": 0,
        "vocabulary_level": "",
        "educational_elements": []
    }
    
    start_time = time.time()
    
    try:
        # Run the workflow
        print("⏳ Generating story... (this may take 30-60 seconds)")
        result = story_workflow.invoke(initial_state)
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        print(f"\n✅ Story generated in {generation_time:.2f} seconds")
        print("\n" + "-"*80)
        print("📖 STORY CONTENT:")
        print("-"*80)
        print(result["story_content"])
        print("-"*80)
        
        # Analyze the content
        analyze_story_formatting(result["story_content"], "English")
        
        return generation_time
        
    except Exception as e:
        print(f"\n❌ Error generating English story: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_hebrew_story():
    """Test story generation with Hebrew content."""
    print("\n" + "="*80)
    print("🧪 TEST 2: HEBREW STORY GENERATION")
    print("="*80 + "\n")
    
    # Create initial state
    initial_state: StoryGenerationState = {
        "child_preferences": {
            "name": "נועה",  # Noa in Hebrew
            "age": 8,
            "language": "hebrew",
            "reading_level": "beginner",
            "interests": ["animals", "friendship"],
            "vocabulary_level": 50
        },
        "story_theme": "animals",
        "chapter_number": 1,
        "previous_chapters": [],
        "previous_choices": [],
        "custom_user_input": None,
        "welcome_message": "",
        "story_content": "",
        "choice_question": "",
        "choices": [],
        "safety_score": 0.0,
        "content_approved": False,
        "content_issues": [],
        "estimated_reading_time": 0,
        "vocabulary_level": "",
        "educational_elements": []
    }
    
    start_time = time.time()
    
    try:
        # Run the workflow
        print("⏳ Generating story... (this may take 30-60 seconds)")
        result = story_workflow.invoke(initial_state)
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        print(f"\n✅ Story generated in {generation_time:.2f} seconds")
        print("\n" + "-"*80)
        print("📖 STORY CONTENT:")
        print("-"*80)
        print(result["story_content"])
        print("-"*80)
        
        # Analyze the content
        analyze_story_formatting(result["story_content"], "Hebrew")
        
        return generation_time
        
    except Exception as e:
        print(f"\n❌ Error generating Hebrew story: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_story_formatting(content: str, language: str):
    """Analyze the story content for child-friendly formatting."""
    print("\n" + "="*80)
    print(f"📊 FORMATTING ANALYSIS ({language})")
    print("="*80 + "\n")
    
    # Split by double newlines to get paragraphs
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    # Analyze paragraphs
    print(f"📝 Total Paragraphs: {len(paragraphs)}")
    
    paragraph_analysis = []
    for i, para in enumerate(paragraphs, 1):
        # Count sentences (approximate by counting . ! ?)
        sentence_count = sum(1 for char in para if char in '.!?')
        # Count words
        word_count = len(para.split())
        # Average words per sentence
        avg_words = word_count / max(sentence_count, 1)
        
        paragraph_analysis.append({
            'number': i,
            'sentences': sentence_count,
            'words': word_count,
            'avg_words_per_sentence': avg_words
        })
        
        status = "✅" if sentence_count <= 3 else "⚠️"
        word_status = "✅" if avg_words <= 15 else "⚠️"
        
        print(f"{status} Paragraph {i}: {sentence_count} sentences, {word_count} words")
        print(f"   {word_status} Avg words/sentence: {avg_words:.1f}")
    
    # Overall statistics
    total_sentences = sum(p['sentences'] for p in paragraph_analysis)
    total_words = sum(p['words'] for p in paragraph_analysis)
    avg_words_overall = total_words / max(total_sentences, 1)
    
    print(f"\n📈 OVERALL STATISTICS:")
    print(f"  Total Words: {total_words}")
    print(f"  Total Sentences: {total_sentences}")
    print(f"  Avg Words/Sentence: {avg_words_overall:.1f}")
    
    # Check compliance with requirements
    print(f"\n🎯 COMPLIANCE CHECK:")
    paragraphs_ok = sum(1 for p in paragraph_analysis if p['sentences'] <= 3)
    sentences_ok = sum(1 for p in paragraph_analysis if p['avg_words_per_sentence'] <= 15)
    
    para_compliance = (paragraphs_ok / len(paragraphs) * 100) if paragraphs else 0
    sent_compliance = (sentences_ok / len(paragraphs) * 100) if paragraphs else 0
    
    print(f"  Paragraphs with ≤3 sentences: {paragraphs_ok}/{len(paragraphs)} ({para_compliance:.1f}%)")
    print(f"  Paragraphs with ≤15 words/sentence: {sentences_ok}/{len(paragraphs)} ({sent_compliance:.1f}%)")
    
    if para_compliance >= 80 and sent_compliance >= 80:
        print(f"\n✅ EXCELLENT! Story meets child-friendly formatting requirements!")
    elif para_compliance >= 60 and sent_compliance >= 60:
        print(f"\n⚠️  GOOD, but could be improved. Some paragraphs could be shorter.")
    else:
        print(f"\n❌ NEEDS IMPROVEMENT. Many paragraphs are too long or complex.")


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 SEMANTIC CONTENT GENERATION TEST SUITE")
    print("Testing child-friendly formatting with LLM")
    print("="*80)
    
    print(f"\n🔧 Configuration:")
    print(f"  Ollama Model: {settings.OLLAMA_MODEL}")
    print(f"  Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"  Temperature: {settings.OLLAMA_TEMPERATURE}")
    
    # Test English
    english_time = await test_english_story()
    
    # Test Hebrew
    hebrew_time = await test_hebrew_story()
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80 + "\n")
    
    if english_time and hebrew_time:
        avg_time = (english_time + hebrew_time) / 2
        print(f"✅ All tests completed successfully!")
        print(f"  English generation time: {english_time:.2f}s")
        print(f"  Hebrew generation time: {hebrew_time:.2f}s")
        print(f"  Average generation time: {avg_time:.2f}s")
        
        if avg_time < 60:
            print(f"\n✅ Performance: EXCELLENT (< 60s)")
        elif avg_time < 90:
            print(f"\n⚠️  Performance: ACCEPTABLE (60-90s)")
        else:
            print(f"\n❌ Performance: SLOW (> 90s)")
    else:
        print(f"❌ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())

