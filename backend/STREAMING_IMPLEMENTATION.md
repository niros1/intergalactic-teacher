# Story Generation Streaming Implementation

## Overview

This document explains the streaming implementation for the story generation workflow, including the architectural decisions, technical approach, limitations, and usage examples.

## Architecture

### Streaming Approach

We use **LangGraph's `astream_events()` API (v2)** to stream workflow execution events in real-time. This provides:
- Node-level progress updates
- LLM token streaming (when available)
- Structured output at completion
- Error handling and recovery

### Key Components

1. **Workflow** (`app/workflows/story_generation.py`):
   - LangGraph StateGraph with 4 nodes: `generate_content` → `safety_check` → `enhance_content` (conditional) → `calculate_metrics`
   - Compiled workflow with `astream_events()` support

2. **Service Layer** (`app/services/story_service.py`):
   - `generate_personalized_story_stream()` - Async generator that yields SSE events
   - Wraps workflow streaming and formats events

3. **API Endpoint** (`app/api/api_v1/endpoints/stories.py`):
   - `GET /api/v1/stories/generate/stream` - Returns FastAPI StreamingResponse
   - Server-Sent Events (SSE) format for client consumption

4. **SSE Formatter** (`app/utils/sse_formatter.py`):
   - Utility functions to format different event types
   - Standardized SSE protocol implementation

## Technical Details

### Streaming vs Structured Output Trade-off

**The Challenge**: LangChain's `with_structured_output()` parses the complete LLM response into a Pydantic model AFTER generation completes. This means we cannot stream individual tokens AND get structured output simultaneously.

**Our Solution**: Hybrid approach
1. **Content Generation Phase**: Stream paragraph chunks after the LLM completes generation
2. **Structured Output**: Parse the full response into `StoryContent` Pydantic model
3. **Final Event**: Send complete structured data with all fields

### Event Types

The streaming workflow emits the following SSE events:

```typescript
// Event types
type StreamEvent =
  | NodeEvent        // Workflow node progress (started/completed)
  | ContentChunk     // Story content chunks
  | SafetyCheck      // Content safety validation
  | Metadata         // Reading metrics
  | Complete         // Final complete story
  | Error            // Error events
```

#### Event Formats

**1. Node Event** (Workflow Progress)
```json
{
  "type": "node_event",
  "data": {
    "node": "generate_content",
    "status": "started|completed|failed",
    "chapter_number": 1,
    "theme": "adventure"
  }
}
```

**2. Content Chunk** (Story Text)
```json
{
  "type": "content",
  "data": {
    "chunk": "Once upon a time, in a magical forest...",
    "is_complete": false
  }
}
```

**3. Safety Check**
```json
{
  "type": "safety_check",
  "data": {
    "approved": true,
    "score": 0.95,
    "issues": []
  }
}
```

**4. Metadata**
```json
{
  "type": "metadata",
  "data": {
    "estimated_reading_time": 5,
    "vocabulary_level": "beginner",
    "educational_elements": ["Reading comprehension", "Decision making"]
  }
}
```

**5. Complete** (Final Result)
```json
{
  "type": "complete",
  "data": {
    "success": true,
    "story_content": "Full story text with formatting...",
    "choices": [
      {"text": "Go left", "description": ""},
      {"text": "Go right", "description": ""}
    ],
    "choice_question": "What should Luna do next?",
    "educational_elements": [...],
    "estimated_reading_time": 5,
    "safety_score": 0.95,
    "content_approved": true,
    "vocabulary_level": "beginner"
  }
}
```

**6. Error**
```json
{
  "type": "error",
  "data": {
    "message": "Story generation failed: ...",
    "code": "WORKFLOW_ERROR"
  }
}
```

## Implementation Details

### Workflow Streaming

The `generate_personalized_story_stream()` method:

```python
async def generate_personalized_story_stream(
    self,
    child: Child,
    theme: str,
    chapter_number: int = 1,
    story_session: Optional[StorySession] = None,
    custom_user_input: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Generate a personalized story with streaming support.

    Yields SSE-formatted events as the story is being generated.
    """
    # 1. Prepare state
    initial_state = StoryGenerationState(...)

    # 2. Stream events from workflow
    async for event in story_workflow.astream_events(
        initial_state,
        config={...},
        version="v2"  # Use v2 for better event streaming
    ):
        event_type = event.get("event")
        event_name = event.get("name", "")
        event_data = event.get("data", {})

        # 3. Handle different event types
        if event_type == "on_chain_start":
            # Node started
            yield format_node_event(...)

        elif event_type == "on_chain_end":
            # Node completed - extract state updates
            output = event_data.get("output", {})

            if "story_content" in output:
                # Stream content chunks
                paragraphs = content.split("\n\n")
                for para in paragraphs:
                    yield format_content_chunk(para)
                    await asyncio.sleep(0.05)  # Streaming effect

        elif event_type == "on_chat_model_stream":
            # Token-level streaming from LLM
            chunk = event_data.get("chunk")
            if chunk and hasattr(chunk, "content"):
                yield format_content_chunk(chunk.content)

    # 4. Send final complete event
    yield format_complete_event({...})
```

### API Endpoint

```python
@router.get("/generate/stream")
async def generate_story_stream(
    child_id: int = Query(...),
    theme: str = Query(...),
    chapter_number: int = Query(1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate a personalized story with SSE streaming."""

    return StreamingResponse(
        story_service.generate_personalized_story_stream(...),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Connection": "keep-alive",
        }
    )
```

## Client-Side Usage

