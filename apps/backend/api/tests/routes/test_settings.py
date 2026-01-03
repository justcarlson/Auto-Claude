#!/usr/bin/env python3
"""
Settings Endpoint Tests
=======================

TDD tests for the /api/settings and /api/version endpoints.
Tests written BEFORE implementation to drive development.
"""

import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path):
    """Ensure each test uses isolated settings storage."""
    from api.services import SettingsService

    # Set temp data directory for this test
    original_data_dir = os.environ.get("DATA_DIR")
    os.environ["DATA_DIR"] = str(tmp_path)

    # Reset the service to use new directory
    SettingsService.reset()

    yield

    # Restore original
    if original_data_dir:
        os.environ["DATA_DIR"] = original_data_dir
    else:
        os.environ.pop("DATA_DIR", None)

    # Reset again for next test
    SettingsService.reset()


# =============================================================================
# GET /api/settings
# =============================================================================


@pytest.mark.asyncio
async def test_get_settings_returns_defaults():
    """
    Given: No settings have been saved
    Should: Return default settings with theme='system'
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/settings")

    assert response.status_code == 200
    data = response.json()
    assert "theme" in data
    assert data["theme"] == "system"  # Default theme


@pytest.mark.asyncio
async def test_get_settings_returns_json_content_type():
    """
    Given: API server is running
    Should: Return application/json content type
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/settings")

    assert "application/json" in response.headers.get("content-type", "")


# =============================================================================
# PUT /api/settings
# =============================================================================


@pytest.mark.asyncio
async def test_save_settings_partial_update():
    """
    Given: Default settings exist
    When: PUT with partial update {theme: 'dark'}
    Should: Merge with existing settings and return updated values
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Save partial settings
        response = await client.put("/api/settings", json={"theme": "dark"})

    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "dark"


@pytest.mark.asyncio
async def test_get_settings_persists_changes():
    """
    Given: Settings have been saved with theme='dark'
    Should: Return the saved settings on subsequent GET
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # First save settings
        await client.put("/api/settings", json={"theme": "dark"})

        # Then retrieve them
        response = await client.get("/api/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "dark"


@pytest.mark.asyncio
async def test_save_settings_invalid_theme_rejected():
    """
    Given: Valid settings schema
    When: PUT with invalid theme value
    Should: Return 422 Unprocessable Entity
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put("/api/settings", json={"theme": "invalid_theme"})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_save_settings_with_all_fields():
    """
    Given: API server is running
    When: PUT with all settings fields
    Should: Save and return all fields correctly
    """
    from api.main import app

    settings = {
        "theme": "light",
        "defaultModel": "claude-3-opus",
        "graphitiEnabled": True,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put("/api/settings", json=settings)

    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "light"
    assert data["defaultModel"] == "claude-3-opus"
    assert data["graphitiEnabled"] is True


# =============================================================================
# GET /api/version
# =============================================================================


@pytest.mark.asyncio
async def test_get_version_returns_string():
    """
    Given: API server is running
    Should: Return a version string
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/version")

    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)
    # Version should match semver-ish pattern (e.g., "2.7.1" or "0.1.0")
    assert len(data["version"].split(".")) >= 2


@pytest.mark.asyncio
async def test_get_version_is_fast():
    """
    Given: API server is running
    Should: Respond within 100ms (fast version check)
    """
    import time

    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        start = time.time()
        response = await client.get("/api/version")
        duration = time.time() - start

    assert response.status_code == 200
    assert duration < 0.1, f"Version check took {duration:.3f}s, expected < 0.1s"
