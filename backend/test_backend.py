#!/usr/bin/env python3
"""
Simple test backend for testing the frontend chapter display functionality.
This bypasses the complex AI generation and just returns mock content.
"""

import json
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Mock data
MOCK_USERS = {
    "1": {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True
    }
}

MOCK_CHILDREN = {
    "1": {
        "id": 1,
        "name": "Test Child",
        "age": 8,
        "reading_level": "intermediate",
        "language_preference": "english",
        "interests": ["adventure", "magic"]
    }
}

MOCK_SESSIONS = {}
STORY_COUNTER = 1
SESSION_COUNTER = 1

# Initialize mock database
def init_db():
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    
    # Create basic tables for testing
    cursor.execute('''CREATE TABLE IF NOT EXISTS stories 
                     (id INTEGER PRIMARY KEY, title TEXT, content TEXT, theme TEXT, 
                      difficulty_level TEXT, language TEXT, total_chapters INTEGER)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS story_sessions 
                     (id INTEGER PRIMARY KEY, story_id INTEGER, child_id INTEGER, 
                      current_chapter INTEGER, is_completed BOOLEAN, created_at TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS story_chapters 
                     (id INTEGER PRIMARY KEY, story_id INTEGER, chapter_number INTEGER, 
                      title TEXT, content TEXT, created_at TEXT)''')
                      
    conn.commit()
    conn.close()

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    return jsonify({
        "access_token": "mock_token",
        "token_type": "bearer",
        "user": MOCK_USERS["1"]
    })

@app.route('/api/v1/children/me', methods=['GET'])
def get_children():
    return jsonify([MOCK_CHILDREN["1"]])

@app.route('/api/v1/stories', methods=['GET'])
def get_stories():
    return jsonify([])

@app.route('/api/v1/stories/generate', methods=['POST'])
def generate_story():
    global STORY_COUNTER
    data = request.get_json()
    
    story_id = STORY_COUNTER
    STORY_COUNTER += 1
    
    # Create mock story content
    story_content = f"""Once upon a time, in a magical land of {data.get('theme', 'adventure')}, there lived a brave young hero. 
    
The hero discovered that they had special powers and needed to use them to help their friends and family.

Along the way, they met many interesting characters who would help them on their journey."""
    
    # Mock choices for the first chapter
    choices = [
        {
            "id": "choice1",
            "text": "Explore the mysterious forest",
            "impact": "normal",
            "description": "Venture into the unknown woods to find adventure"
        },
        {
            "id": "choice2", 
            "text": "Visit the wise old wizard",
            "impact": "normal",
            "description": "Seek guidance from the magical mentor"
        }
    ]
    
    # Save to mock database
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO stories 
                     (id, title, content, theme, difficulty_level, language, total_chapters)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                   (story_id, f"{data.get('theme', 'Adventure').title()} Story", 
                    story_content, data.get('theme', 'adventure'), 'intermediate', 
                    'english', 3))
    
    cursor.execute('''INSERT INTO story_chapters 
                     (story_id, chapter_number, title, content, created_at)
                     VALUES (?, ?, ?, ?, ?)''',
                   (story_id, 1, "Chapter 1", story_content, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "id": str(story_id),
        "title": f"{data.get('theme', 'Adventure').title()} Story",
        "content": story_content.split('\n    \n'),
        "language": "english",
        "readingLevel": "intermediate", 
        "theme": data.get('theme', 'adventure'),
        "choices": choices,
        "isCompleted": False,
        "currentChapter": 1,
        "totalChapters": 3,
        "createdAt": datetime.now().isoformat(),
        "success": True
    })

@app.route('/api/v1/stories/<story_id>/sessions', methods=['POST'])
def create_session(story_id):
    global SESSION_COUNTER
    data = request.get_json()
    
    session_id = SESSION_COUNTER
    SESSION_COUNTER += 1
    
    # Save session to database
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO story_sessions 
                     (id, story_id, child_id, current_chapter, is_completed, created_at)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                   (session_id, int(story_id), data.get('child_id'), 1, False, 
                    datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    # Get story info
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stories WHERE id = ?', (int(story_id),))
    story = cursor.fetchone()
    conn.close()
    
    session_data = {
        "id": str(session_id),
        "story_id": story_id,
        "child_id": data.get('child_id'),
        "current_chapter": 1,
        "is_completed": False,
        "created_at": datetime.now().isoformat()
    }
    
    if story:
        story_data = {
            "id": str(story[0]),
            "title": story[1],
            "content": story[2].split('\n    \n'),
            "theme": story[3],
            "readingLevel": story[4],
            "language": story[5],
            "totalChapters": story[6],
            "currentChapter": 1,
            "isCompleted": False,
            "choices": [
                {
                    "id": "choice1",
                    "text": "Explore the mysterious forest",
                    "impact": "normal"
                },
                {
                    "id": "choice2",
                    "text": "Visit the wise old wizard", 
                    "impact": "normal"
                }
            ]
        }
        
        return jsonify({
            "session": session_data,
            "story": story_data
        })
    
    return jsonify(session_data)

@app.route('/api/v1/stories/sessions/<session_id>/choices', methods=['POST'])
def make_choice(session_id):
    data = request.get_json()
    choice_id = data.get('choiceId')
    
    # Get current session
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM story_sessions WHERE id = ?', (int(session_id),))
    session = cursor.fetchone()
    
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
        
    current_chapter = session[3]  # current_chapter column
    next_chapter = current_chapter + 1
    story_id = session[1]  # story_id column
    
    # Generate new chapter content based on the choice
    if choice_id == "choice1" or choice_id == "continue":
        new_content = f"""Chapter {next_chapter}: The Forest Path

You decided to explore the mysterious forest. As you walk deeper into the woods, the trees seem to whisper ancient secrets.

Suddenly, you come across a clearing where a beautiful unicorn is drinking from a crystal-clear stream.

The unicorn looks at you with wise, knowing eyes and speaks: "I have been waiting for you, young hero."
"""
    else:
        new_content = f"""Chapter {next_chapter}: The Wizard's Tower

You chose to visit the wise old wizard in his tall tower. As you climb the spiral stairs, you smell herbs and magic potions.

The wizard greets you with a warm smile: "Welcome, young adventurer! I have something special to show you."

He waves his staff and reveals a magical map that glows with mysterious symbols.
"""
    
    # Create choices for the new chapter
    new_choices = []
    if next_chapter < 3:  # Not the last chapter
        new_choices = [
            {
                "id": "choice3",
                "text": "Ask about the ancient magic",
                "impact": "normal"
            },
            {
                "id": "choice4", 
                "text": "Request to learn a spell",
                "impact": "normal"
            }
        ]
    
    is_ending = next_chapter >= 3
    
    # Save new chapter
    cursor.execute('''INSERT INTO story_chapters 
                     (story_id, chapter_number, title, content, created_at)
                     VALUES (?, ?, ?, ?, ?)''',
                   (story_id, next_chapter, f"Chapter {next_chapter}", 
                    new_content, datetime.now().isoformat()))
    
    # Update session
    cursor.execute('''UPDATE story_sessions 
                     SET current_chapter = ?, is_completed = ? 
                     WHERE id = ?''',
                   (next_chapter, is_ending, int(session_id)))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "branch_content": new_content,
        "is_ending": is_ending,
        "next_chapter": next_chapter,
        "completion_percentage": int((next_chapter / 3) * 100),
        "new_choices": new_choices
    })

if __name__ == '__main__':
    init_db()
    print("Starting test backend on http://localhost:8001")
    app.run(debug=True, port=8001)