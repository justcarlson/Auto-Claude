"""
Task Logs Service
=================

Web API service for task log operations.
Provides access to task execution logs stored in spec directories.

SECURITY: All operations are sandboxed to the project directory.
Path traversal attacks are blocked.
"""

import json
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TaskLogEntry:
    """A single log entry."""

    timestamp: str
    type: (
        str  # text, tool_start, tool_end, phase_start, phase_end, error, success, info
    )
    content: str
    phase: str  # planning, coding, validation
    tool_name: str | None = None
    tool_input: str | None = None
    subtask_id: str | None = None
    session: int | None = None
    detail: str | None = None
    subphase: str | None = None
    collapsed: bool | None = None


@dataclass
class TaskPhaseLog:
    """Log data for a single phase."""

    phase: str  # planning, coding, validation
    status: str  # pending, active, completed, failed
    started_at: str | None
    completed_at: str | None
    entries: list[TaskLogEntry] = field(default_factory=list)


@dataclass
class TaskLogs:
    """Complete task logs structure."""

    spec_id: str
    created_at: str
    updated_at: str
    phases: dict[str, TaskPhaseLog] = field(default_factory=dict)


class PathTraversalError(Exception):
    """Raised when a path traversal attack is detected."""

    pass


class TaskLogsNotFoundError(Exception):
    """Raised when task logs are not found."""

    pass


class TaskLogsParseError(Exception):
    """Raised when task logs cannot be parsed."""

    pass