### JavaScript/TypeScript Example

```typescript
// Using EventSource API
const eventSource = new EventSource(
  `/api/v1/stories/generate/stream?child_id=1&theme=adventure&chapter_number=1`,
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);

// Listen for story chunk events
eventSource.addEventListener('story_chunk', (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'node_event':
      console.log(`Node: ${data.data.node} - ${data.data.status}`);
      updateProgressIndicator(data.data);
      break;

    case 'content':
      console.log('Content chunk:', data.data.chunk);
      appendStoryContent(data.data.chunk);
      break;

    case 'safety_check':
      console.log('Safety check:', data.data);
      break;

    case 'metadata':
      console.log('Metadata:', data.data);
      updateMetadataDisplay(data.data);
      break;

    case 'complete':
      console.log('Story complete:', data.data);
      finalizeStoryDisplay(data.data);
      eventSource.close();
      break;

    case 'error':
      console.error('Error:', data.data.message);
      showError(data.data.message);
      eventSource.close();
      break;
  }
});

// Handle connection errors
eventSource.onerror = (error) => {
  console.error('EventSource error:', error);
  eventSource.close();
};
```

### React Example

```typescript
import { useEffect, useState } from 'react';

function useStoryStream(childId: number, theme: string, chapterNumber: number) {
  const [content, setContent] = useState<string>('');
  const [progress, setProgress] = useState<string>('');
  const [complete, setComplete] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const url = `/api/v1/stories/generate/stream?child_id=${childId}&theme=${theme}&chapter_number=${chapterNumber}`;
    const eventSource = new EventSource(url);

    eventSource.addEventListener('story_chunk', (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'node_event') {
        setProgress(`${data.data.node}: ${data.data.status}`);
      } else if (data.type === 'content') {
        setContent(prev => prev + data.data.chunk + '\n\n');
      } else if (data.type === 'complete') {
        setComplete(data.data);
        eventSource.close();
      } else if (data.type === 'error') {
        setError(data.data.message);
        eventSource.close();
      }
    });

    eventSource.onerror = () => {
      setError('Connection error');
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [childId, theme, chapterNumber]);

  return { content, progress, complete, error };
}
```

## Limitations and Trade-offs

### 1. Structured Output Streaming

**Limitation**: Cannot stream individual LLM tokens AND parse structured output simultaneously.

**Why**: `with_structured_output()` requires the complete LLM response to parse into the Pydantic model.

**Workaround**: We stream paragraph chunks after generation completes, providing a smooth UX while maintaining structured output.

### 2. Token-Level Streaming

**Limitation**: Token-by-token streaming is not available with `with_structured_output()`.

**Alternative**: The `on_chat_model_stream` events may provide token streaming for non-structured LLM calls (like safety enhancement).

**Current Approach**: We split completed content into paragraphs and stream with small delays to simulate real-time generation.

### 3. Structured Fields

**Limitation**: Structured fields (`choices`, `choice_question`, `educational_elements`) are only available in the final `complete` event.

**Why**: These fields are parsed from the complete LLM response.

**Workaround**: The frontend should handle progressive content display while waiting for the final structured data.

### 4. Error Recovery

**Limitation**: If the workflow fails mid-stream, the client may have partial content.

**Handling**: Always send an `error` event when failures occur. Clients should handle gracefully.

## Performance Considerations

1. **Streaming Overhead**: SSE has minimal overhead but requires long-lived connections
2. **Backpressure**: The async generator handles backpressure automatically
3. **Connection Limits**: Be mindful of concurrent SSE connections (browser typically limits to 6 per domain)
4. **LLM Generation Time**: The actual LLM generation is not accelerated; streaming just provides progress feedback

## Future Enhancements

### Possible Improvements

1. **True Token Streaming**: Implement a dual-mode system:
   - Stream raw tokens for immediate feedback
   - Parse structured output in parallel
   - Send both types of events

2. **Chunked Structured Parsing**: Parse partial structured fields as they become available (requires custom parsing logic)

3. **Progress Estimation**: Add estimated time remaining based on LLM generation speed

4. **Cancellation Support**: Allow clients to cancel in-progress generation

5. **Retry Mechanism**: Automatic retry on connection failures with resume capability

## Testing

### Manual Testing

```bash
# Test the streaming endpoint
curl -N \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/stories/generate/stream?child_id=1&theme=adventure&chapter_number=1"
```

### Integration Testing

```python
import pytest
from app.services.story_service import StoryService

@pytest.mark.asyncio
async def test_streaming_story_generation(db_session, child):
    """Test story generation streaming."""
    service = StoryService(db_session)

    events = []
    async for event in service.generate_personalized_story_stream(
        child=child,
        theme="adventure",
        chapter_number=1
    ):
        events.append(event)

    # Verify event sequence
    assert any("node_event" in e for e in events)
    assert any("content" in e for e in events)
    assert any("complete" in e for e in events)
```

## Monitoring and Debugging

### Logging

The implementation includes comprehensive logging:
- Workflow start/end events
- Node transitions
- Event streaming details
- Error traces

### LangSmith Integration

If `LANGSMITH_TRACING=true`, all workflow executions are traced in LangSmith with:
- Full workflow graph visualization
- Node execution times
- LLM prompts and responses
- Error details

## Conclusion

This streaming implementation provides a robust foundation for real-time story generation feedback while maintaining the benefits of structured output. The hybrid approach balances UX requirements (immediate feedback) with technical constraints (structured parsing).

The implementation is production-ready with proper error handling, logging, and monitoring support.
