# Story Generation Streaming Implementation Guide

## Overview

This document describes the streaming implementation for the story generation API and provides guidance for the **langchain-langgraph-expert** agent to implement the LangGraph workflow streaming support.

## Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│  Frontend   │─────▶│  API Endpoint    │─────▶│  StoryService       │
│  (SSE)      │◀─────│  (FastAPI)       │◀─────│  (Async Generator)  │
└─────────────┘      └──────────────────┘      └─────────────────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────────┐
                                                 │  LangGraph Workflow │
                                                 │  (.astream_events) │
                                                 └─────────────────────┘
```

## Current Implementation Status

### ✅ Completed Components

1. **SSE Formatter Utilities** (`app/utils/sse_formatter.py`)
   - Server-Sent Events formatting functions
   - Event types: content, safety_check, metadata, complete, error, node_event
   - Proper SSE format with event types and data fields

2. **StoryService Streaming Method** (`app/services/story_service.py`)
   - `generate_personalized_story_stream()` async generator
   - Consumes LangGraph streaming events
   - Formats and yields SSE events
   - Handles errors gracefully

3. **API Streaming Endpoint** (`app/api/api_v1/endpoints/stories.py`)
   - `GET /api/v1/stories/generate/stream` endpoint
   - Returns `StreamingResponse` with `text/event-stream` media type
   - Proper headers for SSE (Cache-Control, Connection, X-Accel-Buffering)
   - Authentication and authorization checks

### 🔨 Required: LangGraph Workflow Streaming

**Status: NEEDS IMPLEMENTATION by langchain-langgraph-expert**

The workflow in `app/workflows/story_generation.py` currently uses `.invoke()` for synchronous execution. It needs to be modified to support streaming with `.astream_events()`.

## LangGraph Workflow Streaming Requirements

### Current Workflow Implementation

File: `backend/app/workflows/story_generation.py`

The workflow is a LangGraph StateGraph with these nodes:
- `generate_content` - Generates story using ChatOllama with structured output
- `safety_check` - Validates content safety
- `enhance_content` - Enhances content if needed
- `calculate_metrics` - Calculates reading time and formats content

### Required Changes for Streaming

The workflow needs to support the `.astream_events(version="v2")` API which provides:

1. **Event Types to Handle:**
   - `on_chain_start` - Node execution started
   - `on_chain_end` - Node execution completed
   - `on_chat_model_stream` - Token-level streaming from LLM
   - `on_llm_start` - LLM invocation started
   - `on_llm_end` - LLM invocation completed

2. **Key Modifications Needed:**

#### A. Make the Workflow Async-Compatible

The compiled workflow already supports `.astream_events()`, but the nodes need to be async or properly handle streaming:

```python
# Current: synchronous invoke
result = story_workflow.invoke(initial_state, config={...})

# Required: async streaming
async for event in story_workflow.astream_events(
    initial_state,
    config={...},
    version="v2"
):
    # Handle event
    pass
```

#### B. Enable LLM Streaming in generate_story_content()

The `ChatOllama` LLM needs to emit streaming events:

```python
def generate_story_content(state: StoryGenerationState) -> Dict[str, Any]:
    """Generate story content using Ollama with structured output."""

    # Initialize the base LLM with streaming enabled
    llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=settings.OLLAMA_TEMPERATURE,
        num_predict=settings.OLLAMA_MAX_TOKENS,
        streaming=True,  # ← ADD THIS
    )

    # Note: structured output with streaming may require special handling
    # You may need to use regular invoke for structured output,
    # or implement custom streaming with post-processing
