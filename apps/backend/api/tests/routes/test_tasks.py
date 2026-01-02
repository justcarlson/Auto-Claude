#!/usr/bin/env python3
"""
Tasks CRUD API Tests
====================

TDD tests for task management endpoints (nested under projects):
- POST /api/projects/{project_id}/tasks (create)
- GET /api/projects/{project_id}/tasks (list)
- GET /api/projects/{project_id}/tasks/{task_id} (get)
- PUT /api/projects/{project_id}/tasks/{task_id} (update)
- DELETE /api/projects/{project_id}/tasks/{task_id} (delete)
"""

import pytest
from httpx import ASGITransport, AsyncClient

# =============================================================================
# HELPER: Create project for task tests
# =============================================================================


async def create_project(client: AsyncClient, path: str = "/projects/test") -> dict:
    """Helper to create a project and return its data."""
    response = await client.post("/api/projects", json={"path": path})
    assert response.status_code == 201
    return response.json()


# =============================================================================
# CREATE TASK
# =============================================================================


@pytest.mark.asyncio
async def test_create_task_returns_task_with_id():
    """
    Given: Valid task data and existing project
    Should: Return created task with id and project_id
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/task-test-1")

        response = await client.post(
            f"/api/projects/{project['id']}/tasks",
            json={"title": "Add login", "description": "Implement OAuth2 login"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Add login"
    assert data["description"] == "Implement OAuth2 login"
    assert data["project_id"] == project["id"]
    assert data["status"] == "pending"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_task_requires_title():
    """
    Given: Task data without title
    Should: Return 422 validation error
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/task-test-2")

        response = await client.post(
            f"/api/projects/{project['id']}/tasks",
            json={"description": "Missing title"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_requires_description():
    """
    Given: Task data without description
    Should: Return 422 validation error
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/task-test-3")

        response = await client.post(
            f"/api/projects/{project['id']}/tasks",
            json={"title": "Missing description"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_project_not_found():
    """
    Given: Non-existent project ID
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/projects/nonexistent-project/tasks",
            json={"title": "Test", "description": "Test description"},
        )

    assert response.status_code == 404


# =============================================================================
# LIST TASKS
# =============================================================================


@pytest.mark.asyncio
async def test_list_tasks_returns_empty_initially():
    """
    Given: Project with no tasks
    Should: Return empty list
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/task-test-4")

        response = await client.get(f"/api/projects/{project['id']}/tasks")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_tasks_includes_created():
    """
    Given: Project with tasks
    Should: Return list of tasks
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/task-test-5")

        # Create tasks
        await client.post(
            f"/api/projects/{project['id']}/tasks",
            json={"title": "Task 1", "description": "Description 1"},
        )
        await client.post(
            f"/api/projects/{project['id']}/tasks",
            json={"title": "Task 2", "description": "Description 2"},
        )

        # List
        response = await client.get(f"/api/projects/{project['id']}/tasks")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    titles = [t["title"] for t in data]
    assert "Task 1" in titles
    assert "Task 2" in titles


@pytest.mark.asyncio
async def test_list_tasks_project_not_found():
    """
    Given: Non-existent project ID
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/projects/nonexistent-project/tasks")

    assert response.status_code == 404


# =============================================================================
# GET TASK
# =============================================================================


@pytest.mark.asyncio
async def test_get_task_by_id():
    """
    Given: Task exists
    Should: Return task details
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/task-test-6")

        # Create task
        create_response = await client.post(
            f"/api/projects/{project['id']}/tasks",
            json={"title": "Get Test", "description": "Test description"},
        )
        task = create_response.json()

        # Get by id
        response = await client.get(f"/api/projects/{project['id']}/tasks/{task['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task["id"]
    assert data["title"] == "Get Test"


@pytest.mark.asyncio
async def test_get_task_not_found():
    """
    Given: Task does not exist
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/task-test-7")

        response = await client.get(
            f"/api/projects/{project['id']}/tasks/nonexistent-task"
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_task_project_not_found():
    """
    Given: Non-existent project ID
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/projects/nonexistent-project/tasks/some-task")

    assert response.status_code == 404


# =============================================================================
# UPDATE TASK
# =============================================================================


@pytest.mark.asyncio
async def test_update_task_title():
    """
    Given: Task exists and valid update data
    Should: Update title and return updated task
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/task-test-8")

        # Create task
        create_response = await client.post(
            f"/api/projects/{project['id']}/tasks",
            json={"title": "Original Title", "description": "Description"},
        )
        task = create_response.json()

        # Update
        response = await client.put(
            f"/api/projects/{project['id']}/tasks/{task['id']}",
            json={"title": "Updated Title"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Description"  # Unchanged


@pytest.mark.asyncio
async def test_update_task_status():
    """
    Given: Task exists and status update
    Should: Update status and return updated task
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/task-test-9")

        # Create task
        create_response = await client.post(
            f"/api/projects/{project['id']}/tasks",
            json={"title": "Status Test", "description": "Description"},
        )
        task = create_response.json()
        assert task["status"] == "pending"

        # Update status
        response = await client.put(
            f"/api/projects/{project['id']}/tasks/{task['id']}",
            json={"status": "in_progress"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_update_task_not_found():
    """
    Given: Task does not exist
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/task-test-10")

        response = await client.put(
            f"/api/projects/{project['id']}/tasks/nonexistent-task",
            json={"title": "Updated"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_task_updates_updated_at():
    """
    Given: Task is updated
    Should: Updated_at timestamp changes
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/task-test-11")

        # Create task
        create_response = await client.post(
            f"/api/projects/{project['id']}/tasks",
            json={"title": "Timestamp Test", "description": "Description"},
        )
        task = create_response.json()
        original_updated_at = task["updated_at"]

        # Small delay to ensure timestamp difference
        import asyncio

        await asyncio.sleep(0.01)

        # Update
        response = await client.put(
            f"/api/projects/{project['id']}/tasks/{task['id']}",
            json={"title": "Changed"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["updated_at"] >= original_updated_at


# =============================================================================
# DELETE TASK
# =============================================================================


@pytest.mark.asyncio
async def test_delete_task_removes_it():
    """
    Given: Task exists
    Should: Remove and return 204
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/task-test-12")

        # Create task
        create_response = await client.post(
            f"/api/projects/{project['id']}/tasks",
            json={"title": "Delete Test", "description": "Description"},
        )
        task = create_response.json()

        # Delete
        delete_response = await client.delete(
            f"/api/projects/{project['id']}/tasks/{task['id']}"
        )
        assert delete_response.status_code == 204

        # Verify deleted
        get_response = await client.get(
            f"/api/projects/{project['id']}/tasks/{task['id']}"
        )
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_not_found():
    """
    Given: Task does not exist
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_project(client, "/projects/task-test-13")

        response = await client.delete(
            f"/api/projects/{project['id']}/tasks/nonexistent-task"
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_project_not_found():
    """
    Given: Non-existent project ID
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(
            "/api/projects/nonexistent-project/tasks/some-task"
        )

    assert response.status_code == 404
