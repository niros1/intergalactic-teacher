#!/usr/bin/env python3
"""
Test script to debug previous_chapters context issue.
Compares how the workflow handles previous_chapters vs previous_choices.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.workflows.story_generation import create_story_prompt, StoryGenerationState

def test_previous_chapters_vs_choices():
    """Test to demonstrate the issue with previous_chapters context."""
    
    # Sample previous chapters (realistic story content)
    previous_chapters = [
        "Rohan was a brave 9-year-old boy who lived in a small village near the Whispering Woods. One sunny morning, he decided to explore the mysterious forest that had always fascinated him. As he ventured deeper into the woods, he met Luna, a wise talking owl with silver feathers who became his guide. Luna warned him about the ancient magic that protected the forest and told him that only those with pure hearts could see the forest's true wonders. Together, they discovered a hidden clearing where magical flowers glowed with their own light.",
        
        "In the enchanted clearing, Rohan and Luna encountered Pip, a mischievous fairy who lived in the glowing flowers. Pip explained that the forest was in danger - a shadow creature had been stealing the light from the magical flowers, causing parts of the forest to wither. The fairy asked Rohan to help save the forest by finding three special crystals hidden throughout the woods. Each crystal held the power of different elements: earth, water, and air. Rohan accepted the quest, knowing that his new friends were counting on him."
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
    
    # Generate the prompt
    prompt = create_story_prompt(state)
    
    print("=== GENERATED PROMPT ===")
    print(prompt)
    print("\n" + "="*80 + "\n")
    
    # Analyze the prompt structure
    print("=== ANALYSIS ===")
    
    # Check previous chapters section
    if "STORY CONTEXT (Previous chapters):" in prompt:
        chapters_start = prompt.find("STORY CONTEXT (Previous chapters):")
        chapters_end = prompt.find("\n\nPREVIOUS CHOICES MADE:")
        if chapters_end == -1:
            chapters_end = prompt.find("\n\nCUSTOM USER INPUT:")
        if chapters_end == -1:
            chapters_end = prompt.find("\n\nOUTPUT FORMAT:")
        
        chapters_section = prompt[chapters_start:chapters_end] if chapters_end > chapters_start else prompt[chapters_start:]
        print(f"Previous Chapters Section Length: {len(chapters_section)} characters")
        print(f"Number of chapters included: {len(previous_chapters)}")
        
        # Check if chapters are truncated
        for i, chapter in enumerate(previous_chapters):
            if f"Chapter {i+1}:" in chapters_section:
                print(f"✓ Chapter {i+1} is included")
                # Check if it's truncated
                if len(chapter) > 800 and "..." in chapters_section:
                    print(f"  ⚠️  Chapter {i+1} is truncated (original: {len(chapter)} chars)")
            else:
                print(f"✗ Chapter {i+1} is missing")
    
    # Check previous choices section
    if "PREVIOUS CHOICES MADE:" in prompt:
        print("✓ Previous choices section is included")
        choices_start = prompt.find("PREVIOUS CHOICES MADE:")
        choices_end = prompt.find("\n\nCUSTOM USER INPUT:")
        if choices_end == -1:
            choices_end = prompt.find("\n\nOUTPUT FORMAT:")
        
        choices_section = prompt[choices_start:choices_end] if choices_end > choices_start else prompt[choices_start:]
        print(f"Previous Choices Section Length: {len(choices_section)} characters")
        
        for choice in previous_choices:
            if choice["chosen_option"] in choices_section:
                print(f"✓ Choice '{choice['chosen_option']}' is included")
            else:
                print(f"✗ Choice '{choice['chosen_option']}' is missing")
    
    # Token count estimation
    estimated_tokens = len(prompt.split())
    print(f"\nEstimated token count: {estimated_tokens}")
    
    if estimated_tokens > 2000:
        print("⚠️  Prompt may be too long for optimal LLM performance")
    
    return prompt

if __name__ == "__main__":
    test_previous_chapters_vs_choices()