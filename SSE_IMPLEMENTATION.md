# SSE (Server-Sent Events) Implementation for Story Streaming

## Overview

This document describes the SSE implementation for real-time story generation streaming in the Intergalactic Teacher application. The implementation provides a ChatGPT-like streaming experience where story content appears token-by-token or chunk-by-chunk as it's being generated.

## Architecture

### Backend Components

#### 1. SSE Endpoint
**File**: `/backend/app/api/api_v1/endpoints/stories.py`

New streaming endpoint:
```python
@router.get("/generate/stream")
async def generate_story_stream(
    child_id: int,
    theme: str,
    chapter_number: int = 1,
    title: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> StreamingResponse
```

**Features**:
- Accepts query parameters instead of request body (EventSource limitation)
- Returns `StreamingResponse` with `text/event-stream` content type
- Includes proper headers to disable buffering
- Handles authentication and child access control

#### 2. Streaming Service Method
**File**: `/backend/app/services/story_service.py`

New async generator method:
```python
async def generate_personalized_story_stream(
    self,
    child: Child,
    theme: str,
    chapter_number: int = 1,
    story_session: Optional[StorySession] = None,
    custom_user_input: Optional[str] = None
) -> AsyncGenerator[str, None]
```

**Events emitted**:
1. `node` - Workflow node progress (generate_content, safety_check, etc.)
2. `content` - Story content chunks
3. `safety_check` - Safety validation results
4. `metadata` - Reading time, vocabulary level, educational elements
5. `complete` - Final story with all data
6. `error` - Error information

#### 3. SSE Formatter Utilities
**File**: `/backend/app/utils/sse_formatter.py` (needs to be created)

Helper functions for formatting SSE events:
```python
def format_sse_event(event_type: str, data: Dict[str, Any]) -> str
def format_content_chunk(chunk: str) -> str
def format_progress_event(stage: str, description: str) -> str
def format_safety_check_event(status: str, score: float) -> str
def format_metadata_event(metadata: Dict[str, Any]) -> str
def format_complete_event(story: Dict[str, Any]) -> str
def format_error_event(message: str) -> str
def format_node_event(node_name: str, status: str) -> str
```

### Frontend Components

#### 1. SSE Hook
**File**: `/frontend/src/hooks/useSSEStoryGeneration.tsx`

React hook for SSE client:
```typescript
export const useSSEStoryGeneration = (options?: SSEOptions): UseSSEStoryGenerationResult
```

**Features**:
- Manages EventSource connection lifecycle
- Parses and handles different event types
- Provides callbacks for content, progress, safety check, completion, and errors
- Automatically cleans up on unmount
- Supports reconnection handling

**Usage**:
```typescript
const {
  isStreaming,
  streamedContent,
  currentProgress,
  error,
  startStreaming,
  stopStreaming,
  resetStream
} = useSSEStoryGeneration({
  onContent: (chunk) => console.log('New chunk:', chunk),
  onProgress: (stage, desc) => console.log('Progress:', stage, desc),
  onComplete: (story) => console.log('Complete:', story),
  onError: (err) => console.error('Error:', err)
})
```

#### 2. Enhanced Story Store
**File**: `/frontend/src/stores/storyStore.ts`

Added streaming state and methods:
```typescript
interface StreamingState {
  isStreaming: boolean
  streamedContent: string
  streamProgress: string | null
}

// New methods:
generateStoryStreaming(request, onChunk?)
updateStreamingContent(content)
updateStreamingProgress(progress)
setIsStreaming(isStreaming)
```

**Features**:
- Manages streaming state
- Uses fetch API with ReadableStream for better control than EventSource
- Accumulates content chunks
- Updates progress in real-time
- Builds final story object from streamed data

#### 3. Runtime Hook Integration
**File**: `/frontend/src/hooks/useStoryRuntime.tsx`

To be updated to:
- Display streaming content as it arrives
- Show progress indicators
- Handle streaming state transitions
- Update messages in real-time

#### 4. UI Components
**File**: `/frontend/src/pages/reading/ChatReadingPage.tsx`

To be enhanced with:
- Streaming indicators (animated dots, progress bar)
- Real-time content display
- Progress messages
- Smooth animations for incoming content

## Event Flow

### 1. Story Generation Request

```
User clicks "Generate Story"
   ↓
Frontend calls generateStoryStreaming()
   ↓
HTTP GET /api/v1/stories/generate/stream?child_id=X&theme=adventure&chapter_number=1
   ↓
Backend authenticates and validates
   ↓
StreamingResponse starts
```

### 2. Content Streaming

