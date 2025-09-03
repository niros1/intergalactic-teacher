#!/usr/bin/env python3
"""
Test script to verify improved contextual suggestion system.
"""
import sys
sys.path.append('./backend')

from app.workflows.story_generation import extract_story_elements, generate_contextual_choices, extract_choice_opportunities

def test_contextual_suggestions():
    """Test the contextual suggestion system with various story scenarios."""
    
    # Test scenario 1: Path/direction story
    story1 = """
    Luna the rabbit found herself at a crossroads in the enchanted forest. 
    The left path was covered with glowing flowers, while the right path 
    led deeper into the shadows. She could hear mysterious sounds coming 
    from both directions.
    """
    
    print("=== TEST 1: Path/Direction Story ===")
    elements1 = extract_story_elements(story1)
    print(f"Characters: {elements1['characters']}")
    print(f"Locations: {elements1['locations']}")
    print(f"Choice opportunities: {elements1['choice_opportunities']}")
    
    choices1 = generate_contextual_choices(story1, elements1, child_age=9, language='english')
    print("Generated choices:")
    for i, choice in enumerate(choices1, 1):
        print(f"  {i}. {choice['text']} - {choice['description']}")
    print()
    
    # Test scenario 2: Character interaction story
    story2 = """
    Emma discovered a wise old wizard sitting by a magical fountain. 
    The wizard looked friendly but seemed to be in trouble. His magical 
    crystal was dim and he appeared worried. There was also a mysterious 
    door behind him that was slightly open.
    """
    
    print("=== TEST 2: Character Interaction Story ===")
    elements2 = extract_story_elements(story2)
    print(f"Characters: {elements2['characters']}")
    print(f"Locations: {elements2['locations']}")
    print(f"Choice opportunities: {elements2['choice_opportunities']}")
    
    choices2 = generate_contextual_choices(story2, elements2, child_age=8, language='english')
    print("Generated choices:")
    for i, choice in enumerate(choices2, 1):
        print(f"  {i}. {choice['text']} - {choice['description']}")
    print()
    
    # Test scenario 3: Hebrew language
    story3 = """
    The brave knight reached the castle gates. Inside, he could hear 
    singing and laughter. A friendly dragon was sitting outside, 
    and there was a treasure chest nearby.
    """
    
    print("=== TEST 3: Hebrew Translation ===")
    elements3 = extract_story_elements(story3)
    choices3_hebrew = generate_contextual_choices(story3, elements3, child_age=10, language='hebrew')
    print("Generated Hebrew choices:")
    for i, choice in enumerate(choices3_hebrew, 1):
        print(f"  {i}. {choice['text']} - {choice['description']}")
    print()
    
    # Test scenario 4: Generic fallback
    story4 = """
    The child went to school and learned many things. It was a nice day.
    """
    
    print("=== TEST 4: Generic/Fallback Story ===")
    elements4 = extract_story_elements(story4)
    print(f"Choice opportunities: {elements4['choice_opportunities']}")
    
    choices4 = generate_contextual_choices(story4, elements4, child_age=7, language='english')
    print("Generated choices (should be age-appropriate fallbacks):")
    for i, choice in enumerate(choices4, 1):
        print(f"  {i}. {choice['text']} - {choice['description']}")
    print()

def test_choice_extraction():
    """Test the choice opportunity extraction function."""
    print("=== CHOICE EXTRACTION TESTS ===")
    
    test_cases = [
        ("The path split into left and right directions.", "Should detect path/direction"),
        ("A mysterious door stood before them.", "Should detect door/entrance"), 
        ("The stranger approached with a friendly smile.", "Should detect character interaction"),
        ("A treasure chest glittered in the sunlight.", "Should detect object interaction"),
        ("They heard a strange sound from the cave.", "Should detect sound investigation"),
        ("The child felt scared and worried.", "Should detect emotional support"),
    ]
    
    for story_snippet, expected in test_cases:
        opportunities = extract_choice_opportunities(story_snippet)
        print(f"Story: '{story_snippet}'")
        print(f"Expected: {expected}")
        print(f"Extracted: {opportunities}")
        print()

if __name__ == "__main__":
    test_contextual_suggestions()
    test_choice_extraction()