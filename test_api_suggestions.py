#!/usr/bin/env python3
"""
Simple test to verify the API is working with improved suggestions.
"""
import requests
import json

def test_story_generation():
    """Test story generation API with various scenarios."""
    
    api_url = "http://localhost:8000/api/v1/stories/generate"
    
    # Test data
    test_request = {
        "child_preferences": {
            "age": 9,
            "language": "english",
            "reading_level": "intermediate",
            "interests": ["adventure", "magic"],
            "vocabulary_level": 70
        },
        "story_theme": "magical forest adventure",
        "chapter_number": 1,
        "previous_chapters": [],
        "previous_choices": [],
        "custom_user_input": "I want to meet a friendly dragon!"
    }
    
    print("=== Testing Story Generation API ===")
    print("Making request to:", api_url)
    print("Request data:", json.dumps(test_request, indent=2))
    print()
    
    try:
        response = requests.post(api_url, json=test_request, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n=== SUCCESS! Generated Story ===")
            print(f"Story Content: {data['story_content'][:200]}...")
            print(f"\n=== Generated Choices ===")
            for i, choice in enumerate(data.get('choices', []), 1):
                print(f"{i}. {choice['text']} - {choice['description']}")
            print(f"\nEducational Elements: {data.get('educational_elements', [])}")
            print(f"Vocabulary Words: {data.get('vocabulary_words', [])}")
            print(f"Reading Time: {data.get('estimated_reading_time')} minutes")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Connection Error: Is the API server running? Try:")
        print("cd backend && docker-compose up -d api")
    except Exception as e:
        print(f"Error: {e}")

def test_second_chapter():
    """Test contextual continuation with previous chapter."""
    
    api_url = "http://localhost:8000/api/v1/stories/generate"
    
    test_request = {
        "child_preferences": {
            "age": 8,
            "language": "english", 
            "reading_level": "beginner",
            "interests": ["animals", "friendship"],
            "vocabulary_level": 50
        },
        "story_theme": "forest adventure",
        "chapter_number": 2,
        "previous_chapters": [
            "Emma the rabbit discovered a magical clearing where Luna the wise owl lived. Luna showed Emma a mysterious glowing door hidden behind the great oak tree. The door hummed with magical energy and had two paths leading away from it - one going left toward a sparkling stream, and another going right toward a dark cave."
        ],
        "previous_choices": [
            {
                "question": "What should Emma do next?",
                "chosen_option": "Talk to Luna about the door"
            }
        ],
        "custom_user_input": None
    }
    
    print("\n=== Testing Chapter 2 Continuation ===")
    print("Previous story includes Luna (owl), Emma (rabbit), magical door, left path (stream), right path (cave)")
    print()
    
    try:
        response = requests.post(api_url, json=test_request, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("=== Chapter 2 Generated ===")
            print(f"Story: {data['story_content'][:300]}...")
            print(f"\n=== Contextual Choices (should reference Luna, paths, door, etc.) ===")
            for i, choice in enumerate(data.get('choices', []), 1):
                print(f"{i}. {choice['text']} - {choice['description']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_story_generation()
    test_second_chapter()