```

#### C. Consider Structured Output vs Streaming Trade-offs

**Option 1: Keep Structured Output (Current Approach)**
- Uses `llm.with_structured_output(StoryContent)` which ensures valid JSON
- May not support token-level streaming
- Workflow can still emit node-level events

**Option 2: Implement Custom Streaming**
- Use regular LLM streaming
- Parse JSON incrementally or in post-processing
- Provides token-level streaming to frontend

**Recommendation:** Start with Option 1 (node-level streaming) for reliability, then enhance with Option 2 if token-level streaming is required.

### Example: Node-Level Streaming (Recommended First Step)

```python
# In story_service.py (already implemented)
async for event in story_workflow.astream_events(
    initial_state,
    config={...},
    version="v2"
):
    event_type = event.get("event")
    event_name = event.get("name", "")
    event_data = event.get("data", {})

    if event_type == "on_chain_start":
        if "generate_content" in event_name:
            yield format_node_event("generate_content", "started")

    elif event_type == "on_chain_end":
        output = event_data.get("output", {})
        if "generate_content" in event_name:
            if "story_content" in output:
                content = output["story_content"]
                # Stream content in chunks
                paragraphs = content.split("\n\n")
                for para in paragraphs:
                    yield format_content_chunk(para.strip())
            yield format_node_event("generate_content", "completed")
```

### Testing the Workflow Streaming

After implementing streaming support, test with:

```python
# Test script
import asyncio
from app.workflows.story_generation import story_workflow, StoryGenerationState

async def test_streaming():
    initial_state = StoryGenerationState(
        child_preferences={"age": 8, "reading_level": "intermediate"},
        story_theme="adventure",
        chapter_number=1,
        # ... other required fields
    )

    async for event in story_workflow.astream_events(
        initial_state,
        version="v2"
    ):
        print(f"Event: {event['event']} - {event.get('name', '')}")

asyncio.run(test_streaming())
```

## SSE Event Format Specification

### Event Types

#### 1. node_event
Emitted when workflow nodes start/complete:

```
event: story_chunk
data: {"type": "node_event", "data": {"node": "generate_content", "status": "started"}}

event: story_chunk
data: {"type": "node_event", "data": {"node": "generate_content", "status": "completed"}}
```

#### 2. content
Story content chunks:

```
event: story_chunk
data: {"type": "content", "data": {"chunk": "Once upon a time...", "is_complete": false}}
```

#### 3. safety_check
Content safety validation results:

```
event: story_chunk
data: {"type": "safety_check", "data": {"approved": true, "score": 1.0, "issues": []}}
```

#### 4. metadata
Reading metrics and metadata:

```
event: story_chunk
data: {"type": "metadata", "data": {"estimated_reading_time": 5, "vocabulary_level": "intermediate", "educational_elements": ["Problem solving", "Friendship"]}}
```

#### 5. complete
Final story with all data:

```
event: story_chunk
data: {"type": "complete", "data": {"success": true, "story_content": "...", "choices": [...], "choice_question": "...", ...}}
```

#### 6. error
Error events:

```
event: story_chunk
data: {"type": "error", "data": {"message": "Story generation failed", "code": "WORKFLOW_ERROR"}}
```

## Frontend Integration

### JavaScript/TypeScript Example

```typescript
const eventSource = new EventSource(
  `/api/v1/stories/generate/stream?child_id=123&theme=adventure&chapter_number=1`,
  { withCredentials: true }
);

eventSource.addEventListener('story_chunk', (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'node_event':
      console.log(`Node ${data.data.node} ${data.data.status}`);
      break;

    case 'content':
      appendStoryContent(data.data.chunk);
      break;

    case 'safety_check':
      if (!data.data.approved) {
        showWarning('Content safety issue detected');
      }
      break;

    case 'metadata':
      updateMetadata(data.data);
      break;

    case 'complete':
      handleComplete(data.data);
      eventSource.close();
      break;

    case 'error':
      handleError(data.data);
      eventSource.close();
      break;
  }
});

