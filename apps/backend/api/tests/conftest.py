#!/usr/bin/env python3
"""
Pytest Configuration for FastAPI API Tests
==========================================

Provides async client fixtures for testing the FastAPI backend
without running a server using httpx ASGITransport.
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Add apps/backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# =============================================================================
# ASYNC CLIENT FIXTURES
# =============================================================================


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing FastAPI endpoints.

    Uses ASGITransport to test the app in-memory without starting a server.
    This is the recommended pattern for FastAPI testing.

    Usage:
        async def test_health(async_client):
            response = await async_client.get("/api/health")
            assert response.status_code == 200
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def async_client_with_data(
    temp_data_dir: Path,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async client with a temporary data directory.

    Sets DATA_DIR environment variable to ensure tests have isolated storage.
    """
    from api.main import app

    original_data_dir = os.environ.get("DATA_DIR")
    os.environ["DATA_DIR"] = str(temp_data_dir)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    # Restore original
    if original_data_dir:
        os.environ["DATA_DIR"] = original_data_dir
    else:
        os.environ.pop("DATA_DIR", None)


# =============================================================================
# DIRECTORY FIXTURES
# =============================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory that's cleaned up after the test."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_data_dir(temp_dir: Path) -> Path:
    """Create a temporary data directory for API storage."""
    data_path = temp_dir / "data"
    data_path.mkdir(parents=True)
    return data_path


@pytest.fixture
def temp_projects_dir(temp_dir: Path) -> Path:
    """Create a temporary projects directory."""
    projects_path = temp_dir / "projects"
    projects_path.mkdir(parents=True)
    return projects_path


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================


@pytest.fixture(autouse=True)
def reset_services():
    """Reset all service singletons before each test."""
    from api.services import ProjectService, TaskService

    ProjectService.reset()
    TaskService.reset()
    yield
    ProjectService.reset()
    TaskService.reset()


@pytest.fixture
def sample_project_data() -> dict:
    """Return sample project data for testing."""
    return {
        "path": "/projects/test-app",
        "name": "test-app",
    }


@pytest.fixture
def sample_task_data() -> dict:
    """Return sample task data for testing."""
    return {
        "title": "Add user authentication",
        "description": "Implement OAuth2 login with Google provider",
    }


# =============================================================================
# JSON FILE HELPERS
# =============================================================================


@pytest.fixture
def write_json(temp_data_dir: Path):
    """Factory fixture to write JSON files to temp data directory."""

    def _write_json(filename: str, data: dict) -> Path:
        filepath = temp_data_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(data, indent=2))
        return filepath

    return _write_json


@pytest.fixture
def read_json(temp_data_dir: Path):
    """Factory fixture to read JSON files from temp data directory."""

    def _read_json(filename: str) -> dict:
        filepath = temp_data_dir / filename
        return json.loads(filepath.read_text())

    return _read_json
