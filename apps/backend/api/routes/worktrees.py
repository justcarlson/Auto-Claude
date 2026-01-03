"""
Worktree Endpoints
==================

REST API for Git worktree management.
Supports listing, status, diff, merge, and discard operations.
"""

from api.models import (
    MergeConflict,
    MergePreview,
    MergeStats,
    WorktreeDiffFile,
    WorktreeDiffResponse,
    WorktreeDiscardResponse,
    WorktreeListItem,
    WorktreeListResponse,
    WorktreeMergeRequest,
    WorktreeMergeResponse,
    WorktreeStatusResponse,
)
from api.services import get_worktree_service
from fastapi import APIRouter

router = APIRouter(tags=["worktrees"])


# =============================================================================
# GET /api/projects/{project_id}/worktrees - List Worktrees
# =============================================================================


@router.get("/api/projects/{project_id}/worktrees", response_model=WorktreeListResponse)
async def list_worktrees(project_id: str) -> WorktreeListResponse:
    """
    List all spec worktrees for a project.

    Returns list of worktrees with metadata including branch, stats, etc.
    """
    service = get_worktree_service()
    worktrees = service.list_worktrees()

    items = [
        WorktreeListItem(
            specName=w.spec_name,
            path=str(w.path),
            branch=w.branch,
            baseBranch=w.base_branch,
            commitCount=w.commit_count,
            filesChanged=w.files_changed,
            additions=w.additions,
            deletions=w.deletions,
        )
        for w in worktrees
    ]

    return WorktreeListResponse(worktrees=items)


# =============================================================================
# GET /api/worktrees/{task_id}/status - Get Worktree Status
# =============================================================================


@router.get("/api/worktrees/{task_id}/status", response_model=WorktreeStatusResponse)
async def get_worktree_status(task_id: str) -> WorktreeStatusResponse:
    """
    Get status of a specific worktree.

    Returns worktree existence, branch info, and change statistics.
    The task_id is treated as the spec name.
    """
    service = get_worktree_service()
    info = service.get_worktree_info(task_id)

    if not info:
        return WorktreeStatusResponse(exists=False)

    return WorktreeStatusResponse(
        exists=True,
        worktreePath=str(info.path),
        branch=info.branch,
        baseBranch=info.base_branch,
        commitCount=info.commit_count,
        filesChanged=info.files_changed,
        additions=info.additions,
        deletions=info.deletions,
    )


# =============================================================================
# GET /api/worktrees/{task_id}/diff - Get Worktree Diff
# =============================================================================


def _status_to_label(status: str) -> str:
    """Convert git status letter to human-readable label."""
    status_map = {
        "A": "added",
        "M": "modified",
        "D": "deleted",
        "R": "renamed",
    }
    return status_map.get(status, "modified")


@router.get("/api/worktrees/{task_id}/diff", response_model=WorktreeDiffResponse)
async def get_worktree_diff(task_id: str) -> WorktreeDiffResponse:
    """
    Get detailed diff for a worktree.

    Returns list of changed files with their status and line changes.
    """
    service = get_worktree_service()
    changed_files = service.get_changed_files(task_id)
    summary = service.get_change_summary(task_id)

    files = [
        WorktreeDiffFile(
            path=path,
            status=_status_to_label(status),
            additions=0,  # Per-file stats not available from basic git diff
            deletions=0,
        )
        for status, path in changed_files
    ]

    summary_text = (
        f"{summary.get('new_files', 0)} new, "
        f"{summary.get('modified_files', 0)} modified, "
        f"{summary.get('deleted_files', 0)} deleted"
    )

    return WorktreeDiffResponse(files=files, summary=summary_text)


# =============================================================================
# GET /api/worktrees/{task_id}/merge/preview - Merge Preview
# =============================================================================


@router.get(
    "/api/worktrees/{task_id}/merge/preview", response_model=WorktreeMergeResponse
)
async def get_merge_preview(task_id: str) -> WorktreeMergeResponse:
    """
    Preview merge results without actually merging.

    Returns potential conflicts and merge statistics.
    """
    service = get_worktree_service()
    info = service.get_worktree_info(task_id)

    if not info:
        return WorktreeMergeResponse(
            success=False,
            message=f"No worktree found for {task_id}",
        )

    # Get file changes for preview
    changed_files = service.get_changed_files(task_id)
    summary = service.get_change_summary(task_id)

    # Build preview response
    file_paths = [path for _, path in changed_files]
    stats = MergeStats(
        totalFiles=len(file_paths),
        conflictFiles=0,  # Basic preview doesn't detect conflicts
        totalConflicts=0,
        autoMergeable=len(file_paths),
    )

    preview = MergePreview(
        files=file_paths,
        conflicts=[],  # Would need full merge analysis for conflicts
        summary=stats,
    )

    return WorktreeMergeResponse(
        success=True,
        message="Merge preview generated",
        preview=preview,
    )


# =============================================================================
# POST /api/worktrees/{task_id}/merge - Merge Worktree
# =============================================================================


@router.post("/api/worktrees/{task_id}/merge", response_model=WorktreeMergeResponse)
async def merge_worktree(
    task_id: str, request: WorktreeMergeRequest | None = None
) -> WorktreeMergeResponse:
    """
    Merge a worktree branch into the base branch.

    If noCommit=True, stages changes without committing.
    """
    service = get_worktree_service()
    no_commit = request.noCommit if request else False

    try:
        success = service.merge_worktree(task_id, no_commit=no_commit)

        if success:
            return WorktreeMergeResponse(
                success=True,
                message="Merge completed successfully"
                if not no_commit
                else "Changes staged",
                merged=not no_commit,
                staged=no_commit,
                projectPath=str(service.project_dir) if service.project_dir else None,
            )
        else:
            return WorktreeMergeResponse(
                success=False,
                message="Merge failed - conflicts detected",
                merged=False,
            )
    except Exception as e:
        return WorktreeMergeResponse(
            success=False,
            message=str(e),
            merged=False,
        )


# =============================================================================
# POST /api/worktrees/{task_id}/discard - Discard Worktree
# =============================================================================


@router.post("/api/worktrees/{task_id}/discard", response_model=WorktreeDiscardResponse)
async def discard_worktree(task_id: str) -> WorktreeDiscardResponse:
    """
    Discard a worktree and its branch.

    Permanently removes the worktree and deletes the associated branch.
    """
    service = get_worktree_service()

    if not service.worktree_exists(task_id):
        return WorktreeDiscardResponse(
            success=False,
            message=f"No worktree found for {task_id}",
        )

    try:
        service.remove_worktree(task_id, delete_branch=True)
        return WorktreeDiscardResponse(
            success=True,
            message=f"Worktree {task_id} discarded successfully",
        )
    except Exception as e:
        return WorktreeDiscardResponse(
            success=False,
            message=str(e),
        )
