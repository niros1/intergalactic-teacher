# Streaming API Quick Reference

## Endpoint

```
GET /api/v1/stories/generate/stream
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `child_id` | int | Yes | - | Child profile ID |
| `theme` | string | Yes | - | Story theme (e.g., "adventure") |
| `chapter_number` | int | No | 1 | Chapter to generate |
| `title` | string | No | null | Story title |

## Authentication

- Cookie-based session OR Bearer token
- Requires access to specified child profile

## Response

- **Media Type**: `text/event-stream`
- **Format**: Server-Sent Events (SSE)
- **Status**: 200 (success), 403 (forbidden), 404 (not found), 500 (error)

## Event Types

All events have this structure:
```
event: story_chunk
data: {"type": "<event_type>", "data": {...}}
```

### 1. node_event
Workflow progress:
```json
{"type": "node_event", "data": {"node": "generate_content", "status": "started"}}
{"type": "node_event", "data": {"node": "generate_content", "status": "completed"}}
```

### 2. content
Story text chunks:
```json
{"type": "content", "data": {"chunk": "Once upon a time...", "is_complete": false}}
```

### 3. safety_check
Safety validation:
```json
{"type": "safety_check", "data": {"approved": true, "score": 1.0, "issues": []}}
```

### 4. metadata
Reading metrics:
```json
{"type": "metadata", "data": {
  "estimated_reading_time": 5,
  "vocabulary_level": "intermediate",
  "educational_elements": ["Problem solving", "Friendship"]
}}
```

### 5. complete
Final story (last event):
```json
{"type": "complete", "data": {
  "success": true,
  "story_content": "Full story text...",
  "choices": [{"text": "Choice 1"}, {"text": "Choice 2"}],
  "choice_question": "What should they do next?",
  "educational_elements": ["..."],
  "estimated_reading_time": 5,
  "safety_score": 1.0,
  "vocabulary_level": "intermediate"
}}
```

### 6. error
Error events:
```json
{"type": "error", "data": {"message": "Error message", "code": "ERROR_CODE"}}
```

## Example: curl

```bash
curl -N -H "Accept: text/event-stream" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/stories/generate/stream?child_id=1&theme=adventure&chapter_number=1"
```

## Example: JavaScript (EventSource)

```javascript
const source = new EventSource(
  '/api/v1/stories/generate/stream?child_id=1&theme=adventure',
  { withCredentials: true }
);

source.addEventListener('story_chunk', (e) => {
  const {type, data} = JSON.parse(e.data);

  switch(type) {
    case 'content':
      displayContent(data.chunk);
      break;
    case 'safety_check':
      if (!data.approved) showWarning();
      break;
    case 'complete':
      finishStory(data);
      source.close();
      break;
    case 'error':
      handleError(data);
      source.close();
      break;
  }
});

source.onerror = () => source.close();
```

## Example: JavaScript (fetch + ReadableStream)

```javascript
const response = await fetch(
  '/api/v1/stories/generate/stream?child_id=1&theme=adventure',
  { credentials: 'include' }
);

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const {done, value} = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  processSSEChunk(chunk);
}
```

## Example: Python (httpx)

```python
import httpx
import json

async with httpx.AsyncClient() as client:
    async with client.stream(
        "GET",
        "http://localhost:8000/api/v1/stories/generate/stream",
        params={"child_id": 1, "theme": "adventure"},
        headers={"Authorization": "Bearer YOUR_TOKEN"},
        timeout=300.0
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                print(f"{data['type']}: {data['data']}")
```

## Typical Event Flow

```
1. node_event: workflow started
2. node_event: generate_content started
3. content: Story chunk 1
4. content: Story chunk 2
5. content: Story chunk 3
6. node_event: generate_content completed
7. node_event: safety_check started
8. safety_check: Validation results
9. node_event: safety_check completed
10. node_event: calculate_metrics started
11. metadata: Reading metrics
12. node_event: calculate_metrics completed
13. complete: Final story with all data
```

## Error Handling

- **Auth errors (403, 404)**: HTTP response with error details
- **Generation errors**: `error` event in stream
- **Network errors**: EventSource `onerror` event
- **Timeout**: Implement client-side timeout (5-10 minutes)

## Performance

- **TTFB**: < 500ms
- **Total time**: 30-60 seconds (depends on LLM)
- **Events/second**: 10-20 during generation
- **Max concurrent**: 5-10 streams (depends on resources)

## Deployment Notes

### NGINX Configuration
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

### Docker
No buffering at any layer. Set timeouts to 5-10 minutes.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No events received | Check CORS, buffering, authentication |
| Events delayed | Disable proxy buffering (NGINX, Docker) |
| Stream timeout | Increase proxy/server timeouts |
| Connection closed early | Check for network issues, implement retry |
| Malformed events | Verify SSE format (event:, data:, blank lines) |

## File Locations

- **API Endpoint**: `backend/app/api/api_v1/endpoints/stories.py`
- **Service Layer**: `backend/app/services/story_service.py`
- **SSE Formatters**: `backend/app/utils/sse_formatter.py`
- **Workflow**: `backend/app/workflows/story_generation.py`

## Documentation

- **Full Guide**: `STREAMING_IMPLEMENTATION_GUIDE.md`
- **Complete Summary**: `STREAMING_SUMMARY.md`
- **Implementation Status**: `STREAMING_COMPLETE.md`
- **This Reference**: `STREAMING_QUICK_REFERENCE.md`

---

**Quick Start**:
1. Rebuild: `docker-compose up --build -d api`
2. Test: `curl -N -H "Accept: text/event-stream" "http://localhost:8000/api/v1/stories/generate/stream?child_id=1&theme=adventure"`
