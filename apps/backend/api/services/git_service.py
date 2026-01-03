"""
Git Service
============

Web API service for Git operations.
Provides branch listing, main branch detection, status checks, and initialization.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BranchInfo:
    """Information about a git branch."""

    name: str
    current: bool = False


@dataclass
class GitStatus:
    """Git repository status information."""

    is_repo: bool
    is_dirty: bool = False
    branch: str | None = None
    untracked_files: list[str] | None = None
    modified_files: list[str] | None = None
    staged_files: list[str] | None = None


class GitService:
    """
    Singleton service for git operations.

    Provides a singleton pattern for API route access to git
    operations without requiring a full worktree manager.
    """

    _instance: "GitService | None" = None

    def __init__(self):
        self._project_dir: Path | None = None

    @classmethod
    def get_instance(cls) -> "GitService":
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
        Set the project directory for git operations.

        Args:
            project_dir: Path to the project root
        """
        self._project_dir = project_dir

    def _get_project_dir(self) -> Path:
        """Get the project directory, raising if not configured."""
        if self._project_dir is None:
            raise RuntimeError("GitService not configured. Call set_project_dir first.")
        return self._project_dir

    def _run_git(
        self, args: list[str], cwd: Path | None = None
    ) -> subprocess.CompletedProcess:
        """Run a git command and return the result."""
        return subprocess.run(
            ["git"] + args,
            cwd=cwd or self._get_project_dir(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def is_git_repo(self) -> bool:
        """Check if the project directory is a git repository."""
        project_dir = self._get_project_dir()
        result = self._run_git(["rev-parse", "--git-dir"], cwd=project_dir)
        return result.returncode == 0

    def list_branches(self) -> list[BranchInfo]:
        """
        List all branches in the repository.

        Returns:
            List of BranchInfo with name and current flag
        """
        result = self._run_git(["branch", "--list"])
        if result.returncode != 0:
            return []

        branches = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            current = line.startswith("*")
            name = line.lstrip("* ").strip()
            if name:
                branches.append(BranchInfo(name=name, current=current))

        return branches

    def detect_main_branch(self) -> str | None:
        """
        Detect the main branch (main or master).

        Returns:
            'main' or 'master' if found, None otherwise
        """
        # Check for 'main' first
        result = self._run_git(["rev-parse", "--verify", "main"])
        if result.returncode == 0:
            return "main"

        # Check for 'master'
        result = self._run_git(["rev-parse", "--verify", "master"])
        if result.returncode == 0:
            return "master"

        # Fall back to current branch
        result = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if result.returncode == 0:
            return result.stdout.strip()

        return None

    def get_current_branch(self) -> str | None:
        """Get the current branch name."""
        result = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    def get_status(self) -> GitStatus:
        """
        Get the git status of the repository.

        Returns:
            GitStatus with is_repo, is_dirty, branch, and file lists
        """
        project_dir = self._get_project_dir()

        # Check if it's a repo
        if not self.is_git_repo():
            return GitStatus(is_repo=False)

        branch = self.get_current_branch()

        # Get status
        result = self._run_git(["status", "--porcelain"], cwd=project_dir)
        if result.returncode != 0:
            return GitStatus(is_repo=True, branch=branch)

        untracked = []
        modified = []
        staged = []

        # Split on newlines, don't strip() the whole string as it removes
        # the leading space which is part of the git status format
        for line in result.stdout.split("\n"):
            # Strip only trailing whitespace, preserve leading status chars
            line = line.rstrip()
            if not line:
                continue

            # Status is first 2 characters, then a space, then the path
            # XY path where X is staged status, Y is working tree status
            if len(line) < 4:
                continue

            index_status = line[0]  # Staged status
            worktree_status = line[1]  # Working tree status
            filepath = line[3:].strip()

            if not filepath:
                continue

            # Check for untracked files (both chars are ?)
            if index_status == "?" and worktree_status == "?":
                untracked.append(filepath)
            else:
                # Check staged changes
                if index_status in "AMDRC":
                    staged.append(filepath)
                # Check working tree changes
                if worktree_status in "MD":
                    modified.append(filepath)

        is_dirty = bool(untracked or modified or staged)

        return GitStatus(
            is_repo=True,
            is_dirty=is_dirty,
            branch=branch,
            untracked_files=untracked,
            modified_files=modified,
            staged_files=staged,
        )

    def init_repo(self) -> tuple[bool, bool]:
        """
        Initialize a git repository.

        Returns:
            Tuple of (success, was_new_repo)
            - success: Whether operation succeeded
            - was_new_repo: True if repo was newly created, False if already existed
        """
        project_dir = self._get_project_dir()

        # Check if already a repo
        if self.is_git_repo():
            return (True, False)

        # Initialize
        result = self._run_git(["init"], cwd=project_dir)
        if result.returncode == 0:
            return (True, True)

        return (False, False)

    @property
    def project_dir(self) -> Path | None:
        """Get the current project directory."""
        return self._project_dir


def get_git_service() -> GitService:
    """Dependency injection helper for FastAPI."""
    return GitService.get_instance()
