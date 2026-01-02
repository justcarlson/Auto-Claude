"""
Project Service
===============

Business logic for project management.
Uses in-memory storage for simplicity (can be replaced with file/DB).
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from api.models import Project


class ProjectService:
    """
    Service for managing projects.

    Uses in-memory storage for now. Projects are lost on restart.
    TODO: Persist to /data/projects.json in production.
    """

    _instance: Optional["ProjectService"] = None

    def __init__(self):
        self._projects: dict[str, Project] = {}

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

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        return self._projects.get(project_id)

    def get_project_by_path(self, path: str) -> Optional[Project]:
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
            return True
        return False
