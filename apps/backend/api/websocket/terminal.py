"""
Terminal WebSocket Handler
==========================

WebSocket endpoint that bridges browser connections to PTY sessions.
Manages terminal lifecycle: create on connect, destroy on disconnect.
"""

import asyncio
import json

from api.services.terminal_service import TerminalManager
from fastapi import WebSocket, WebSocketDisconnect

# Singleton terminal manager for all WebSocket connections
_terminal_manager: TerminalManager | None = None


def get_terminal_manager() -> TerminalManager:
    """Get or create the singleton TerminalManager."""
    global _terminal_manager
    if _terminal_manager is None:
        _terminal_manager = TerminalManager()
    return _terminal_manager


def reset_terminal_manager() -> None:
    """Reset the terminal manager (for testing)."""
    global _terminal_manager
    if _terminal_manager is not None:
        # Destroy all terminals synchronously in a new event loop if needed
        try:
            loop = asyncio.get_running_loop()
            # Schedule cleanup
            loop.create_task(_terminal_manager.destroy_all())
        except RuntimeError:
            # No running loop, create one
            asyncio.run(_terminal_manager.destroy_all())
    _terminal_manager = None


async def terminal_websocket(websocket: WebSocket, terminal_id: str):
    """
    WebSocket handler for terminal connections.

    Protocol:
    - On connect: Creates PTY, sends {"type": "connected", "terminal_id": "..."}
    - On receive {"type": "input", "data": "..."}: Writes to PTY
    - On receive {"type": "resize", "cols": N, "rows": N}: Resizes PTY
    - On disconnect: Destroys PTY

    Streams PTY output as {"type": "output", "data": "..."} messages.
    """
    await websocket.accept()

    manager = get_terminal_manager()
    internal_terminal_id: str | None = None

    try:
        # Create terminal for this connection
        internal_terminal_id = await manager.create_terminal(
            cwd="/tmp",
            shell="/bin/bash",
            cols=80,
            rows=24,
        )

        # Send connected message with the user-provided terminal_id
        await websocket.send_json(
            {
                "type": "connected",
                "terminal_id": terminal_id,
            }
        )

        # Start output streaming task
        output_task = asyncio.create_task(
            _stream_output(websocket, manager, internal_terminal_id)
        )

        try:
            # Handle incoming messages
            while True:
                try:
                    data = await websocket.receive_text()
                    await _handle_message(
                        websocket, manager, internal_terminal_id, data
                    )
                except WebSocketDisconnect:
                    break
        finally:
            output_task.cancel()
            try:
                await output_task
            except asyncio.CancelledError:
                pass  # Expected when client disconnects - task cleanup is intentional

    finally:
        # Cleanup terminal on disconnect
        if internal_terminal_id:
            await manager.destroy(internal_terminal_id)


async def _stream_output(
    websocket: WebSocket,
    manager: TerminalManager,
    terminal_id: str,
) -> None:
    """
    Continuously stream PTY output to WebSocket.

    Runs until cancelled or terminal dies.
    """
    while True:
        try:
            if not manager.is_alive(terminal_id):
                break

            # Read with short timeout to stay responsive
            async for chunk in manager.read(terminal_id, timeout=0.5):
                await websocket.send_json(
                    {
                        "type": "output",
                        "data": chunk,
                    }
                )

            # Small delay between read cycles
            await asyncio.sleep(0.05)

        except KeyError:
            # Terminal was destroyed
            break
        except Exception:
            # Connection closed or other error
            break


async def _handle_message(
    websocket: WebSocket,
    manager: TerminalManager,
    terminal_id: str,
    raw_data: str,
) -> None:
    """
    Handle incoming WebSocket message.

    Args:
        websocket: The WebSocket connection
        manager: TerminalManager instance
        terminal_id: Internal terminal ID
        raw_data: Raw message string (should be JSON)
    """
    try:
        message = json.loads(raw_data)
    except json.JSONDecodeError as e:
        await websocket.send_json(
            {
                "type": "error",
                "data": f"Invalid JSON: {e}",
            }
        )
        return

    msg_type = message.get("type")

    if msg_type == "input":
        # Write input to PTY
        data = message.get("data", "")
        if data:
            try:
                await manager.write(terminal_id, data)
            except KeyError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "data": "Terminal not found",
                    }
                )

    elif msg_type == "resize":
        # Resize PTY
        cols = message.get("cols", 80)
        rows = message.get("rows", 24)
        try:
            await manager.resize(terminal_id, rows, cols)
        except KeyError:
            await websocket.send_json(
                {
                    "type": "error",
                    "data": "Terminal not found",
                }
            )

    elif msg_type == "ping":
        # Respond to ping with pong
        await websocket.send_json({"type": "pong"})

    else:
        # Unknown message type - ignore but don't error
        # This allows forward compatibility with new message types
        pass
