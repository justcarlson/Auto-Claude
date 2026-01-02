"""
Task Service
============

Business logic for task management.
Tasks are nested under projects.
"""

import uuid
from datetime import datetime

from api.models import Task, TaskCreate, TaskUpdate


class TaskService:
    """
    Service for managing tasks within projects.

    Uses in-memory storage for now. Tasks are lost on restart.
    TODO: Persist to /data/projects/{id}/tasks.json in production.
    """

    _instance: "TaskService | None" = None

    def __init__(self):
        # Tasks stored by project_id -> task_id -> Task
        self._tasks: dict[str, dict[str, Task]] = {}

    @classmethod
    def get_instance(cls) -> "TaskService":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = TaskService()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None

    def _ensure_project_store(self, project_id: str) -> dict[str, Task]:
        """Ensure task storage exists for a project."""
        if project_id not in self._tasks:
            self._tasks[project_id] = {}
        return self._tasks[project_id]

    def list_tasks(self, project_id: str) -> list[Task]:
        """List all tasks for a project."""
        project_tasks = self._tasks.get(project_id, {})
        return list(project_tasks.values())

    def get_task(self, project_id: str, task_id: str) -> Task | None:
        """Get task by ID within a project."""
        project_tasks = self._tasks.get(project_id, {})
        return project_tasks.get(task_id)

    def create_task(self, project_id: str, data: TaskCreate) -> Task:
        """
        Create a new task in a project.

        Args:
            project_id: ID of the parent project
            data: Task creation data

        Returns:
            Created task
        """
        now = datetime.utcnow()
        task = Task(
            id=str(uuid.uuid4()),
            project_id=project_id,
            title=data.title,
            description=data.description,
            status="pending",
            created_at=now,
            updated_at=now,
        )

        project_tasks = self._ensure_project_store(project_id)
        project_tasks[task.id] = task
        return task

    def update_task(
        self, project_id: str, task_id: str, data: TaskUpdate
    ) -> Task | None:
        """
        Update a task.

        Args:
            project_id: ID of the parent project
            task_id: ID of the task to update
            data: Fields to update

        Returns:
            Updated task or None if not found
        """
        task = self.get_task(project_id, task_id)
        if not task:
            return None

        # Update fields if provided
        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if value is not None:
                setattr(task, field, value)

        # Always update timestamp
        task.updated_at = datetime.utcnow()

        return task

    def delete_task(self, project_id: str, task_id: str) -> bool:
        """
        Delete a task.

        Args:
            project_id: ID of the parent project
            task_id: ID of the task to delete

        Returns:
            True if deleted, False if not found
        """
        project_tasks = self._tasks.get(project_id, {})
        if task_id in project_tasks:
            del project_tasks[task_id]
            return True
        return False

    def delete_tasks_for_project(self, project_id: str) -> int:
        """
        Delete all tasks for a project.

        Args:
            project_id: ID of the project

        Returns:
            Number of tasks deleted
        """
        if project_id in self._tasks:
            count = len(self._tasks[project_id])
            del self._tasks[project_id]
            return count
        return 0
