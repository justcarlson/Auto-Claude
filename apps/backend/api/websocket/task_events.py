"""
Task Events WebSocket Handler
=============================

WebSocket endpoint that streams real-time task events:
- progress: Task progress updates
- status: Task status changes
- error: Task errors
- log: Task log output
"""

import asyncio
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect

# Track connected clients per task_id
# task_id -> set of WebSocket connections
_task_clients: dict[str, set[WebSocket]] = defaultdict(set)

# Lock for thread-safe client management
_client_lock = asyncio.Lock()


async def task_events_websocket(websocket: WebSocket, task_id: str):
    """
    WebSocket handler for task event streaming.

    Protocol:
    - On connect: Sends {"type": "connected", "taskId": "..."}
    - Events streamed as {"type": "...", "taskId": "...", ...}
    - Event types: progress, status, error, log

    Args:
        websocket: The WebSocket connection
        task_id: ID of the task to subscribe to
    """
    await websocket.accept()

    # Register client
    async with _client_lock:
        _task_clients[task_id].add(websocket)

    try:
        # Send connected message
        await websocket.send_json(
            {
                "type": "connected",
                "taskId": task_id,
            }
        )

        # Keep connection alive until disconnect
        while True:
            try:
                # Wait for any message (ping/pong, etc.)
                data = await websocket.receive_text()
                # Echo pong for ping
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break

    finally:
        # Unregister client
        async with _client_lock:
            _task_clients[task_id].discard(websocket)
            # Cleanup empty sets
            if not _task_clients[task_id]:
                del _task_clients[task_id]


def emit_progress(task_id: str, data: dict) -> None:
    """
    Emit a progress event to all connected clients for a task.

    Args:
        task_id: Task ID
        data: Progress data (e.g., {"phase": "building", "percent": 50})
    """
    _emit_event(
        task_id,
        {
            "type": "progress",
            "taskId": task_id,
            "data": data,
        },
    )


def emit_status(task_id: str, status: str) -> None:
    """
    Emit a status change event to all connected clients.

    Args:
        task_id: Task ID
        status: New status value
    """
    _emit_event(
        task_id,
        {
            "type": "status",
            "taskId": task_id,
            "status": status,
        },
    )


def emit_error(task_id: str, error: str) -> None:
    """
    Emit an error event to all connected clients.

    Args:
        task_id: Task ID
        error: Error message
    """
    _emit_event(
        task_id,
        {
            "type": "error",
            "taskId": task_id,
            "error": error,
        },
    )


def emit_log(task_id: str, level: str, message: str) -> None:
    """
    Emit a log event to all connected clients.

    Args:
        task_id: Task ID
        level: Log level (info, warn, error, debug)
        message: Log message
    """
    _emit_event(
        task_id,
        {
            "type": "log",
            "taskId": task_id,
            "level": level,
            "message": message,
        },
    )


def _emit_event(task_id: str, event: dict) -> None:
    """
    Emit an event to all connected clients for a task.

    Handles sending synchronously for tests (no running event loop).
    """
    clients = _task_clients.get(task_id, set())
    if not clients:
        return

    try:
        loop = asyncio.get_running_loop()
        # Schedule sends in the event loop
        for client in clients:
            loop.create_task(_safe_send(client, event))
    except RuntimeError:
        # No running event loop (sync context like tests)
        # Use run_until_complete for each send
        for client in clients:
            try:
                # Create a new loop for sync sending
                loop = asyncio.new_event_loop()
                loop.run_until_complete(client.send_json(event))
                loop.close()
            except Exception:
                pass  # Client may have disconnected


async def _safe_send(client: WebSocket, event: dict) -> None:
    """Safely send an event, ignoring disconnected clients."""
    try:
        await client.send_json(event)
    except Exception:
        pass  # Client disconnected


def reset_task_clients() -> None:
    """Reset all task clients (for testing)."""
    global _task_clients
    _task_clients = defaultdict(set)