```
Backend workflow starts
   ↓
Event: {type: "node", node: "workflow", status: "started"}
   ↓
Event: {type: "node", node: "generate_content", status: "started"}
   ↓
Event: {type: "content", chunk: "Once upon a time..."}
Event: {type: "content", chunk: "in a magical forest..."}
Event: {type: "content", chunk: "there lived a brave..."}
   ↓
Event: {type: "node", node: "generate_content", status: "completed"}
   ↓
Event: {type: "node", node: "safety_check", status: "started"}
   ↓
Event: {type: "safety_check", status: "approved", score: 1.0}
   ↓
Event: {type: "node", node: "safety_check", status: "completed"}
   ↓
Event: {type: "metadata", estimated_reading_time: 5, vocabulary_level: "beginner"}
   ↓
Event: {type: "complete", story: {...full story object...}}
   ↓
Connection closes
```

### 3. Frontend Processing

```
Fetch starts streaming
   ↓
Read chunks from ReadableStream
   ↓
Parse SSE messages (data: {...})
   ↓
Handle each event type:
  - progress → Update progress display
  - content → Append to accumulated content
  - safety_check → Show safety status
  - complete → Build final story object
  - error → Show error message
   ↓
Update UI in real-time
   ↓
On complete: Update store with final story
```

## SSE Message Format

All events follow this structure:
```
data: {"type": "event_type", ...event_data}

```

**Note**: SSE messages must end with double newline (`\n\n`)

### Event Types

#### 1. Progress Event
```json
data: {
  "type": "progress",
  "progress": {
    "stage": "generate_content",
    "description": "Generating story content..."
  }
}
```

#### 2. Content Event
```json
data: {
  "type": "content",
  "chunk": "Once upon a time in a magical forest..."
}
```

#### 3. Safety Check Event
```json
data: {
  "type": "safety_check",
  "status": "approved",
  "score": 1.0
}
```

#### 4. Metadata Event
```json
data: {
  "type": "metadata",
  "estimated_reading_time": 5,
  "vocabulary_level": "beginner",
  "educational_elements": ["Reading comprehension", "Decision making"]
}
```

#### 5. Complete Event
```json
data: {
  "type": "complete",
  "story": {
    "success": true,
    "story_content": "...",
    "choices": [...],
    "choice_question": "...",
    "educational_elements": [...],
    "estimated_reading_time": 5,
    "safety_score": 1.0,
    "content_approved": true,
    "vocabulary_level": "beginner"
  }
}
```

#### 6. Error Event
```json
data: {
  "type": "error",
  "message": "Story generation failed",
  "error_code": "WORKFLOW_ERROR"
}
```

## Usage Examples

### Basic Streaming

```typescript
import { useStoryStore } from '../stores/storyStore';

function StoryGenerator() {
  const { generateStoryStreaming, streamingState } = useStoryStore();

  const handleGenerate = async () => {
    try {
      const story = await generateStoryStreaming({
        childId: '123',
        theme: 'adventure',
        chapter_number: 1,
        title: 'The Magic Forest'
      });
      console.log('Story complete:', story);
    } catch (error) {
      console.error('Generation failed:', error);
    }
  };

  return (
    <div>
      {streamingState.isStreaming && (
        <div>
          <p>{streamingState.streamProgress}</p>
          <div>{streamingState.streamedContent}</div>
        </div>
      )}
      <button onClick={handleGenerate}>Generate Story</button>
    </div>
  );
}
```

### With Callbacks

```typescript
const { generateStoryStreaming } = useStoryStore();

await generateStoryStreaming(
  {
    childId: '123',
    theme: 'adventure',
    chapter_number: 1
  },
  (chunk) => {
    // Handle each content chunk as it arrives
    console.log('New chunk:', chunk);
    // Could trigger animations, sound effects, etc.
  }
);
```

### Using the SSE Hook Directly

```typescript
import { useSSEStoryGeneration } from '../hooks/useSSEStoryGeneration';

function CustomStreaming() {
  const {
    isStreaming,
    streamedContent,
    currentProgress,
    error,
    startStreaming
  } = useSSEStoryGeneration({
    onContent: (chunk) => {
      console.log('Content:', chunk);
    },
    onProgress: (stage, description) => {
      console.log('Progress:', stage, description);
    },
    onComplete: (story) => {
      console.log('Complete:', story);
    },
    onError: (error) => {
      console.error('Error:', error);
    }
  });

  const handleStart = () => {
    startStreaming('/api/v1/stories/generate/stream', {
      child_id: '123',
      theme: 'adventure',
      chapter_number: 1
    });
  };

  return (
    <div>
      {currentProgress && <p>{currentProgress}</p>}
      {streamedContent && <div>{streamedContent}</div>}
      {error && <p>Error: {error}</p>}
      <button onClick={handleStart} disabled={isStreaming}>
        {isStreaming ? 'Generating...' : 'Generate'}
      </button>
    </div>
  );
}
```

## Testing

### Backend Testing

```python
import httpx

async def test_story_streaming():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            'GET',
            'http://localhost:8000/api/v1/stories/generate/stream',
            params={
                'child_id': 1,
                'theme': 'adventure',
                'chapter_number': 1
            },
            headers={'Authorization': 'Bearer YOUR_TOKEN'}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    event = json.loads(line[6:])
                    print(f"Event: {event['type']}")
```

