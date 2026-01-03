#!/usr/bin/env python3
"""
Worktree Endpoints Tests
========================

TDD tests for the /api/worktrees endpoints.
Tests written BEFORE implementation to drive development.
"""

import os
import subprocess
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def git_project(tmp_path: Path):
    """
    Create a temporary git project with initial commit.
    This is required for worktree operations.
    """
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )

    # Create initial file and commit
    (project_dir / "README.md").write_text("# Test Project\n")
    subprocess.run(
        ["git", "add", "."], cwd=project_dir, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )

    # Rename default branch to main if needed
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip() != "main":
        subprocess.run(
            ["git", "branch", "-m", result.stdout.strip(), "main"],
            cwd=project_dir,
            capture_output=True,
        )

    return project_dir


@pytest.fixture
def git_project_with_worktree(git_project: Path):
    """
    Create a git project with an existing worktree for a spec.
    """
    spec_name = "001-test-task"
    worktrees_dir = git_project / ".worktrees"
    worktrees_dir.mkdir()
    worktree_path = worktrees_dir / spec_name
    branch_name = f"auto-claude/{spec_name}"

    # Create worktree with new branch
    subprocess.run(
        ["git", "worktree", "add", "-b", branch_name, str(worktree_path), "main"],
        cwd=git_project,
        check=True,
        capture_output=True,
    )

    # Make some changes in the worktree
    (worktree_path / "new_file.py").write_text("# New file\nprint('hello')\n")
    subprocess.run(
        ["git", "add", "."], cwd=worktree_path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Add new file"],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )

    return {
        "project_dir": git_project,
        "spec_name": spec_name,
        "worktree_path": worktree_path,
        "branch_name": branch_name,
    }


@pytest.fixture(autouse=True)
def isolated_worktree_service(tmp_path: Path):
    """Ensure each test uses isolated worktree service."""
    from api.services.worktree_service import WorktreeService

    # Reset worktree service for fresh state
    WorktreeService.reset()

    yield

    # Cleanup after test
    WorktreeService.reset()


# =============================================================================
# GET /api/projects/{id}/worktrees - List Worktrees
# =============================================================================


@pytest.mark.asyncio
async def test_list_worktrees_empty(git_project: Path):
    """
    Given: A project with no worktrees
    Should: Return empty worktrees list
    """
    from api.main import app
    from api.services.worktree_service import WorktreeService

    # Configure service with test project
    service = WorktreeService.get_instance()
    service.set_project_dir(git_project)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/projects/test-project-id/worktrees")

    assert response.status_code == 200
    data = response.json()
    assert "worktrees" in data
    assert isinstance(data["worktrees"], list)
    assert len(data["worktrees"]) == 0


@pytest.mark.asyncio
async def test_list_worktrees_with_tasks(git_project_with_worktree: dict):
    """
    Given: A project with existing worktrees
    Should: Return list of all worktrees with metadata
    """
    from api.main import app
    from api.services.worktree_service import WorktreeService

    # Configure service with test project
    service = WorktreeService.get_instance()
    service.set_project_dir(git_project_with_worktree["project_dir"])

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/projects/test-project-id/worktrees")

    assert response.status_code == 200
    data = response.json()
    assert len(data["worktrees"]) == 1
    worktree = data["worktrees"][0]
    assert worktree["specName"] == "001-test-task"
    assert worktree["branch"] == "auto-claude/001-test-task"
    assert worktree["baseBranch"] == "main"
    assert worktree["commitCount"] >= 1
    assert worktree["filesChanged"] >= 1


# =============================================================================
# GET /api/worktrees/{task_id}/status - Get Worktree Status
# =============================================================================


@pytest.mark.asyncio
async def test_get_status_returns_diff_info(git_project_with_worktree: dict):
    """
    Given: A task with an existing worktree
    Should: Return status with diff statistics
    """
    from api.main import app
    from api.services.worktree_service import WorktreeService

    service = WorktreeService.get_instance()
    service.set_project_dir(git_project_with_worktree["project_dir"])

    spec_name = git_project_with_worktree["spec_name"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/api/worktrees/{spec_name}/status")

    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert data["branch"] == f"auto-claude/{spec_name}"
    assert data["baseBranch"] == "main"
    assert data["commitCount"] >= 1
    assert data["filesChanged"] >= 1
    assert data["additions"] >= 0
    assert data["deletions"] >= 0


@pytest.mark.asyncio
async def test_get_status_nonexistent_worktree(git_project: Path):
    """
    Given: A task without a worktree
    Should: Return exists=False
    """
    from api.main import app
    from api.services.worktree_service import WorktreeService

    service = WorktreeService.get_instance()
    service.set_project_dir(git_project)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/worktrees/nonexistent-task/status")

    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is False


# =============================================================================
# GET /api/worktrees/{task_id}/diff - Get Worktree Diff
# =============================================================================


@pytest.mark.asyncio
async def test_get_diff_returns_file_changes(git_project_with_worktree: dict):
    """
    Given: A task with changes in worktree
    Should: Return list of changed files with status
    """
    from api.main import app
    from api.services.worktree_service import WorktreeService

    service = WorktreeService.get_instance()
    service.set_project_dir(git_project_with_worktree["project_dir"])

    spec_name = git_project_with_worktree["spec_name"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/api/worktrees/{spec_name}/diff")

    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert len(data["files"]) >= 1

    # Check file structure
    file_info = data["files"][0]
    assert "path" in file_info
    assert "status" in file_info
    assert file_info["status"] in ["added", "modified", "deleted", "renamed"]
    assert "additions" in file_info
    assert "deletions" in file_info


# =============================================================================
# GET /api/worktrees/{task_id}/merge/preview - Merge Preview
# =============================================================================


@pytest.mark.asyncio
async def test_merge_preview_shows_conflicts(git_project_with_worktree: dict):
    """
    Given: A worktree with changes
    Should: Return merge preview with conflict analysis
    """
    from api.main import app
    from api.services.worktree_service import WorktreeService

    service = WorktreeService.get_instance()
    service.set_project_dir(git_project_with_worktree["project_dir"])

    spec_name = git_project_with_worktree["spec_name"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/api/worktrees/{spec_name}/merge/preview")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "preview" in data
    preview = data["preview"]
    assert "files" in preview
    assert "conflicts" in preview
    assert "summary" in preview


# =============================================================================
# POST /api/worktrees/{task_id}/merge - Merge Worktree
# =============================================================================


@pytest.mark.asyncio
async def test_merge_applies_changes(git_project_with_worktree: dict):
    """
    Given: A worktree with committed changes
    When: Merge is requested
    Should: Merge changes to base branch
    """
    from api.main import app
    from api.services.worktree_service import WorktreeService

    service = WorktreeService.get_instance()
    service.set_project_dir(git_project_with_worktree["project_dir"])

    spec_name = git_project_with_worktree["spec_name"]
    project_dir = git_project_with_worktree["project_dir"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/api/worktrees/{spec_name}/merge",
            json={"noCommit": False},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["merged"] is True

    # Verify file exists in main branch
    assert (project_dir / "new_file.py").exists()


@pytest.mark.asyncio
async def test_merge_with_no_commit(git_project_with_worktree: dict):
    """
    Given: A worktree with committed changes
    When: Merge is requested with noCommit=True
    Should: Stage changes without committing
    """
    from api.main import app
    from api.services.worktree_service import WorktreeService

    service = WorktreeService.get_instance()
    service.set_project_dir(git_project_with_worktree["project_dir"])

    spec_name = git_project_with_worktree["spec_name"]
    project_dir = git_project_with_worktree["project_dir"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/api/worktrees/{spec_name}/merge",
            json={"noCommit": True},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["staged"] is True

    # Verify changes are staged but not committed
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    assert "new_file.py" in result.stdout


# =============================================================================
# POST /api/worktrees/{task_id}/discard - Discard Worktree
# =============================================================================


@pytest.mark.asyncio
async def test_discard_removes_worktree(git_project_with_worktree: dict):
    """
    Given: An existing worktree
    When: Discard is requested
    Should: Remove worktree and branch
    """
    from api.main import app
    from api.services.worktree_service import WorktreeService

    service = WorktreeService.get_instance()
    service.set_project_dir(git_project_with_worktree["project_dir"])

    spec_name = git_project_with_worktree["spec_name"]
    worktree_path = git_project_with_worktree["worktree_path"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(f"/api/worktrees/{spec_name}/discard")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Verify worktree is removed
    assert not worktree_path.exists()
