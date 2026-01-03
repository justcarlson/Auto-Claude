#!/usr/bin/env python3
"""
Project Environment Endpoint Tests
===================================

TDD tests for the /api/projects/{id}/env endpoints.
"""

import os

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def isolated_env(tmp_path):
    """Ensure each test uses isolated storage."""
    from api.services import ProjectService, SettingsService

    original_data_dir = os.environ.get("DATA_DIR")
    os.environ["DATA_DIR"] = str(tmp_path)

    ProjectService.reset()
    SettingsService.reset()

    yield

    if original_data_dir:
        os.environ["DATA_DIR"] = original_data_dir
    else:
        os.environ.pop("DATA_DIR", None)

    ProjectService.reset()
    SettingsService.reset()


async def create_test_project(client: AsyncClient) -> dict:
    """Helper to create a test project."""
    response = await client.post("/api/projects", json={"path": "/test/project"})
    return response.json()


# =============================================================================
# GET /api/projects/{id}/env
# =============================================================================


@pytest.mark.asyncio
async def test_get_env_project_not_found_404():
    """
    Given: Project does not exist
    Should: Return 404 Not Found
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/projects/nonexistent-id/env")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_env_returns_defaults():
    """
    Given: Project exists but no env config set
    Should: Return default env config with all fields
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_test_project(client)
        response = await client.get(f"/api/projects/{project['id']}/env")

    assert response.status_code == 200
    data = response.json()

    assert "claudeAuthStatus" in data
    assert data["claudeAuthStatus"] == "not_configured"
    assert "linearEnabled" in data
    assert data["linearEnabled"] is False
    assert "githubEnabled" in data
    assert data["githubEnabled"] is False
    assert "gitlabEnabled" in data
    assert data["gitlabEnabled"] is False
    assert "graphitiEnabled" in data
    assert data["graphitiEnabled"] is False


# =============================================================================
# PUT /api/projects/{id}/env
# =============================================================================


@pytest.mark.asyncio
async def test_update_env_project_not_found_404():
    """
    Given: Project does not exist
    Should: Return 404 Not Found
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/api/projects/nonexistent-id/env", json={"linearEnabled": True}
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_env_partial_merge():
    """
    Given: Project exists with default env config
    When: PUT with partial update {linearEnabled: true, linearApiKey: 'key'}
    Should: Merge with existing config and return updated values
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_test_project(client)

        response = await client.put(
            f"/api/projects/{project['id']}/env",
            json={"linearEnabled": True, "linearApiKey": "test-key"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["linearEnabled"] is True
    assert data["linearApiKey"] == "test-key"
    assert data["githubEnabled"] is False


@pytest.mark.asyncio
async def test_update_env_persists_changes():
    """
    Given: Project env config has been updated
    Should: Return the updated config on subsequent GET
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_test_project(client)

        await client.put(
            f"/api/projects/{project['id']}/env",
            json={"githubEnabled": True, "githubRepo": "owner/repo"},
        )

        response = await client.get(f"/api/projects/{project['id']}/env")

    assert response.status_code == 200
    data = response.json()
    assert data["githubEnabled"] is True
    assert data["githubRepo"] == "owner/repo"


@pytest.mark.asyncio
async def test_update_env_creates_if_missing():
    """
    Given: Project exists but has never had env config set
    When: PUT with config update
    Should: Create new env config with provided values
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_test_project(client)

        response = await client.put(
            f"/api/projects/{project['id']}/env",
            json={"graphitiEnabled": True, "autoBuildModel": "claude-3-opus"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["graphitiEnabled"] is True
    assert data["autoBuildModel"] == "claude-3-opus"


@pytest.mark.asyncio
async def test_update_env_with_mcp_servers():
    """
    Given: Project exists
    When: PUT with mcpServers configuration
    Should: Save and return MCP server settings
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        project = await create_test_project(client)

        response = await client.put(
            f"/api/projects/{project['id']}/env",
            json={"mcpServers": {"context7Enabled": True, "graphitiEnabled": False}},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["mcpServers"]["context7Enabled"] is True
    assert data["mcpServers"]["graphitiEnabled"] is False
