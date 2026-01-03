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
