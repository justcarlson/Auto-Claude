"""
Git Operations Endpoints
========================

REST API for Git operations.
Supports branch listing, main branch detection, status checks, and initialization.
"""

from api.models import (
    GitBranch,
    GitBranchesResponse,
    GitInitResponse,
    GitMainBranchResponse,
    GitStatusResponse,
)
from api.services import get_git_service
from fastapi import APIRouter

router = APIRouter(tags=["git"])


# =============================================================================
# GET /api/projects/{project_id}/git/branches - List Branches
# =============================================================================


@router.get(
    "/api/projects/{project_id}/git/branches", response_model=GitBranchesResponse
)
async def list_branches(project_id: str) -> GitBranchesResponse:
    """
    List all branches in the project repository.

    Returns list of branches with metadata including current branch flag.
    """
    service = get_git_service()
    branch_infos = service.list_branches()

    branches = [GitBranch(name=b.name, current=b.current) for b in branch_infos]

    return GitBranchesResponse(branches=branches)


# =============================================================================
# GET /api/projects/{project_id}/git/main-branch - Detect Main Branch
# =============================================================================


@router.get(
    "/api/projects/{project_id}/git/main-branch", response_model=GitMainBranchResponse
)
async def detect_main_branch(project_id: str) -> GitMainBranchResponse:
    """
    Detect the main branch (main or master) of the repository.

    Returns the detected branch name and whether it was auto-detected.
    """
    service = get_git_service()
    main_branch = service.detect_main_branch()

    if main_branch:
        return GitMainBranchResponse(branch=main_branch, detected=True)
    else:
        return GitMainBranchResponse(branch="main", detected=False)


# =============================================================================
# GET /api/projects/{project_id}/git/status - Get Git Status
# =============================================================================


@router.get("/api/projects/{project_id}/git/status", response_model=GitStatusResponse)
async def get_git_status(project_id: str) -> GitStatusResponse:
    """
    Get the git status of the project repository.

    Returns whether directory is a repo, is dirty, current branch,
    and lists of untracked, modified, and staged files.
    """
    service = get_git_service()
    status = service.get_status()

    return GitStatusResponse(
        isRepo=status.is_repo,
        isDirty=status.is_dirty,
        branch=status.branch,
        untrackedFiles=status.untracked_files or [],
        modifiedFiles=status.modified_files or [],
        stagedFiles=status.staged_files or [],
    )


# =============================================================================
# POST /api/projects/{project_id}/git/init - Initialize Git Repository
# =============================================================================


@router.post("/api/projects/{project_id}/git/init", response_model=GitInitResponse)
async def init_git_repo(project_id: str) -> GitInitResponse:
    """
    Initialize a git repository in the project directory.

    Returns success status and whether repo was newly initialized
    or was already a repository.
    """
    service = get_git_service()
    success, was_new = service.init_repo()

    if success:
        if was_new:
            return GitInitResponse(
                success=True,
                initialized=True,
                alreadyRepo=False,
                message="Git repository initialized successfully",
            )
        else:
            return GitInitResponse(
                success=True,
                initialized=False,
                alreadyRepo=True,
                message="Directory is already a git repository",
            )
    else:
        return GitInitResponse(
            success=False,
            initialized=False,
            alreadyRepo=False,
            message="Failed to initialize git repository",
        )
