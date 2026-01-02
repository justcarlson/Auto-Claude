"""
API Models (Pydantic)
=====================

Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import Optional
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

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class Task(BaseModel):
    """Response model for a task."""

    id: str = Field(..., description="Unique task identifier")
    project_id: str = Field(..., description="Parent project ID")
    title: str
    description: str
    status: str = Field(default="pending")
    spec_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
