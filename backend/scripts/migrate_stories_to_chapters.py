#!/usr/bin/env python3
"""
Migration script to convert existing stories from content field to chapters table.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append('/app')

from app.db.base import SessionLocal
from app.models.story import Story
from app.models.story_chapter import StoryChapter


def migrate_stories_to_chapters():
    """Convert existing stories with content to use chapters table."""
    db = SessionLocal()
    
    try:
        # Get all stories that have content but no chapters
        stories_with_content = db.query(Story).filter(
            Story.content != "",
            Story.content.isnot(None)
        ).all()
        
        migrated_count = 0
        
        for story in stories_with_content:
            # Check if this story already has chapters
            existing_chapters = db.query(StoryChapter).filter(
                StoryChapter.story_id == story.id
            ).count()
            
            if existing_chapters > 0:
                print(f"Story {story.id} already has chapters, skipping...")
                continue
            
            print(f"Migrating story {story.id}: {story.title}")
            
            # Extract content
            content = story.content.strip()
            
            # Clean up any JSON formatting artifacts
            if content.startswith('story_content: `'):
                content = content[16:]  # Remove 'story_content: `' prefix
            if content.endswith('`'):
                content = content[:-1]  # Remove trailing backtick
                
            # Create first chapter
            chapter = StoryChapter(
                story_id=story.id,
                chapter_number=1,
                title="Chapter 1",
                content=content,
                is_ending=False,
                is_published=True,
                estimated_reading_time=story.estimated_reading_time or 5,
                word_count=len(content.split()) if content else 0
            )
            
            db.add(chapter)
            migrated_count += 1
            
            print(f"  Created chapter 1 with {len(content)} characters")
        
        # Commit all changes
        db.commit()
        print(f"\nMigration completed! Migrated {migrated_count} stories to chapters.")
        
        # Optional: Clear the content field from stories (keep as backup for now)
        # Uncomment the next lines if you want to clear the old content
        # for story in stories_with_content:
        #     story.content = ""
        # db.commit()
        # print("Cleared content field from migrated stories.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_stories_to_chapters()