"""Server-Sent Events (SSE) formatting utilities for streaming responses."""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def format_sse_event(
    data: Dict[str, Any],
    event_type: Optional[str] = None,
    event_id: Optional[str] = None,
    retry: Optional[int] = None
) -> str:
    """
    Format data as a Server-Sent Event (SSE).

    Args:
        data: The data to send (will be JSON serialized)
        event_type: Optional event type (defaults to "message")
        event_id: Optional event ID for client tracking
        retry: Optional retry time in milliseconds

    Returns:
        Formatted SSE string with proper line endings

    SSE Format:
        event: <event_type>
        id: <event_id>
        retry: <retry_ms>
        data: <json_data>

        (blank line to signal end of event)
    """
    sse_lines = []

    # Add event type if specified
    if event_type:
        sse_lines.append(f"event: {event_type}")

    # Add event ID if specified
    if event_id:
        sse_lines.append(f"id: {event_id}")

    # Add retry time if specified
    if retry:
        sse_lines.append(f"retry: {retry}")

    # Add data (JSON serialized)
    json_data = json.dumps(data, ensure_ascii=False)
    sse_lines.append(f"data: {json_data}")

    # Add blank line to signal end of event
    sse_lines.append("")
    sse_lines.append("")

    return "\n".join(sse_lines)


def format_story_chunk_event(chunk_type: str, data: Any, event_id: Optional[str] = None) -> str:
    """
    Format a story generation chunk event.

    Args:
        chunk_type: Type of chunk (content, safety_check, metadata, complete, error)
        data: The chunk data
        event_id: Optional event ID

    Returns:
        Formatted SSE event
    """
    event_data = {
        "type": chunk_type,
        "data": data
    }

    return format_sse_event(
        data=event_data,
        event_type="story_chunk",
        event_id=event_id
    )


def format_content_chunk(text: str, is_complete: bool = False) -> str:
    """Format a content text chunk."""
    return format_story_chunk_event(
        chunk_type="content",
        data={
            "chunk": text,
            "is_complete": is_complete
        }
    )


def format_node_event(node_name: str, status: str, data: Optional[Dict] = None) -> str:
    """
    Format a workflow node event.

    Args:
        node_name: Name of the workflow node
        status: Status (started, completed, failed)
        data: Optional additional data
    """
    event_data = {
        "node": node_name,
        "status": status
    }

    if data:
        event_data.update(data)

    return format_story_chunk_event(
        chunk_type="node_event",
        data=event_data
    )


def format_safety_check_event(approved: bool, score: float, issues: list = None) -> str:
    """Format a content safety check event."""
    return format_story_chunk_event(
        chunk_type="safety_check",
        data={
            "approved": approved,
            "score": score,
            "issues": issues or []
        }
    )


def format_metadata_event(
    estimated_reading_time: int,
    vocabulary_level: str,
    educational_elements: list
) -> str:
    """Format a metadata event."""
    return format_story_chunk_event(
        chunk_type="metadata",
        data={
            "estimated_reading_time": estimated_reading_time,
            "vocabulary_level": vocabulary_level,
            "educational_elements": educational_elements
        }
    )


def format_complete_event(story_data: Dict[str, Any]) -> str:
    """
    Format the final completion event with full story data.

    Args:
        story_data: Complete story object with all metadata
    """
    return format_story_chunk_event(
        chunk_type="complete",
        data=story_data
    )


def format_error_event(error_message: str, error_code: Optional[str] = None) -> str:
    """Format an error event."""
    error_data = {"message": error_message}

    if error_code:
        error_data["code"] = error_code

    return format_story_chunk_event(
        chunk_type="error",
        data=error_data
    )


def format_heartbeat_event() -> str:
    """
    Format a heartbeat/keepalive event to prevent connection timeout.

    Returns a comment line which is valid SSE but doesn't trigger events.
    """
    return ": heartbeat\n\n"
