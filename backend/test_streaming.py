#!/usr/bin/env python3
"""
Quick test script to verify streaming implementation structure.

This script tests:
1. SSE formatter functions
2. Basic async generator structure
3. Event format compliance

For full integration testing, use the API endpoint with curl or a proper HTTP client.
"""

import asyncio
import json
from app.utils.sse_formatter import (
    format_content_chunk,
    format_node_event,
    format_safety_check_event,
    format_metadata_event,
    format_complete_event,
    format_error_event,
)


def test_sse_formatters():
    """Test SSE formatter functions."""
    print("🧪 Testing SSE Formatters\n")

    # Test content chunk
    print("1. Content Chunk:")
    event = format_content_chunk("Once upon a time...", is_complete=False)
    print(event)
    assert "event: story_chunk" in event
    assert '"type": "content"' in event
    assert "Once upon a time..." in event
    print("✅ Content chunk format correct\n")

    # Test node event
    print("2. Node Event:")
    event = format_node_event("generate_content", "started")
    print(event)
    assert "event: story_chunk" in event
    assert '"type": "node_event"' in event
    assert '"node": "generate_content"' in event
    print("✅ Node event format correct\n")

    # Test safety check event
    print("3. Safety Check Event:")
    event = format_safety_check_event(approved=True, score=1.0, issues=[])
    print(event)
    assert "event: story_chunk" in event
    assert '"type": "safety_check"' in event
    assert '"approved": true' in event
    print("✅ Safety check event format correct\n")

    # Test metadata event
    print("4. Metadata Event:")
    event = format_metadata_event(
        estimated_reading_time=5,
        vocabulary_level="intermediate",
        educational_elements=["Problem solving", "Friendship"]
    )
    print(event)
    assert "event: story_chunk" in event
    assert '"type": "metadata"' in event
    assert '"estimated_reading_time": 5' in event
    print("✅ Metadata event format correct\n")

    # Test complete event
    print("5. Complete Event:")
    event = format_complete_event({
        "success": True,
        "story_content": "The complete story...",
        "choices": [{"text": "Choice 1"}]
    })
    print(event)
    assert "event: story_chunk" in event
    assert '"type": "complete"' in event
    assert '"success": true' in event
    print("✅ Complete event format correct\n")

    # Test error event
    print("6. Error Event:")
    event = format_error_event(
        error_message="Something went wrong",
        error_code="TEST_ERROR"
    )
    print(event)
    assert "event: story_chunk" in event
    assert '"type": "error"' in event
    assert "Something went wrong" in event
    print("✅ Error event format correct\n")


async def test_async_generator_structure():
    """Test basic async generator structure (without actual workflow)."""
    print("\n🧪 Testing Async Generator Structure\n")

    async def mock_story_stream():
        """Mock stream generator for testing."""
        # Simulate workflow events
        yield format_node_event("workflow", "started", {"chapter_number": 1})
        await asyncio.sleep(0.1)

        yield format_node_event("generate_content", "started")
        await asyncio.sleep(0.1)

        # Simulate content chunks
        paragraphs = [
            "Once upon a time, in a land far away...",
            "There lived a brave young explorer.",
            "She loved discovering new places and meeting new friends."
        ]

        for para in paragraphs:
            yield format_content_chunk(para)
            await asyncio.sleep(0.1)

        yield format_node_event("generate_content", "completed")
        await asyncio.sleep(0.1)

        yield format_node_event("safety_check", "started")
        await asyncio.sleep(0.1)

        yield format_safety_check_event(approved=True, score=1.0, issues=[])
        yield format_node_event("safety_check", "completed")
        await asyncio.sleep(0.1)

        yield format_metadata_event(
            estimated_reading_time=3,
            vocabulary_level="beginner",
            educational_elements=["Exploration", "Friendship"]
        )

        yield format_complete_event({
            "success": True,
            "story_content": " ".join(paragraphs),
            "choices": [
                {"text": "Explore the forest"},
                {"text": "Visit the village"}
            ],
            "choice_question": "Where should she go next?"
        })

    event_count = 0
    events_by_type = {}

    async for event in mock_story_stream():
        event_count += 1

        # Extract event type from SSE format
        if "data: " in event:
            data_line = [line for line in event.split("\n") if line.startswith("data: ")][0]
            data = json.loads(data_line[6:])  # Remove "data: " prefix
            event_type = data.get("type", "unknown")

            if event_type not in events_by_type:
                events_by_type[event_type] = 0
            events_by_type[event_type] += 1

            print(f"Event {event_count}: {event_type}")

    print(f"\n✅ Async generator completed")
    print(f"Total events: {event_count}")
    print(f"Events by type: {events_by_type}")

    # Verify expected events
    assert events_by_type.get("node_event", 0) >= 6, "Should have multiple node events"
    assert events_by_type.get("content", 0) == 3, "Should have 3 content chunks"
    assert events_by_type.get("safety_check", 0) == 1, "Should have 1 safety check"
    assert events_by_type.get("metadata", 0) == 1, "Should have 1 metadata event"
    assert events_by_type.get("complete", 0) == 1, "Should have 1 complete event"

    print("✅ All event types present and correct\n")


def test_sse_format_compliance():
    """Verify SSE format compliance."""
    print("🧪 Testing SSE Format Compliance\n")

    event = format_content_chunk("Test content")
    lines = event.split("\n")

    # Check for event type line
    assert any(line.startswith("event: ") for line in lines), "Should have event type"

    # Check for data line
    assert any(line.startswith("data: ") for line in lines), "Should have data line"

    # Check for blank lines (event separator)
    assert lines[-1] == "", "Should end with blank line"
    assert lines[-2] == "", "Should have double newline"

    # Verify JSON in data line
    data_line = [line for line in lines if line.startswith("data: ")][0]
    data_json = data_line[6:]  # Remove "data: " prefix
    parsed_data = json.loads(data_json)

    assert "type" in parsed_data, "Data should have 'type' field"
    assert "data" in parsed_data, "Data should have 'data' field"

    print("✅ SSE format is compliant\n")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  Streaming Implementation Tests")
    print("="*60 + "\n")

    try:
        # Test SSE formatters
        test_sse_formatters()

        # Test SSE format compliance
        test_sse_format_compliance()

        # Test async generator structure
        asyncio.run(test_async_generator_structure())

        print("\n" + "="*60)
        print("  ✅ All Tests Passed!")
        print("="*60 + "\n")

        print("Next Steps:")
        print("1. Rebuild Docker container: cd backend && docker-compose up --build -d api")
        print("2. Test API endpoint with curl or a frontend")
        print("3. Coordinate with langchain-langgraph-expert for workflow streaming")
        print("\nSee STREAMING_SUMMARY.md for complete testing guide.")

    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
