"""
Terminal Endpoints
==================

REST API for terminal session management (create, destroy, list, check alive).
Works alongside the WebSocket endpoint for I/O streaming.
"""

from api.models import (
    TerminalAliveResponse,
    TerminalCreateRequest,
    TerminalCreateResponse,
    TerminalSession,
    TerminalSessionsResponse,
)
from api.websocket.terminal import get_terminal_manager
from fastapi import APIRouter, HTTPException, Response, status

router = APIRouter(prefix="/api/terminals", tags=["terminals"])


@router.post(
    "", response_model=TerminalCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_terminal(request: TerminalCreateRequest) -> TerminalCreateResponse:
    """
    Create a new terminal session.

    Returns session_id to use with WebSocket /ws/terminal/{session_id}
    """
    manager = get_terminal_manager()
    session_id = await manager.create_terminal(
        cwd=request.cwd or "/tmp",
        shell=request.shell or "/bin/bash",
        cols=request.cols,
        rows=request.rows,
    )
    return TerminalCreateResponse(session_id=session_id)


@router.delete("/{terminal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy_terminal(terminal_id: str) -> Response:
    """
    Destroy a terminal session and clean up resources.
    """
    manager = get_terminal_manager()
    destroyed = await manager.destroy(terminal_id)
    if not destroyed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Terminal not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sessions", response_model=TerminalSessionsResponse)
async def list_sessions() -> TerminalSessionsResponse:
    """
    List all active terminal sessions.
    """
    manager = get_terminal_manager()
    sessions_data = manager.list_sessions()
    sessions = [
        TerminalSession(id=s["id"], cwd=s["cwd"], alive=s["alive"])
        for s in sessions_data
    ]
    return TerminalSessionsResponse(sessions=sessions)


@router.get("/{terminal_id}/alive", response_model=TerminalAliveResponse)
async def check_alive(terminal_id: str) -> TerminalAliveResponse:
    """
    Check if a terminal session is still running.

    Returns alive=False for non-existent terminals (not 404) for client convenience.
    """
    manager = get_terminal_manager()
    alive = manager.is_alive(terminal_id)
    return TerminalAliveResponse(alive=alive)
