#!/usr/bin/env python3
"""
Task Execution API Tests
========================

TDD tests for task execution endpoints:
- POST /api/tasks/{task_id}/start
- POST /api/tasks/{task_id}/stop
- POST /api/tasks/{task_id}/review
- PUT /api/tasks/{task_id}/status
- GET /api/tasks/{task_id}/running
- POST /api/tasks/{task_id}/recover
"""

import pytest
from httpx import ASGITransport, AsyncClient

# =============================================================================
# HELPER: Create project and task for execution tests
# =============================================================================


async def create_project(client: AsyncClient, path: str = "/projects/test") -> dict:
    """Helper to create a project and return its data."""
    response = await client.post("/api/projects", json={"path": path})
    assert response.status_code == 201
    return response.json()


async def create_task(
    client: AsyncClient, project_id: str, title: str = "Test Task"
) -> dict:
    """Helper to create a task and return its data."""
    response = await client.post(
        f"/api/projects/{project_id}/tasks",
        json={"title": title, "description": "Test description"},
    )
    assert response.status_code == 201
    return response.json()


# =============================================================================
# START TASK
# =============================================================================


@pytest.mark.asyncio
async def test_start_task_not_found_404():
    """
    Given: Non-existent task ID
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/tasks/nonexistent-task/start", json={})

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_task_creates_process():
    """
    Given: Valid task ID
    Should: Start task execution and return running state
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/exec-test-1")
        task = await create_task(client, project["id"], "Start Test")

        response = await client.post(f"/api/tasks/{task['id']}/start", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["taskId"] == task["id"]
    assert data["status"] in ["starting", "running"]


@pytest.mark.asyncio
async def test_start_task_with_options():
    """
    Given: Valid task ID with execution options
    Should: Accept options and start task
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/exec-test-2")
        task = await create_task(client, project["id"], "Options Test")

        response = await client.post(
            f"/api/tasks/{task['id']}/start",
            json={"parallel": True, "workers": 4},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


# =============================================================================
# STOP TASK
# =============================================================================


@pytest.mark.asyncio
async def test_stop_task_not_found_404():
    """
    Given: Non-existent task ID
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/tasks/nonexistent-task/stop", json={})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_stop_task_kills_process():
    """
    Given: Running task
    Should: Stop execution and return stopped state
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/exec-test-3")
        task = await create_task(client, project["id"], "Stop Test")

        # Start task first
        await client.post(f"/api/tasks/{task['id']}/start", json={})

        # Stop task
        response = await client.post(f"/api/tasks/{task['id']}/stop", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["taskId"] == task["id"]


# =============================================================================
# SUBMIT REVIEW
# =============================================================================


@pytest.mark.asyncio
async def test_submit_review_task_not_found_404():
    """
    Given: Non-existent task ID
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/tasks/nonexistent-task/review",
            json={"approved": True},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_review_approved():
    """
    Given: Task in review state
    Should: Mark approved and update status to done
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/exec-test-4")
        task = await create_task(client, project["id"], "Review Test")

        response = await client.post(
            f"/api/tasks/{task['id']}/review",
            json={"approved": True},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "done"


@pytest.mark.asyncio
async def test_submit_review_rejected_with_feedback():
    """
    Given: Task review rejected
    Should: Return to in_progress with feedback stored
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/exec-test-5")
        task = await create_task(client, project["id"], "Reject Test")

        response = await client.post(
            f"/api/tasks/{task['id']}/review",
            json={"approved": False, "feedback": "Needs more tests"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "in_progress"
    assert "feedback" in data


# =============================================================================
# UPDATE STATUS
# =============================================================================


@pytest.mark.asyncio
async def test_update_status_task_not_found_404():
    """
    Given: Non-existent task ID
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/api/tasks/nonexistent-task/status",
            json={"status": "in_progress"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_status_valid_transition():
    """
    Given: Valid status transition
    Should: Update and return new status
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/exec-test-6")
        task = await create_task(client, project["id"], "Status Test")

        response = await client.put(
            f"/api/tasks/{task['id']}/status",
            json={"status": "in_progress"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_update_status_invalid_status_400():
    """
    Given: Invalid status value
    Should: Return 400 validation error
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/exec-test-7")
        task = await create_task(client, project["id"], "Invalid Status Test")

        response = await client.put(
            f"/api/tasks/{task['id']}/status",
            json={"status": "invalid_status_value"},
        )

    assert response.status_code == 400


# =============================================================================
# CHECK TASK RUNNING
# =============================================================================


@pytest.mark.asyncio
async def test_check_task_running_not_found_404():
    """
    Given: Non-existent task ID
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/tasks/nonexistent-task/running")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_check_task_running_true():
    """
    Given: Task is running
    Should: Return running=true
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/exec-test-8")
        task = await create_task(client, project["id"], "Running Check Test")

        # Start task
        await client.post(f"/api/tasks/{task['id']}/start", json={})

        # Check if running
        response = await client.get(f"/api/tasks/{task['id']}/running")

    assert response.status_code == 200
    data = response.json()
    assert data["running"] is True


@pytest.mark.asyncio
async def test_check_task_running_false():
    """
    Given: Task is not running
    Should: Return running=false
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/exec-test-9")
        task = await create_task(client, project["id"], "Not Running Test")

        # Don't start task
        response = await client.get(f"/api/tasks/{task['id']}/running")

    assert response.status_code == 200
    data = response.json()
    assert data["running"] is False


# =============================================================================
# RECOVER STUCK TASK
# =============================================================================


@pytest.mark.asyncio
async def test_recover_stuck_task_not_found_404():
    """
    Given: Non-existent task ID
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/tasks/nonexistent-task/recover", json={})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_recover_stuck_task():
    """
    Given: Task is stuck
    Should: Recover and return new status
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/exec-test-10")
        task = await create_task(client, project["id"], "Recover Test")

        response = await client.post(
            f"/api/tasks/{task['id']}/recover",
            json={"targetStatus": "pending", "autoRestart": False},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "newStatus" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_recover_stuck_task_with_auto_restart():
    """
    Given: Task recovery with auto restart
    Should: Recover and restart the task
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/exec-test-11")
        task = await create_task(client, project["id"], "Auto Restart Test")

        response = await client.post(
            f"/api/tasks/{task['id']}/recover",
            json={"autoRestart": True},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
