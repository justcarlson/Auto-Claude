#!/usr/bin/env python3
"""
Git Operations Endpoints Tests
==============================

TDD tests for the /api/projects/{id}/git endpoints.
Tests written BEFORE implementation to drive development.
"""

import subprocess
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def git_project(tmp_path: Path):
    """
    Create a temporary git project with initial commit on 'main' branch.
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
def git_project_with_master(tmp_path: Path):
    """
    Create a temporary git project with 'master' as the main branch.
    """
    project_dir = tmp_path / "test-project-master"
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

    # Rename default branch to master
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip() != "master":
        subprocess.run(
            ["git", "branch", "-m", result.stdout.strip(), "master"],
            cwd=project_dir,
            capture_output=True,
        )

    return project_dir


@pytest.fixture
def git_project_with_branches(git_project: Path):
    """
    Create a git project with multiple branches.
    """
    # Create feature branches
    subprocess.run(
        ["git", "branch", "feature/auth"],
        cwd=git_project,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "branch", "feature/api"],
        cwd=git_project,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "branch", "develop"],
        cwd=git_project,
        check=True,
        capture_output=True,
    )

    return git_project


@pytest.fixture
def non_git_project(tmp_path: Path):
    """
    Create a regular directory that is NOT a git repository.
    """
    project_dir = tmp_path / "not-a-git-repo"
    project_dir.mkdir()
    (project_dir / "README.md").write_text("# Not a git repo\n")
    return project_dir


@pytest.fixture(autouse=True)
def isolated_git_service(tmp_path: Path):
    """Ensure each test uses isolated git service."""
    from api.services.git_service import GitService

    # Reset git service for fresh state
    GitService.reset()

    yield

    # Cleanup after test
    GitService.reset()


# =============================================================================
# GET /api/projects/{id}/git/branches - List Branches
# =============================================================================


@pytest.mark.asyncio
async def test_get_branches_lists_all(git_project_with_branches: Path):
    """
    Given: A project with multiple branches
    Should: Return list of all branches
    """
    from api.main import app
    from api.services.git_service import GitService

    service = GitService.get_instance()
    service.set_project_dir(git_project_with_branches)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/projects/test-project-id/git/branches")

    assert response.status_code == 200
    data = response.json()
    assert "branches" in data
    assert isinstance(data["branches"], list)
    assert len(data["branches"]) >= 4  # main + 3 created branches

    # Check branch structure
    branch_names = [b["name"] for b in data["branches"]]
    assert "main" in branch_names
    assert "feature/auth" in branch_names
    assert "feature/api" in branch_names
    assert "develop" in branch_names

    # Check that current branch is marked
    current_branches = [b for b in data["branches"] if b.get("current")]
    assert len(current_branches) == 1
    assert current_branches[0]["name"] == "main"


# =============================================================================
# GET /api/projects/{id}/git/main-branch - Detect Main Branch
# =============================================================================


@pytest.mark.asyncio
async def test_detect_main_branch_main(git_project: Path):
    """
    Given: A project with 'main' branch
    Should: Return 'main' as the main branch
    """
    from api.main import app
    from api.services.git_service import GitService

    service = GitService.get_instance()
    service.set_project_dir(git_project)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/projects/test-project-id/git/main-branch")

    assert response.status_code == 200
    data = response.json()
    assert data["branch"] == "main"
    assert data["detected"] is True


@pytest.mark.asyncio
async def test_detect_main_branch_master(git_project_with_master: Path):
    """
    Given: A project with 'master' branch (no 'main')
    Should: Return 'master' as the main branch
    """
    from api.main import app
    from api.services.git_service import GitService

    service = GitService.get_instance()
    service.set_project_dir(git_project_with_master)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/projects/test-project-id/git/main-branch")

    assert response.status_code == 200
    data = response.json()
    assert data["branch"] == "master"
    assert data["detected"] is True


# =============================================================================
# GET /api/projects/{id}/git/status - Check Status
# =============================================================================


@pytest.mark.asyncio
async def test_check_status_clean(git_project: Path):
    """
    Given: A project with no uncommitted changes
    Should: Return clean status
    """
    from api.main import app
    from api.services.git_service import GitService

    service = GitService.get_instance()
    service.set_project_dir(git_project)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/projects/test-project-id/git/status")

    assert response.status_code == 200
    data = response.json()
    assert data["isRepo"] is True
    assert data["isDirty"] is False
    assert data["branch"] == "main"
    assert data["untrackedFiles"] == []
    assert data["modifiedFiles"] == []
    assert data["stagedFiles"] == []


@pytest.mark.asyncio
async def test_check_status_dirty(git_project: Path):
    """
    Given: A project with uncommitted changes
    Should: Return dirty status with details
    """
    from api.main import app
    from api.services.git_service import GitService

    # Make some changes
    (git_project / "new_file.py").write_text("# New file\n")
    (git_project / "README.md").write_text("# Modified\n")

    service = GitService.get_instance()
    service.set_project_dir(git_project)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/projects/test-project-id/git/status")

    assert response.status_code == 200
    data = response.json()
    assert data["isRepo"] is True
    assert data["isDirty"] is True
    assert data["branch"] == "main"
    assert "new_file.py" in data["untrackedFiles"]
    assert "README.md" in data["modifiedFiles"]


# =============================================================================
# POST /api/projects/{id}/git/init - Initialize Git
# =============================================================================


@pytest.mark.asyncio
async def test_initialize_git_new_repo(non_git_project: Path):
    """
    Given: A directory that is not a git repo
    When: Git init is requested
    Should: Initialize the repo and return success
    """
    from api.main import app
    from api.services.git_service import GitService

    service = GitService.get_instance()
    service.set_project_dir(non_git_project)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/projects/test-project-id/git/init")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["initialized"] is True

    # Verify .git directory was created
    assert (non_git_project / ".git").exists()


@pytest.mark.asyncio
async def test_initialize_git_already_initialized(git_project: Path):
    """
    Given: A directory that is already a git repo
    When: Git init is requested
    Should: Return success but indicate already initialized
    """
    from api.main import app
    from api.services.git_service import GitService

    service = GitService.get_instance()
    service.set_project_dir(git_project)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/projects/test-project-id/git/init")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["initialized"] is False  # Already was a repo
    assert data["alreadyRepo"] is True
