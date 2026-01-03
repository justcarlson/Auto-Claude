#!/usr/bin/env python3
"""
Task Logs Endpoints Tests
=========================

TDD tests for the /api/tasks/{task_id}/logs endpoints.
Tests written BEFORE implementation to drive development.
"""

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def project_with_task_logs(tmp_path: Path):
    """
    Create a temporary project with spec directories and task logs.
    Mirrors the structure used by the Electron frontend.
    """
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Create .auto-claude/specs structure
    specs_dir = project_dir / ".auto-claude" / "specs"
    specs_dir.mkdir(parents=True)

    # Create a spec directory with logs
    spec_001 = specs_dir / "001-test-feature"
    spec_001.mkdir()

    # Create task_logs.json with realistic structure
    task_logs = {
        "spec_id": "001-test-feature",
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-01T12:00:00Z",
        "phases": {
            "planning": {
                "phase": "planning",
                "status": "completed",
                "started_at": "2025-01-01T10:00:00Z",
                "completed_at": "2025-01-01T10:30:00Z",
                "entries": [
                    {
                        "timestamp": "2025-01-01T10:00:00Z",
                        "type": "phase_start",
                        "content": "Starting planning phase",
                        "phase": "planning",
                    },
                    {
                        "timestamp": "2025-01-01T10:15:00Z",
                        "type": "text",
                        "content": "Analyzing requirements...",
                        "phase": "planning",
                    },
                    {
                        "timestamp": "2025-01-01T10:30:00Z",
                        "type": "phase_end",
                        "content": "Planning complete",
                        "phase": "planning",
                    },
                ],
            },
            "coding": {
                "phase": "coding",
                "status": "active",
                "started_at": "2025-01-01T10:30:00Z",
                "completed_at": None,
                "entries": [
                    {
                        "timestamp": "2025-01-01T10:30:00Z",
                        "type": "phase_start",
                        "content": "Starting coding phase",
                        "phase": "coding",
                    },
                    {
                        "timestamp": "2025-01-01T11:00:00Z",
                        "type": "tool_start",
                        "content": "Reading file",
                        "phase": "coding",
                        "tool_name": "Read",
                        "tool_input": "src/main.ts",
                    },
                ],
            },
            "validation": {
                "phase": "validation",
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "entries": [],
            },
        },
    }

    (spec_001 / "task_logs.json").write_text(json.dumps(task_logs, indent=2))

    # Create spec.md for task identification
    (spec_001 / "spec.md").write_text("# Test Feature\n\nDescription of the feature.")

    return project_dir, spec_001


@pytest.fixture
def project_without_logs(tmp_path: Path):
    """
    Create a project with a spec directory but no logs file.
    """
    project_dir = tmp_path / "no-logs-project"
    project_dir.mkdir()

    specs_dir = project_dir / ".auto-claude" / "specs"
    specs_dir.mkdir(parents=True)

    spec_002 = specs_dir / "002-no-logs"
    spec_002.mkdir()

    # Only spec.md, no task_logs.json
    (spec_002 / "spec.md").write_text("# No Logs Feature")

    return project_dir, spec_002


@pytest.fixture(autouse=True)
def isolated_task_logs_service(tmp_path: Path):
    """Ensure each test uses isolated task logs service."""
    from api.services.task_logs_service import TaskLogsService

    # Reset service for fresh state
    TaskLogsService.reset()

    yield

    # Cleanup after test
    TaskLogsService.reset()


# =============================================================================
# GET /api/tasks/{task_id}/logs - Get Task Logs
# =============================================================================


@pytest.mark.asyncio
async def test_get_logs_returns_structured_data(project_with_task_logs):
    """
    Given: A task with logs in spec directory
    Should: Return structured log data with phases and entries
    """
    from api.main import app
    from api.services.task_logs_service import TaskLogsService

    project_dir, spec_dir = project_with_task_logs

    service = TaskLogsService.get_instance()
    service.set_project_dir(project_dir)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/tasks/001-test-feature/logs")

    assert response.status_code == 200
    data = response.json()

    # Check top-level structure
    assert "spec_id" in data
    assert data["spec_id"] == "001-test-feature"
    assert "created_at" in data
    assert "updated_at" in data
    assert "phases" in data

    # Check phases structure
    phases = data["phases"]
    assert "planning" in phases
    assert "coding" in phases
    assert "validation" in phases

    # Check planning phase
    planning = phases["planning"]
    assert planning["phase"] == "planning"
    assert planning["status"] == "completed"
    assert planning["started_at"] is not None
    assert planning["completed_at"] is not None
    assert len(planning["entries"]) == 3

    # Check coding phase (active)
    coding = phases["coding"]
    assert coding["phase"] == "coding"
    assert coding["status"] == "active"
    assert len(coding["entries"]) == 2

    # Check an entry has expected fields
    entry = coding["entries"][1]
    assert entry["type"] == "tool_start"
    assert entry["tool_name"] == "Read"


