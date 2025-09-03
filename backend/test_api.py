#!/usr/bin/env python3
"""Simple test API to demonstrate Ollama story generation without authentication issues."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, '/Users/niro/dev/playground/intergalactic-teacher/backend')

from app.workflows.story_generation import StoryGenerationState, generate_story_content

app = FastAPI(
    title="Intergalactic Teacher - Story Test API",
    description="Test API for Ollama-powered story generation",
    version="1.0.0"
)

class StoryRequest(BaseModel):
    theme: str = "space adventure"
    child_age: int = 8
    interests: List[str] = ["space", "adventure", "robots"]
    reading_level: str = "beginner"
    language: str = "english"
    chapter_number: int = 1

class StoryResponse(BaseModel):
    story_content: str
    choices: List[dict]
    educational_elements: List[str]
    estimated_reading_time: int
    vocabulary_level: str

@app.get("/")
async def root():
    """Welcome endpoint."""
    return {
        "message": "🚀 Intergalactic Teacher - Ollama Story Generation API",
        "status": "running",
        "model": "llama3.3:latest"
    }

@app.post("/generate-story", response_model=dict)
async def generate_story(request: StoryRequest):
    """Generate an interactive story using Ollama."""
    
    try:
        # Create story generation state
        state = StoryGenerationState(
            child_preferences={
                "age": request.child_age,
                "interests": request.interests,
                "reading_level": request.reading_level,
                "language": request.language
            },
            story_theme=request.theme,
            chapter_number=request.chapter_number,
            previous_chapters=[],
            previous_choices=[],
            story_content="",
            choices=[],
            safety_score=0.0,
            content_approved=False,
            content_issues=[],
            estimated_reading_time=0,
            vocabulary_level=request.reading_level,
            educational_elements=[]
        )
        
        # Generate story using Ollama
        result = generate_story_content(state)
        
        return {
            "success": True,
            "story": result,
            "metadata": {
                "model": "llama3.3:latest",
                "theme": request.theme,
                "child_age": request.child_age,
                "reading_level": request.reading_level
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "story-generation"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)