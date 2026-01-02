#!/usr/bin/env python3
"""
Projects CRUD API Tests
=======================

TDD tests for project management endpoints:
- GET /api/projects (list)
- POST /api/projects (create)
- GET /api/projects/{id} (get)
- DELETE /api/projects/{id} (delete)
"""

import pytest
from httpx import ASGITransport, AsyncClient


# =============================================================================
# LIST PROJECTS
# =============================================================================


@pytest.mark.asyncio
async def test_list_projects_returns_empty_initially():
    """
    Given: No projects have been added
    Should: Return empty list
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/projects")

    assert response.status_code == 200
    assert response.json() == []


# =============================================================================
# ADD PROJECT
# =============================================================================


@pytest.mark.asyncio
async def test_add_project_creates_project():
    """
    Given: Valid project path
    Should: Return created project with id
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/projects", json={"path": "/projects/my-app"})

    assert response.status_code == 201
    data = response.json()
    assert data["path"] == "/projects/my-app"
    assert "id" in data
    assert data["name"] == "my-app"  # Derived from path


@pytest.mark.asyncio
async def test_add_project_requires_path():
    """
    Given: Request without path
    Should: Return 422 validation error
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/projects", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_project_prevents_duplicates():
    """
    Given: Project with same path already exists
    Should: Return 409 conflict
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # First add
        await client.post("/api/projects", json={"path": "/projects/dup-app"})

        # Second add (duplicate)
        response = await client.post(
            "/api/projects", json={"path": "/projects/dup-app"}
        )

    assert response.status_code == 409


# =============================================================================
# GET PROJECT
# =============================================================================


@pytest.mark.asyncio
async def test_get_project_by_id():
    """
    Given: Project exists
    Should: Return project details
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create project
        create_response = await client.post(
            "/api/projects", json={"path": "/projects/get-test"}
        )
        project = create_response.json()

        # Get by id
        response = await client.get(f"/api/projects/{project['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project["id"]
    assert data["path"] == "/projects/get-test"


@pytest.mark.asyncio
async def test_get_project_not_found():
    """
    Given: Project does not exist
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/projects/nonexistent-id")

    assert response.status_code == 404


# =============================================================================
# DELETE PROJECT
# =============================================================================


@pytest.mark.asyncio
async def test_delete_project_removes_it():
    """
    Given: Project exists
    Should: Remove and return 204
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create project
        create_response = await client.post(
            "/api/projects", json={"path": "/projects/delete-test"}
        )
        project = create_response.json()

        # Delete
        delete_response = await client.delete(f"/api/projects/{project['id']}")
        assert delete_response.status_code == 204

        # Verify deleted
        get_response = await client.get(f"/api/projects/{project['id']}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_found():
    """
    Given: Project does not exist
    Should: Return 404
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/api/projects/nonexistent-id")

    assert response.status_code == 404


# =============================================================================
# LIST AFTER MUTATIONS
# =============================================================================


@pytest.mark.asyncio
async def test_list_projects_includes_added():
    """
    Given: Projects have been added
    Should: Return list including added projects
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Add projects
        await client.post("/api/projects", json={"path": "/projects/list-test-1"})
        await client.post("/api/projects", json={"path": "/projects/list-test-2"})

        # List
        response = await client.get("/api/projects")

    assert response.status_code == 200
    data = response.json()
    paths = [p["path"] for p in data]
    assert "/projects/list-test-1" in paths
    assert "/projects/list-test-2" in paths