eventSource.onerror = (error) => {
  console.error('SSE Error:', error);
  eventSource.close();
};
```

## Error Handling

### Service Layer Error Handling

The `generate_personalized_story_stream()` method handles errors at multiple levels:

1. **Initialization errors** - Yield error event before starting stream
2. **Workflow streaming errors** - Catch and yield error event
3. **Event processing errors** - Log and continue (graceful degradation)

### API Layer Error Handling

The endpoint wraps the stream in a try-catch and:
- Returns proper HTTP status codes for auth/validation errors
- Returns error events in the stream for generation errors
- Logs all errors for debugging

### Frontend Error Handling

Frontend should:
- Listen for `error` type events in the SSE stream
- Handle `onerror` events from EventSource
- Implement timeout logic (e.g., 5 minutes max)
- Show user-friendly error messages

## Database Considerations for Streaming

### Current Approach
The streaming endpoint does **NOT** save to database during streaming. It only generates and streams content.

### Why?
- Streaming should be fast and not blocked by DB writes
- Complete story is saved after streaming completes (or in a separate endpoint call)
- Frontend receives the complete data in the `complete` event

### Alternative: Save During Streaming
If you need to save progress during streaming, consider:

1. **Batch writes** - Save after key nodes complete
2. **Background tasks** - Use FastAPI BackgroundTasks to save after response
3. **Separate save endpoint** - Frontend POSTs complete story to save

Example with BackgroundTasks:

```python
from fastapi import BackgroundTasks

async def save_story_to_db(story_data: dict, db: Session):
    """Background task to save story after streaming completes."""
    # Save story, chapters, choices to database
    pass

@router.get("/generate/stream")
async def generate_story_stream(
    ...,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Stream generation...

    # Add background task to save after streaming
    background_tasks.add_task(save_story_to_db, final_story_data, db)

    return StreamingResponse(...)
```

## Deployment Considerations

### NGINX Configuration

When deploying behind NGINX, ensure buffering is disabled for SSE:

```nginx
location /api/v1/stories/generate/stream {
    proxy_pass http://backend;
    proxy_buffering off;
    proxy_cache off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;
    proxy_read_timeout 5m;
}
```

### Docker Configuration

Ensure the Docker container has:
- Sufficient timeout settings
- No buffering in the reverse proxy layer

### LangSmith Tracing

The workflow already includes LangSmith tracing metadata. For streaming, events will appear in LangSmith with the proper tags and metadata:

```python
config={
    "metadata": {
        "child_id": child.id,
        "theme": theme,
        "chapter_number": chapter_number,
    },
    "tags": ["story_generation", f"chapter_{chapter_number}", theme]
}
```

## Performance Optimization

### Chunking Strategy

Current implementation streams content by paragraphs:
```python
paragraphs = content.split("\n\n")
for para in paragraphs:
    yield format_content_chunk(para.strip())
    await asyncio.sleep(0.05)  # Small delay for streaming effect
```

Adjust the delay based on:
- Network latency
- Frontend rendering performance
- User experience preferences

### Memory Management

The service accumulates state for the final event:
```python
final_state = {}  # Accumulates workflow output
```

For very long stories, consider:
- Streaming chunks without full accumulation
- Using Redis to cache intermediate state
- Implementing pagination for multi-chapter streaming

## Next Steps for langchain-langgraph-expert

1. **Review** the workflow in `app/workflows/story_generation.py`
2. **Implement** `.astream_events()` support in the workflow
3. **Test** streaming with the provided test script
4. **Verify** that all node events are properly emitted
5. **Document** any workflow-specific streaming considerations
6. **Optimize** token-level streaming if needed

## Support and References

- [LangGraph Streaming Documentation](https://langchain-ai.github.io/langgraph/how-tos/streaming/)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Server-Sent Events Spec](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [LangSmith Tracing](https://docs.smith.langchain.com/)

## Contact

For questions about:
- **API/Service Layer**: fullstack-developer agent
- **LangGraph/Workflow**: langchain-langgraph-expert agent
- **Frontend Integration**: frontend specialist