class TaskLogsService:
    """
    Singleton service for task log operations.

    All task IDs are validated to prevent traversal attacks.
    Operations are sandboxed to the configured project directory.
    """

    _instance: "TaskLogsService | None" = None

    def __init__(self):
        self._project_dir: Path | None = None

    @classmethod
    def get_instance(cls) -> "TaskLogsService":
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
        Set the project directory for task log operations.

        Args:
            project_dir: Path to the project root
        """
        self._project_dir = project_dir.resolve()

    def _get_project_dir(self) -> Path:
        """Get the project directory, raising if not configured."""
        if self._project_dir is None:
            raise RuntimeError(
                "TaskLogsService not configured. Call set_project_dir first."
            )
        return self._project_dir

    def _validate_task_id(self, task_id: str) -> str:
        """
        Validate and sanitize a task ID, ensuring it's safe.

        Args:
            task_id: Task/spec ID

        Returns:
            Sanitized task ID

        Raises:
            PathTraversalError: If task_id contains traversal patterns
        """
        # Decode URL-encoded characters
        decoded = urllib.parse.unquote(task_id)

        # Normalize path separators
        normalized = decoded.replace("\\", "/")

        # Block traversal patterns
        if ".." in normalized:
            raise PathTraversalError(f"Path traversal detected: {task_id}")

        # Block absolute paths
        if normalized.startswith("/"):
            raise PathTraversalError(f"Absolute path not allowed: {task_id}")

        # Block path separators in task ID
        if "/" in normalized:
            raise PathTraversalError(f"Path separators not allowed: {task_id}")

        return decoded

    def _find_spec_dir(self, task_id: str) -> Path:
        """
        Find the spec directory for a task.

        Args:
            task_id: Task/spec ID

        Returns:
            Path to spec directory

        Raises:
            TaskLogsNotFoundError: If spec directory not found
        """
        project_dir = self._get_project_dir()
        validated_id = self._validate_task_id(task_id)

        # Look in .auto-claude/specs/
        specs_dir = project_dir / ".auto-claude" / "specs"

        if not specs_dir.exists():
            raise TaskLogsNotFoundError(f"Specs directory not found")

        # Find spec directory matching task_id
        for spec_dir in specs_dir.iterdir():
            if spec_dir.is_dir() and spec_dir.name == validated_id:
                return spec_dir

        raise TaskLogsNotFoundError(f"Task not found: {task_id}")

    def get_logs(self, task_id: str) -> TaskLogs:
        """
        Get task logs for a task.

        Args:
            task_id: Task/spec ID

        Returns:
            TaskLogs dataclass

        Raises:
            PathTraversalError: If task_id contains traversal patterns
            TaskLogsNotFoundError: If task or logs not found
            TaskLogsParseError: If logs cannot be parsed
        """
        spec_dir = self._find_spec_dir(task_id)
        logs_file = spec_dir / "task_logs.json"

        if not logs_file.exists():
            raise TaskLogsNotFoundError(f"No logs found for task: {task_id}")

        try:
            content = logs_file.read_text(encoding="utf-8")
            data = json.loads(content)
            return self._parse_logs(data)
        except json.JSONDecodeError as e:
            raise TaskLogsParseError(f"Failed to parse logs: {e}")

    def _parse_logs(self, data: dict[str, Any]) -> TaskLogs:
        """
        Parse raw JSON data into TaskLogs dataclass.

        Args:
            data: Raw JSON data

        Returns:
            TaskLogs dataclass
        """
        phases = {}

        for phase_name, phase_data in data.get("phases", {}).items():
            entries = []
            for entry_data in phase_data.get("entries", []):
                entry = TaskLogEntry(
                    timestamp=entry_data.get("timestamp", ""),
                    type=entry_data.get("type", "text"),
                    content=entry_data.get("content", ""),
                    phase=entry_data.get("phase", phase_name),
                    tool_name=entry_data.get("tool_name"),
                    tool_input=entry_data.get("tool_input"),
                    subtask_id=entry_data.get("subtask_id"),
                    session=entry_data.get("session"),
                    detail=entry_data.get("detail"),
                    subphase=entry_data.get("subphase"),
                    collapsed=entry_data.get("collapsed"),
                )
                entries.append(entry)

            phase_log = TaskPhaseLog(
                phase=phase_data.get("phase", phase_name),
                status=phase_data.get("status", "pending"),
                started_at=phase_data.get("started_at"),
                completed_at=phase_data.get("completed_at"),
                entries=entries,
            )
            phases[phase_name] = phase_log

        return TaskLogs(
            spec_id=data.get("spec_id", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            phases=phases,
        )

    def to_dict(self, logs: TaskLogs) -> dict[str, Any]:
        """
        Convert TaskLogs to dictionary for JSON serialization.

        Args:
            logs: TaskLogs dataclass

        Returns:
            Dictionary representation
        """
        phases = {}
        for phase_name, phase_log in logs.phases.items():
            entries = []
            for entry in phase_log.entries:
                entry_dict = {
                    "timestamp": entry.timestamp,
                    "type": entry.type,
                    "content": entry.content,
                    "phase": entry.phase,
                }
                if entry.tool_name is not None:
                    entry_dict["tool_name"] = entry.tool_name
                if entry.tool_input is not None:
                    entry_dict["tool_input"] = entry.tool_input
                if entry.subtask_id is not None:
                    entry_dict["subtask_id"] = entry.subtask_id
                if entry.session is not None:
                    entry_dict["session"] = entry.session
                if entry.detail is not None:
                    entry_dict["detail"] = entry.detail
                if entry.subphase is not None:
                    entry_dict["subphase"] = entry.subphase
                if entry.collapsed is not None:
                    entry_dict["collapsed"] = entry.collapsed
                entries.append(entry_dict)

            phases[phase_name] = {
                "phase": phase_log.phase,
                "status": phase_log.status,
                "started_at": phase_log.started_at,
                "completed_at": phase_log.completed_at,
                "entries": entries,
            }

        return {
            "spec_id": logs.spec_id,
            "created_at": logs.created_at,
            "updated_at": logs.updated_at,
            "phases": phases,
        }


def get_task_logs_service() -> TaskLogsService:
    """Dependency injection helper for FastAPI."""
    return TaskLogsService.get_instance()