@pytest.mark.asyncio
async def test_get_logs_for_nonexistent_task(project_with_task_logs):
    """
    Given: A task ID that doesn't exist
    Should: Return 404 Not Found
    """
    from api.main import app
    from api.services.task_logs_service import TaskLogsService

    project_dir, _ = project_with_task_logs

    service = TaskLogsService.get_instance()
    service.set_project_dir(project_dir)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/tasks/999-nonexistent/logs")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_logs_for_task_without_logs(project_without_logs):
    """
    Given: A task that exists but has no logs file
    Should: Return 404 Not Found with appropriate message
    """
    from api.main import app
    from api.services.task_logs_service import TaskLogsService

    project_dir, _ = project_without_logs

    service = TaskLogsService.get_instance()
    service.set_project_dir(project_dir)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/tasks/002-no-logs/logs")

    assert response.status_code == 404
    assert "logs" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_logs_path_traversal_blocked(project_with_task_logs):
    """
    Given: A malicious task_id with path traversal
    Should: Return 403 Forbidden or 404 (route doesn't match)

    Note: FastAPI handles some traversal attempts at the routing level,
    returning 404 if the path doesn't match. We accept either 403 or 404
    as valid security responses - the key is that the attack doesn't succeed.
    """
    from api.main import app
    from api.services.task_logs_service import TaskLogsService

    project_dir, _ = project_with_task_logs

    service = TaskLogsService.get_instance()
    service.set_project_dir(project_dir)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Try various path traversal attacks
        # All should return either 403 (service blocked) or 404 (route not matched)
        attacks = [
            "..%2F..%2F..%2Fetc%2Fpasswd",  # URL-encoded ../
            "..%5C..%5Cwindows%5Csystem32",  # URL-encoded ..\
            "../../../etc/passwd",
            "001-test/../../../etc/passwd",
            "..\\..\\windows\\system32",
        ]

        for attack in attacks:
            response = await client.get(f"/api/tasks/{attack}/logs")
            # 403 = service blocked, 404 = route didn't match (also secure)
            # Just ensure we don't get 200 (success) or 500 (server error)
            assert response.status_code in [403, 404], (
                f"Path traversal not blocked: {attack}, got {response.status_code}"
            )


@pytest.mark.asyncio
async def test_get_logs_returns_proper_entry_types(project_with_task_logs):
    """
    Given: A task with various log entry types
    Should: Return entries with correct type discrimination
    """
    from api.main import app
    from api.services.task_logs_service import TaskLogsService

    project_dir, _ = project_with_task_logs

    service = TaskLogsService.get_instance()
    service.set_project_dir(project_dir)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/tasks/001-test-feature/logs")

    assert response.status_code == 200
    data = response.json()

    # Collect all entry types
    all_types = set()
    for phase_data in data["phases"].values():
        for entry in phase_data["entries"]:
            all_types.add(entry["type"])

    # Should have variety of types
    assert "phase_start" in all_types
    assert "text" in all_types or "tool_start" in all_types


# =============================================================================
# Service Configuration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_service_not_configured_error(tmp_path: Path):
    """
    Given: Service not configured with project dir
    Should: Return 500 error with configuration message
    """
    from api.main import app
    from api.services.task_logs_service import TaskLogsService

    # Don't configure service
    TaskLogsService.reset()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/tasks/any-task/logs")

    # Should return error about configuration
    assert response.status_code == 500
    assert "configured" in response.json()["detail"].lower()


# =============================================================================
# Corrupted/Invalid JSON Tests
# =============================================================================


@pytest.fixture
def project_with_corrupted_logs(tmp_path: Path):
    """
    Create a project with corrupted task_logs.json.
    """
    project_dir = tmp_path / "corrupted-project"
    project_dir.mkdir()

    specs_dir = project_dir / ".auto-claude" / "specs"
    specs_dir.mkdir(parents=True)

    spec = specs_dir / "003-corrupted"
    spec.mkdir()

    # Write invalid JSON
    (spec / "task_logs.json").write_text("{invalid json content")
    (spec / "spec.md").write_text("# Corrupted")

    return project_dir


@pytest.mark.asyncio
async def test_get_logs_with_corrupted_json(project_with_corrupted_logs):
    """
    Given: A task with corrupted task_logs.json
    Should: Return 500 error (or graceful fallback)
    """
    from api.main import app
    from api.services.task_logs_service import TaskLogsService

    service = TaskLogsService.get_instance()
    service.set_project_dir(project_with_corrupted_logs)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/tasks/003-corrupted/logs")

    # Could be 500 (parse error) or 404 (treated as no logs)
    # Either is acceptable, just not 200
    assert response.status_code in [404, 500]
