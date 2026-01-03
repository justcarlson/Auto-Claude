#!/usr/bin/env python3
"""
Terminal Endpoints Tests
========================

TDD tests for the /api/terminals endpoints.
Tests written BEFORE implementation to drive development.
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def isolated_terminals():
    """Ensure each test uses isolated terminal manager."""
    from api.websocket.terminal import reset_terminal_manager

    # Reset terminal manager for fresh state
    reset_terminal_manager()

    yield

    # Cleanup after test
    reset_terminal_manager()


# =============================================================================
# POST /api/terminals - Create Terminal
# =============================================================================


@pytest.mark.asyncio
async def test_create_terminal_returns_session_id():
    """
    Given: Valid terminal creation request
    Should: Return 201 with session_id
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/terminals",
            json={"cwd": "/tmp", "cols": 80, "rows": 24},
        )

    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert isinstance(data["session_id"], str)
    assert len(data["session_id"]) > 0


@pytest.mark.asyncio
async def test_create_terminal_with_defaults():
    """
    Given: Terminal creation request without optional fields
    Should: Use defaults and return 201
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/terminals", json={})

    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data


@pytest.mark.asyncio
async def test_create_terminal_with_shell():
    """
    Given: Terminal creation request with custom shell
    Should: Accept shell parameter and return 201
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/terminals",
            json={"shell": "/bin/bash"},
        )

    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data


# =============================================================================
# DELETE /api/terminals/{id} - Destroy Terminal
# =============================================================================


@pytest.mark.asyncio
async def test_destroy_terminal_cleans_up():
    """
    Given: Existing terminal session
    When: DELETE request sent
    Should: Return 204 and clean up resources
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # First create a terminal
        create_response = await client.post("/api/terminals", json={})
        assert create_response.status_code == 201
        session_id = create_response.json()["session_id"]

        # Then destroy it
        response = await client.delete(f"/api/terminals/{session_id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_destroy_terminal_not_found():
    """
    Given: Non-existent terminal ID
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/api/terminals/nonexistent-id")

    assert response.status_code == 404


# =============================================================================
# GET /api/terminals/sessions - List Sessions
# =============================================================================


@pytest.mark.asyncio
async def test_list_sessions_empty():
    """
    Given: No active terminals
    Should: Return empty list
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/terminals/sessions")

    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)
    assert len(data["sessions"]) == 0


@pytest.mark.asyncio
async def test_list_sessions_with_terminals():
    """
    Given: Multiple active terminals
    Should: Return list of all session IDs
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create two terminals
        resp1 = await client.post("/api/terminals", json={})
        resp2 = await client.post("/api/terminals", json={})
        session_id1 = resp1.json()["session_id"]
        session_id2 = resp2.json()["session_id"]

        # List sessions
        response = await client.get("/api/terminals/sessions")

    assert response.status_code == 200
    data = response.json()
    assert len(data["sessions"]) == 2
    session_ids = [s["id"] for s in data["sessions"]]
    assert session_id1 in session_ids
    assert session_id2 in session_ids


# =============================================================================
# GET /api/terminals/{id}/alive - Check Alive Status
# =============================================================================


@pytest.mark.asyncio
async def test_check_alive_returns_status_true():
    """
    Given: Active terminal session
    Should: Return alive=True
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create terminal
        create_resp = await client.post("/api/terminals", json={})
        session_id = create_resp.json()["session_id"]

        # Check alive
        response = await client.get(f"/api/terminals/{session_id}/alive")

    assert response.status_code == 200
    data = response.json()
    assert "alive" in data
    assert data["alive"] is True


@pytest.mark.asyncio
async def test_check_alive_returns_status_false():
    """
    Given: Destroyed terminal session
    Should: Return alive=False
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create and then destroy terminal
        create_resp = await client.post("/api/terminals", json={})
        session_id = create_resp.json()["session_id"]
        await client.delete(f"/api/terminals/{session_id}")

        # Check alive - should still work but return false
        response = await client.get(f"/api/terminals/{session_id}/alive")

    assert response.status_code == 200
    data = response.json()
    assert data["alive"] is False


@pytest.mark.asyncio
async def test_check_alive_nonexistent():
    """
    Given: Non-existent terminal ID
    Should: Return alive=False (not 404, for client convenience)
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/terminals/nonexistent-id/alive")

    assert response.status_code == 200
    data = response.json()
    assert data["alive"] is False


# =============================================================================
# Session Info in List
# =============================================================================


@pytest.mark.asyncio
async def test_list_sessions_includes_metadata():
    """
    Given: Active terminal with specific cwd
    Should: Return session with cwd and alive status
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create terminal with specific cwd
        create_resp = await client.post("/api/terminals", json={"cwd": "/tmp"})
        session_id = create_resp.json()["session_id"]

        # List sessions
        response = await client.get("/api/terminals/sessions")

    assert response.status_code == 200
    data = response.json()
    session = next(s for s in data["sessions"] if s["id"] == session_id)
    assert session["cwd"] == "/tmp"
    assert session["alive"] is True
