"""
Project Service
===============

Business logic for project management.
Uses in-memory storage for simplicity (can be replaced with file/DB).
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from api.models import (
    McpServersConfig,
    Project,
    ProjectEnvConfig,
    ProjectEnvConfigUpdate,
)


class ProjectService:
    """
    Service for managing projects.

    Uses in-memory storage for now. Projects are lost on restart.
    TODO: Persist to /data/projects.json in production.
    """

    _instance: "ProjectService | None" = None

    def __init__(self):
        self._projects: dict[str, Project] = {}
        self._env_configs: dict[str, ProjectEnvConfig] = {}

    @classmethod
    def get_instance(cls) -> "ProjectService":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = ProjectService()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None

    def list_projects(self) -> list[Project]:
        """List all projects."""
        return list(self._projects.values())

    def get_project(self, project_id: str) -> Project | None:
        """Get project by ID."""
        return self._projects.get(project_id)

    def get_project_by_path(self, path: str) -> Project | None:
        """Get project by path."""
        normalized = os.path.normpath(path)
        for project in self._projects.values():
            if os.path.normpath(project.path) == normalized:
                return project
        return None

    def create_project(self, path: str) -> Project:
        """
        Create a new project.

        Args:
            path: Absolute path to project directory

        Returns:
            Created project

        Raises:
            ValueError: If project with path already exists
        """
        # Check for duplicate
        if self.get_project_by_path(path):
            raise ValueError(f"Project already exists: {path}")

        # Create project
        project = Project(
            id=str(uuid.uuid4()),
            path=path,
            name=Path(path).name,
            created_at=datetime.utcnow(),
        )

        self._projects[project.id] = project
        return project

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id: Project ID to delete

        Returns:
            True if deleted, False if not found
        """
        if project_id in self._projects:
            del self._projects[project_id]
            self._env_configs.pop(project_id, None)
            return True
        return False

    def get_project_env(self, project_id: str) -> ProjectEnvConfig | None:
        """
        Get project environment configuration.

        Args:
            project_id: Project ID

        Returns:
            Environment config or None if project not found
        """
        if project_id not in self._projects:
            return None

        if project_id not in self._env_configs:
            self._env_configs[project_id] = ProjectEnvConfig()

        return self._env_configs[project_id]

    def update_project_env(
        self, project_id: str, updates: ProjectEnvConfigUpdate
    ) -> ProjectEnvConfig | None:
        """
        Update project environment configuration.

        Args:
            project_id: Project ID
            updates: Partial env config to merge

        Returns:
            Updated env config or None if project not found
        """
        if project_id not in self._projects:
            return None

        if project_id not in self._env_configs:
            self._env_configs[project_id] = ProjectEnvConfig()

        current = self._env_configs[project_id].model_dump()
        update_data = updates.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if value is not None:
                if key == "mcpServers" and isinstance(value, dict):
                    existing_mcp = current.get("mcpServers") or {}
                    if hasattr(existing_mcp, "model_dump"):
                        existing_mcp = existing_mcp.model_dump()
                    elif not isinstance(existing_mcp, dict):
                        existing_mcp = {}
                    merged_mcp = {**existing_mcp, **value}
                    current["mcpServers"] = merged_mcp
                else:
                    current[key] = value

        self._env_configs[project_id] = ProjectEnvConfig(**current)
        return self._env_configs[project_id]
