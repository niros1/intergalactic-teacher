#!/usr/bin/env python3
"""
Test script to verify the frontend chapter display functionality.
This script tests the API endpoints to ensure they work correctly.
"""

import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

def test_login():
    """Test user login"""
    print("Testing login...")
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "test@example.com",
        "password": "password"
    })
    print(f"Login response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Login successful. Token: {data.get('access_token', 'N/A')[:20]}...")
        return data.get('access_token')
    return None

def test_get_children(token):
    """Test getting children"""
    print("\nTesting get children...")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.get(f"{BASE_URL}/children/me", headers=headers)
    print(f"Get children response: {response.status_code}")
    if response.status_code == 200:
        children = response.json()
        print(f"Found {len(children)} children")
        return children[0] if children else None
    return None

def test_generate_story(token, child_id):
    """Test story generation"""
    print("\nTesting story generation...")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.post(f"{BASE_URL}/stories/generate", 
                           headers=headers,
                           json={
                               "child_id": child_id,
                               "theme": "adventure",
                               "title": "Test Adventure Story"
                           })
    print(f"Story generation response: {response.status_code}")
    if response.status_code == 200:
        story = response.json()
        print(f"Generated story: {story.get('title', 'N/A')}")
        print(f"Story ID: {story.get('id', 'N/A')}")
        print(f"Content paragraphs: {len(story.get('content', []))}")
        print(f"Choices: {len(story.get('choices', []))}")
        return story
    else:
        print(f"Error: {response.text}")
    return None

def test_create_session(token, story_id, child_id):
    """Test creating a story session"""
    print(f"\nTesting session creation for story {story_id}...")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.post(f"{BASE_URL}/stories/{story_id}/sessions",
                           headers=headers,
                           json={"child_id": child_id})
    print(f"Session creation response: {response.status_code}")
    if response.status_code == 200:
        session_data = response.json()
        session_id = session_data.get('session', {}).get('id') or session_data.get('id')
        print(f"Created session: {session_id}")
        return session_id
    else:
        print(f"Error: {response.text}")
    return None

def test_make_choice(token, session_id, choice_id):
    """Test making a choice in the story"""
    print(f"\nTesting choice making with choice: {choice_id}...")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.post(f"{BASE_URL}/stories/sessions/{session_id}/choices",
                           headers=headers,
                           json={
                               "choiceId": choice_id,
                               "timestamp": "2025-01-01T00:00:00.000Z"
                           })
    print(f"Choice response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Choice successful: {result.get('success', False)}")
        print(f"New chapter content length: {len(result.get('branch_content', ''))}")
        print(f"Is ending: {result.get('is_ending', False)}")
        print(f"Next chapter: {result.get('next_chapter', 'N/A')}")
        print(f"New choices: {len(result.get('new_choices', []))}")
        return result
    else:
        print(f"Error: {response.text}")
    return None

def test_continue_story(token, session_id):
    """Test continuing story without specific choice"""
    print(f"\nTesting story continuation...")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.post(f"{BASE_URL}/stories/sessions/{session_id}/choices",
                           headers=headers,
                           json={
                               "choiceId": "continue",
                               "timestamp": "2025-01-01T00:00:00.000Z"
                           })
    print(f"Continue response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Continue successful: {result.get('success', False)}")
        print(f"New chapter content length: {len(result.get('branch_content', ''))}")
        print(f"Is ending: {result.get('is_ending', False)}")
        print(f"Next chapter: {result.get('next_chapter', 'N/A')}")
        return result
    else:
        print(f"Error: {response.text}")
    return None

def main():
    """Run the complete test flow"""
    print("=== Testing Frontend Chapter Display Flow ===")
    
    # Test login
    token = test_login()
    if not token:
        print("Login failed, continuing without token...")
        token = None
    
    # Test get children
    child = test_get_children(token)
    if not child:
        print("No children found, using mock child ID...")
        child_id = 1
    else:
        child_id = child.get('id', 1)
    
    # Test story generation
    story = test_generate_story(token, child_id)
    if not story:
        print("Story generation failed!")
        return
    
    story_id = story.get('id')
    
    # Test session creation
    session_id = test_create_session(token, story_id, child_id)
    if not session_id:
        print("Session creation failed!")
        return
    
    # Test making a choice
    choice_result = test_make_choice(token, session_id, "choice1")
    if not choice_result:
        print("Choice making failed!")
        return
    
    # Test continuing the story (if not ending)
    if not choice_result.get('is_ending', True):
        continue_result = test_continue_story(token, session_id)
        if continue_result:
            print("\n=== Test Flow Completed Successfully! ===")
            print("Frontend should now be able to:")
            print("1. Generate a story with multiple chapters")
            print("2. Display chapter content after making choices") 
            print("3. Show new choices for the next chapter")
            print("4. Continue to subsequent chapters")
        else:
            print("Story continuation failed!")
    else:
        print("\n=== Test Flow Completed! ===")
        print("Story ended after first choice.")

if __name__ == "__main__":
    main()