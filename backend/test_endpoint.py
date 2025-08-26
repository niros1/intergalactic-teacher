"""Simple test endpoint to try story generation without auth."""

from fastapi import FastAPI
from app.workflows.story_generation import StoryGenerationState, generate_story_content
import uvicorn

app = FastAPI(title="Simple Story Test")

@app.post("/generate-story")
async def test_story_generation(theme: str = "space adventure"):
    """Generate a story without authentication - for testing only."""
    
    test_state = StoryGenerationState(
        child_preferences={
            "age": 8,
            "interests": ["space", "adventure", "robots"],
            "reading_level": "beginner",
            "language": "english"
        },
        story_theme=theme,
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
    
    result = generate_story_content(test_state)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)