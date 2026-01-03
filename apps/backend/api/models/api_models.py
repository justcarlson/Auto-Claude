"""
API Models (Pydantic)
=====================

Pydantic models for request/response validation.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

# =============================================================================
# PROJECT MODELS
# =============================================================================


class ProjectCreate(BaseModel):
    """Request model for creating a project."""

    path: str = Field(..., description="Absolute path to the project directory")


class Project(BaseModel):
    """Response model for a project."""

    id: str = Field(..., description="Unique project identifier")
    path: str = Field(..., description="Absolute path to the project directory")
    name: str = Field(..., description="Project name (derived from path)")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# TASK MODELS
# =============================================================================


class TaskCreate(BaseModel):
    """Request model for creating a task."""

    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")


class TaskUpdate(BaseModel):
    """Request model for updating a task."""

    title: str | None = None
    description: str | None = None
    status: str | None = None


class Task(BaseModel):
    """Response model for a task."""

    id: str = Field(..., description="Unique task identifier")
    project_id: str = Field(..., description="Parent project ID")
    title: str
    description: str
    status: str = Field(default="pending")
    spec_path: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# TASK EXECUTION MODELS
# =============================================================================


class TaskStatus(str, Enum):
    """Valid task status values."""

    pending = "pending"
    in_progress = "in_progress"
    reviewing = "reviewing"
    done = "done"
    failed = "failed"
    stuck = "stuck"


class TaskStartRequest(BaseModel):
    """Request model for starting a task."""

    parallel: bool | None = Field(default=None, description="Run in parallel mode")
    workers: int | None = Field(default=None, description="Number of workers")


class TaskStartResponse(BaseModel):
    """Response model for starting a task."""

    success: bool
    taskId: str
    status: str


class TaskStopResponse(BaseModel):
    """Response model for stopping a task."""

    success: bool
    taskId: str


class TaskReviewRequest(BaseModel):
    """Request model for submitting a task review."""

    approved: bool = Field(..., description="Whether the review is approved")
    feedback: str | None = Field(default=None, description="Feedback if rejected")


class TaskReviewResponse(BaseModel):
    """Response model for task review."""

    success: bool
    status: str
    feedback: str | None = None


class TaskStatusUpdateRequest(BaseModel):
    """Request model for updating task status."""

    status: str = Field(..., description="New status value")


class TaskRunningResponse(BaseModel):
    """Response model for checking if task is running."""

    running: bool


class TaskRecoverRequest(BaseModel):
    """Request model for recovering a stuck task."""

    targetStatus: str | None = Field(
        default=None, description="Target status after recovery"
    )
    autoRestart: bool = Field(default=True, description="Auto-restart after recovery")


class TaskRecoverResponse(BaseModel):
    """Response model for task recovery."""

    success: bool
    newStatus: str
    message: str
    autoRestarted: bool = False


# =============================================================================
# SETTINGS MODELS
# =============================================================================


class ThemeType(str, Enum):
    """Valid theme values."""

    light = "light"
    dark = "dark"
    system = "system"


class AppSettings(BaseModel):
    """Application settings model."""

    theme: ThemeType = Field(default=ThemeType.system, description="UI theme")
    defaultModel: str | None = Field(default=None, description="Default Claude model")
    graphitiEnabled: bool | None = Field(
        default=None, description="Enable Graphiti memory"
    )


class AppSettingsUpdate(BaseModel):
    """Request model for updating settings (all fields optional)."""

    theme: ThemeType | None = None
    defaultModel: str | None = None
    graphitiEnabled: bool | None = None


class VersionResponse(BaseModel):
    """Response model for version endpoint."""

    version: str = Field(..., description="Application version")


# =============================================================================
# PROJECT ENVIRONMENT MODELS
# =============================================================================


class McpServersConfig(BaseModel):
    """MCP server configuration for a project."""

    context7Enabled: bool | None = Field(default=True)
    graphitiEnabled: bool | None = Field(default=None)
    linearMcpEnabled: bool | None = Field(default=None)
    electronEnabled: bool | None = Field(default=False)
    puppeteerEnabled: bool | None = Field(default=False)


class ProjectEnvConfig(BaseModel):
    """Project environment configuration."""

    claudeOAuthToken: str | None = Field(default=None)
    claudeAuthStatus: str = Field(default="not_configured")
    claudeTokenIsGlobal: bool | None = Field(default=None)

    autoBuildModel: str | None = Field(default=None)

    linearEnabled: bool = Field(default=False)
    linearApiKey: str | None = Field(default=None)
    linearTeamId: str | None = Field(default=None)
    linearProjectId: str | None = Field(default=None)
    linearRealtimeSync: bool | None = Field(default=None)

    githubEnabled: bool = Field(default=False)
    githubToken: str | None = Field(default=None)
    githubRepo: str | None = Field(default=None)
    githubAutoSync: bool | None = Field(default=None)
    githubAuthMethod: str | None = Field(default=None)

    gitlabEnabled: bool = Field(default=False)
    gitlabInstanceUrl: str | None = Field(default=None)
    gitlabToken: str | None = Field(default=None)
    gitlabProject: str | None = Field(default=None)
    gitlabAutoSync: bool | None = Field(default=None)

    defaultBranch: str | None = Field(default=None)

    graphitiEnabled: bool = Field(default=False)
    graphitiProviderConfig: dict | None = Field(default=None)
    openaiApiKey: str | None = Field(default=None)
    openaiKeyIsGlobal: bool | None = Field(default=None)
    graphitiDatabase: str | None = Field(default=None)
    graphitiDbPath: str | None = Field(default=None)

    enableFancyUi: bool = Field(default=True)

    mcpServers: McpServersConfig | None = Field(default=None)
    agentMcpOverrides: dict | None = Field(default=None)
    customMcpServers: list | None = Field(default=None)


class ProjectEnvConfigUpdate(BaseModel):
    """Request model for updating project env config (all fields optional)."""

    claudeOAuthToken: str | None = None
    claudeAuthStatus: str | None = None
    claudeTokenIsGlobal: bool | None = None

    autoBuildModel: str | None = None

    linearEnabled: bool | None = None
    linearApiKey: str | None = None
    linearTeamId: str | None = None
    linearProjectId: str | None = None
    linearRealtimeSync: bool | None = None

    githubEnabled: bool | None = None
    githubToken: str | None = None
    githubRepo: str | None = None
    githubAutoSync: bool | None = None
    githubAuthMethod: str | None = None

    gitlabEnabled: bool | None = None
    gitlabInstanceUrl: str | None = None
    gitlabToken: str | None = None
    gitlabProject: str | None = None
    gitlabAutoSync: bool | None = None

    defaultBranch: str | None = None

    graphitiEnabled: bool | None = None
    graphitiProviderConfig: dict | None = None
    openaiApiKey: str | None = None
    openaiKeyIsGlobal: bool | None = None
    graphitiDatabase: str | None = None
    graphitiDbPath: str | None = None

    enableFancyUi: bool | None = None

    mcpServers: dict | None = None
    agentMcpOverrides: dict | None = None
    customMcpServers: list | None = None


# =============================================================================
# TERMINAL MODELS
# =============================================================================


class TerminalCreateRequest(BaseModel):
    """Request model for creating a terminal session."""

    cwd: str | None = Field(default=None, description="Working directory")
    shell: str | None = Field(default=None, description="Shell executable path")
    cols: int = Field(default=80, description="Terminal columns")
    rows: int = Field(default=24, description="Terminal rows")


class TerminalCreateResponse(BaseModel):
    """Response model for terminal creation."""

    session_id: str = Field(..., description="Unique terminal session ID")


class TerminalSession(BaseModel):
    """Response model for a terminal session."""

    id: str = Field(..., description="Terminal session ID")
    cwd: str = Field(..., description="Working directory")
    alive: bool = Field(..., description="Whether the terminal is still running")


class TerminalSessionsResponse(BaseModel):
    """Response model for listing terminal sessions."""

    sessions: list[TerminalSession] = Field(
        default_factory=list, description="Active terminal sessions"
    )


class TerminalAliveResponse(BaseModel):
    """Response model for checking terminal alive status."""

    alive: bool = Field(..., description="Whether the terminal is running")


# =============================================================================
# WORKTREE MODELS
# =============================================================================


class WorktreeStatusResponse(BaseModel):
    """Response model for worktree status."""

    exists: bool = Field(..., description="Whether worktree exists for this task")
    worktreePath: str | None = Field(default=None, description="Path to worktree")
    branch: str | None = Field(default=None, description="Branch name")
    baseBranch: str | None = Field(default=None, description="Base branch name")
    commitCount: int | None = Field(default=None, description="Number of commits ahead")
    filesChanged: int | None = Field(
        default=None, description="Number of files changed"
    )
    additions: int | None = Field(default=None, description="Number of lines added")
    deletions: int | None = Field(default=None, description="Number of lines deleted")


class WorktreeDiffFile(BaseModel):
    """Model for a file in a diff."""

    path: str = Field(..., description="File path relative to project root")
    status: str = Field(..., description="added, modified, deleted, or renamed")
    additions: int = Field(default=0, description="Lines added")
    deletions: int = Field(default=0, description="Lines deleted")


class WorktreeDiffResponse(BaseModel):
    """Response model for worktree diff."""

    files: list[WorktreeDiffFile] = Field(
        default_factory=list, description="Changed files"
    )
    summary: str = Field(default="", description="Summary of changes")


class MergeConflict(BaseModel):
    """Model for a merge conflict."""

    file: str = Field(..., description="File with conflict")
    location: str = Field(default="", description="Conflict location")
    tasks: list[str] = Field(default_factory=list, description="Tasks involved")
    severity: str = Field(default="none", description="Conflict severity")
    canAutoMerge: bool = Field(default=False, description="Can be auto-merged")
    strategy: str | None = Field(default=None, description="Merge strategy")
    reason: str = Field(default="", description="Conflict reason")
    type: str | None = Field(default=None, description="Conflict type")


class GitConflictInfo(BaseModel):
    """Model for Git-level conflict information."""

    hasConflicts: bool = Field(default=False)
    conflictingFiles: list[str] = Field(default_factory=list)
    needsRebase: bool = Field(default=False)
    commitsBehind: int = Field(default=0)
    baseBranch: str = Field(default="")
    specBranch: str = Field(default="")


class MergeStats(BaseModel):
    """Model for merge statistics."""

    totalFiles: int = Field(default=0)
    conflictFiles: int = Field(default=0)
    totalConflicts: int = Field(default=0)
    autoMergeable: int = Field(default=0)
    aiResolved: int | None = Field(default=None)
    humanRequired: int | None = Field(default=None)
    hasGitConflicts: bool | None = Field(default=None)


class MergePreview(BaseModel):
    """Model for merge preview results."""

    files: list[str] = Field(default_factory=list)
    conflicts: list[MergeConflict] = Field(default_factory=list)
    summary: MergeStats = Field(default_factory=MergeStats)
    gitConflicts: GitConflictInfo | None = Field(default=None)


class WorktreeMergeRequest(BaseModel):
    """Request model for merging a worktree."""

    noCommit: bool = Field(
        default=False, description="Stage changes without committing"
    )


class WorktreeMergeResponse(BaseModel):
    """Response model for worktree merge."""

    success: bool = Field(..., description="Whether merge succeeded")
    message: str = Field(..., description="Status message")
    merged: bool | None = Field(default=None, description="Whether changes were merged")
    conflictFiles: list[str] | None = Field(
        default=None, description="Files with conflicts"
    )
    staged: bool | None = Field(default=None, description="Whether changes are staged")
    alreadyStaged: bool | None = Field(
        default=None, description="Whether already staged"
    )
    projectPath: str | None = Field(default=None, description="Project path")
    suggestedCommitMessage: str | None = Field(
        default=None, description="AI-generated commit message"
    )
    conflicts: list[MergeConflict] | None = Field(default=None)
    stats: MergeStats | None = Field(default=None)
    gitConflicts: GitConflictInfo | None = Field(default=None)
    preview: MergePreview | None = Field(default=None)


class WorktreeDiscardResponse(BaseModel):
    """Response model for worktree discard."""

    success: bool = Field(..., description="Whether discard succeeded")
    message: str = Field(..., description="Status message")


class WorktreeListItem(BaseModel):
    """Model for a worktree list item."""

    specName: str = Field(..., description="Spec folder name")
    path: str = Field(..., description="Worktree path")
    branch: str = Field(..., description="Branch name")
    baseBranch: str = Field(..., description="Base branch name")
    commitCount: int = Field(default=0, description="Commits ahead")
    filesChanged: int = Field(default=0, description="Files changed")
    additions: int = Field(default=0, description="Lines added")
    deletions: int = Field(default=0, description="Lines deleted")


class WorktreeListResponse(BaseModel):
    """Response model for listing worktrees."""

    worktrees: list[WorktreeListItem] = Field(
        default_factory=list, description="List of worktrees"
    )


# =============================================================================
# GIT OPERATIONS MODELS
# =============================================================================


class GitBranch(BaseModel):
    """Model for a git branch."""

    name: str = Field(..., description="Branch name")
    current: bool = Field(
        default=False, description="Whether this is the current branch"
    )


class GitBranchesResponse(BaseModel):
    """Response model for listing branches."""

    branches: list[GitBranch] = Field(
        default_factory=list, description="List of branches"
    )


class GitMainBranchResponse(BaseModel):
    """Response model for detecting main branch."""

    branch: str = Field(..., description="Detected main branch name")
    detected: bool = Field(default=True, description="Whether branch was auto-detected")


class GitStatusResponse(BaseModel):
    """Response model for git status."""

    isRepo: bool = Field(..., description="Whether directory is a git repo")
    isDirty: bool = Field(
        default=False, description="Whether there are uncommitted changes"
    )
    branch: str | None = Field(default=None, description="Current branch name")
    untrackedFiles: list[str] = Field(
        default_factory=list, description="Untracked files"
    )
    modifiedFiles: list[str] = Field(default_factory=list, description="Modified files")
    stagedFiles: list[str] = Field(default_factory=list, description="Staged files")


class GitInitResponse(BaseModel):
    """Response model for git init."""

    success: bool = Field(..., description="Whether operation succeeded")
    initialized: bool = Field(
        default=False, description="Whether repo was newly initialized"
    )
    alreadyRepo: bool = Field(
        default=False, description="Whether directory was already a repo"
    )
    message: str | None = Field(default=None, description="Status message")


# =============================================================================
# FILESYSTEM MODELS
# =============================================================================


class FileNode(BaseModel):
    """Model for a file or directory node."""

    name: str = Field(..., description="File or directory name")
    path: str = Field(..., description="Path relative to project root")
    type: str = Field(..., description="'file' or 'directory'")
    size: int | None = Field(default=None, description="File size in bytes")


class DirectoryListResponse(BaseModel):
    """Response model for listing directory contents."""

    nodes: list[FileNode] = Field(
        default_factory=list, description="List of files and directories"
    )


class FileContentResponse(BaseModel):
    """Response model for reading file content."""

    path: str = Field(..., description="File path relative to project root")
    content: str | None = Field(default=None, description="File content (if text)")
    isBinary: bool = Field(default=False, description="Whether file is binary")
    size: int = Field(default=0, description="File size in bytes")
