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
