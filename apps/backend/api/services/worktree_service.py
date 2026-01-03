"""
Worktree Service
================

Web API service for Git worktree management.
Wraps the core WorktreeManager for API layer access.
"""

from pathlib import Path

from core.worktree import WorktreeInfo, WorktreeManager


class WorktreeService:
    """
    Singleton service for worktree operations.

    Provides a singleton pattern for API route access to worktree
    operations. Wraps the core WorktreeManager.
    """

    _instance: "WorktreeService | None" = None

    def __init__(self):
        self._project_dir: Path | None = None
        self._manager: WorktreeManager | None = None

    @classmethod
    def get_instance(cls) -> "WorktreeService":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance. Used for testing."""
        cls._instance = None

    def set_project_dir(self, project_dir: Path) -> None:
        """
        Set the project directory for worktree operations.

        Args:
            project_dir: Path to the git project root
        """
        self._project_dir = project_dir
        self._manager = WorktreeManager(project_dir)
        self._manager.setup()

    def _get_manager(self) -> WorktreeManager:
        """Get the worktree manager, raising if not configured."""
        if self._manager is None:
            raise RuntimeError(
                "WorktreeService not configured. Call set_project_dir first."
            )
        return self._manager

    def list_worktrees(self) -> list[WorktreeInfo]:
        """
        List all spec worktrees in the project.

        Returns:
            List of WorktreeInfo for each worktree
        """
        manager = self._get_manager()
        return manager.list_all_worktrees()

    def get_worktree_info(self, spec_name: str) -> WorktreeInfo | None:
        """
        Get info about a specific worktree.

        Args:
            spec_name: The spec folder name (e.g., "001-test-task")

        Returns:
            WorktreeInfo or None if not found
        """
        manager = self._get_manager()
        return manager.get_worktree_info(spec_name)

    def get_changed_files(self, spec_name: str) -> list[tuple[str, str]]:
        """
        Get list of changed files in a worktree.

        Args:
            spec_name: The spec folder name

        Returns:
            List of (status, path) tuples where status is A/M/D/R
        """
        manager = self._get_manager()
        return manager.get_changed_files(spec_name)

    def get_change_summary(self, spec_name: str) -> dict:
        """
        Get summary of changes in a worktree.

        Args:
            spec_name: The spec folder name

        Returns:
            Dict with new_files, modified_files, deleted_files counts
        """
        manager = self._get_manager()
        return manager.get_change_summary(spec_name)

    def merge_worktree(
        self, spec_name: str, delete_after: bool = False, no_commit: bool = False
    ) -> bool:
        """
        Merge a worktree branch back to base branch.

        Args:
            spec_name: The spec folder name
            delete_after: Whether to remove worktree and branch after merge
            no_commit: If True, stage changes but don't commit

        Returns:
            True if merge succeeded
        """
        manager = self._get_manager()
        return manager.merge_worktree(
            spec_name, delete_after=delete_after, no_commit=no_commit
        )

    def remove_worktree(self, spec_name: str, delete_branch: bool = True) -> None:
        """
        Remove a worktree and optionally its branch.

        Args:
            spec_name: The spec folder name
            delete_branch: Whether to also delete the branch
        """
        manager = self._get_manager()
        manager.remove_worktree(spec_name, delete_branch=delete_branch)

    def worktree_exists(self, spec_name: str) -> bool:
        """
        Check if a worktree exists for a spec.

        Args:
            spec_name: The spec folder name

        Returns:
            True if worktree exists
        """
        manager = self._get_manager()
        return manager.worktree_exists(spec_name)

    @property
    def project_dir(self) -> Path | None:
        """Get the current project directory."""
        return self._project_dir

    @property
    def base_branch(self) -> str | None:
        """Get the base branch name."""
        if self._manager:
            return self._manager.base_branch
        return None


def get_worktree_service() -> WorktreeService:
    """Dependency injection helper for FastAPI."""
    return WorktreeService.get_instance()