### Frontend Testing

```typescript
// Test in browser console
const eventSource = new EventSource(
  '/api/v1/stories/generate/stream?child_id=1&theme=adventure&chapter_number=1&token=YOUR_TOKEN'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data);
};

eventSource.onerror = (error) => {
  console.error('SSE Error:', error);
  eventSource.close();
};
```

## Error Handling

### Backend
- Connection errors: Emit error event and close stream
- Workflow errors: Emit error event with details
- Validation errors: Return HTTP error before streaming starts
- Timeout handling: Implement timeouts for long-running generations

### Frontend
- Connection failures: Retry with exponential backoff
- Parse errors: Log and skip malformed events
- Network errors: Show user-friendly error message
- Timeout: Cancel stream after configurable duration

## Performance Considerations

1. **Chunk Size**: Balance between responsiveness and overhead
   - Too small: Many events, high overhead
   - Too large: Less responsive feeling
   - Recommended: Paragraph-level chunks (50-200 words)

2. **Buffering**: Disable server-side buffering
   - Set `X-Accel-Buffering: no` header
   - Configure nginx/proxy appropriately

3. **Connection Limits**: Browsers limit concurrent SSE connections
   - Maximum 6 per domain (HTTP/1.1)
   - Use HTTP/2 for better performance

4. **Memory Management**: Clean up accumulated content
   - Limit stored chunks
   - Clear on unmount/completion

## Security

1. **Authentication**: Token-based auth via query parameter
   - Alternative: Use cookie-based auth
   - Consider implementing connection validation

2. **Rate Limiting**: Prevent abuse
   - Limit concurrent streams per user
   - Implement request throttling

3. **Input Validation**: Sanitize all inputs
   - Validate child_id ownership
   - Validate theme and parameters

## Future Enhancements

1. **Token-level Streaming**: Stream individual tokens from LLM
2. **Progress Percentage**: Add numeric progress (0-100%)
3. **Pause/Resume**: Allow pausing and resuming generation
4. **Reconnection**: Auto-reconnect on connection loss
5. **Compression**: Implement SSE compression for bandwidth savings
6. **Caching**: Cache partial results for retry scenarios
7. **Analytics**: Track streaming metrics (time to first chunk, etc.)

## Troubleshooting

### Issue: Events not received
- Check CORS configuration
- Verify Content-Type is `text/event-stream`
- Check for proxy buffering
- Validate SSE format (double newlines)

### Issue: Slow streaming
- Check chunk size
- Verify no buffering at proxy level
- Check network latency
- Profile LLM generation time

### Issue: Connection drops
- Implement heartbeat/keep-alive
- Check timeout configurations
- Handle network transitions
- Implement retry logic

## Files Modified/Created

### Backend
- ✅ `/backend/app/api/api_v1/endpoints/stories.py` - Added SSE endpoint
- ✅ `/backend/app/services/story_service.py` - Added streaming method
- ⏳ `/backend/app/utils/sse_formatter.py` - SSE formatting utilities (needs creation)

### Frontend
- ✅ `/frontend/src/hooks/useSSEStoryGeneration.tsx` - SSE client hook
- ✅ `/frontend/src/stores/storyStore.ts` - Enhanced with streaming state
- ⏳ `/frontend/src/hooks/useStoryRuntime.tsx` - Needs streaming integration
- ⏳ `/frontend/src/pages/reading/ChatReadingPage.tsx` - Needs UI indicators

## Next Steps

1. ⏳ Create `/backend/app/utils/sse_formatter.py` with formatting utilities
2. ⏳ Update `useStoryRuntime` to handle streaming content
3. ⏳ Add UI streaming indicators to ChatReadingPage
4. ⏳ Test end-to-end flow
5. ⏳ Add error handling and retry logic
6. ⏳ Implement progress animations
7. ⏳ Add unit and integration tests
8. ⏳ Deploy and monitor performance

## Deployment Notes

### Docker
Update docker-compose.yml if needed:
```yaml
api:
  environment:
    - STREAMING_ENABLED=true
    - MAX_STREAMING_CONNECTIONS=100
```

### Environment Variables
```bash
# Backend
STREAMING_ENABLED=true
STREAMING_TIMEOUT=300  # seconds
STREAMING_CHUNK_SIZE=200  # words

# Frontend
VITE_STREAMING_ENABLED=true
VITE_STREAMING_RETRY_ATTEMPTS=3
```

## Support

For issues or questions:
1. Check server logs for backend errors
2. Check browser console for frontend errors
3. Verify network tab shows event-stream connection
4. Test with simple curl/httpx request first

---

**Implementation Status**: 60% Complete

**Last Updated**: 2025-10-09

**Contributors**: Frontend Developer Agent
