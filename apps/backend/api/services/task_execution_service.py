"""
Task Execution Service
======================

Business logic for task execution management.
Handles starting, stopping, and monitoring task processes.
"""

from api.models import (
    TaskRecoverResponse,
    TaskReviewResponse,
    TaskStartResponse,
    TaskStatus,
    TaskStopResponse,
)


class TaskExecutionService:
    """
    Service for managing task execution.

    Tracks running tasks and their process state.
    In web/Docker mode, this manages subprocess execution.
    """

    _instance: "TaskExecutionService | None" = None

    def __init__(self):
        # Track running task IDs -> process state
        self._running_tasks: dict[str, dict] = {}
        # Track task feedback from reviews
        self._task_feedback: dict[str, str] = {}

    @classmethod
    def get_instance(cls) -> "TaskExecutionService":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = TaskExecutionService()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None

    def start_task(
        self,
        task_id: str,
        parallel: bool | None = None,
        workers: int | None = None,
    ) -> TaskStartResponse:
        """
        Start a task execution.

        Args:
            task_id: ID of the task to start
            parallel: Whether to run in parallel mode
            workers: Number of worker processes

        Returns:
            TaskStartResponse with success status
        """
        # Mark task as running
        self._running_tasks[task_id] = {
            "status": "running",
            "parallel": parallel,
            "workers": workers,
        }

        return TaskStartResponse(
            success=True,
            taskId=task_id,
            status="running",
        )

    def stop_task(self, task_id: str) -> TaskStopResponse:
        """
        Stop a running task.

        Args:
            task_id: ID of the task to stop

        Returns:
            TaskStopResponse with success status
        """
        # Remove from running tasks
        if task_id in self._running_tasks:
            del self._running_tasks[task_id]

        return TaskStopResponse(
            success=True,
            taskId=task_id,
        )

    def submit_review(
        self,
        task_id: str,
        approved: bool,
        feedback: str | None = None,
    ) -> TaskReviewResponse:
        """
        Submit a review for a task.

        Args:
            task_id: ID of the task
            approved: Whether the review is approved
            feedback: Optional feedback if rejected

        Returns:
            TaskReviewResponse with new status
        """
        if approved:
            # Mark as done
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
            return TaskReviewResponse(
                success=True,
                status="done",
            )
        else:
            # Return to in_progress with feedback
            if feedback:
                self._task_feedback[task_id] = feedback
            return TaskReviewResponse(
                success=True,
                status="in_progress",
                feedback=feedback,
            )

    def update_status(self, task_id: str, status: str) -> str:
        """
        Update task status.

        Args:
            task_id: ID of the task
            status: New status value

        Returns:
            The new status

        Raises:
            ValueError: If status is invalid
        """
        # Validate status
        valid_statuses = [s.value for s in TaskStatus]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")

        # Update running state if needed
        if status in ["pending", "done", "failed"]:
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
        elif status in ["in_progress", "reviewing"]:
            if task_id not in self._running_tasks:
                self._running_tasks[task_id] = {"status": status}
            else:
                self._running_tasks[task_id]["status"] = status

        return status

    def is_running(self, task_id: str) -> bool:
        """
        Check if a task is running.

        Args:
            task_id: ID of the task

        Returns:
            True if task is running
        """
        return task_id in self._running_tasks

    def recover_task(
        self,
        task_id: str,
        target_status: str | None = None,
        auto_restart: bool = True,
    ) -> TaskRecoverResponse:
        """
        Recover a stuck task.

        Args:
            task_id: ID of the task
            target_status: Target status after recovery
            auto_restart: Whether to auto-restart

        Returns:
            TaskRecoverResponse with recovery details
        """
        # Default to pending if no target specified
        new_status = target_status or "pending"

        # Clear any stuck state
        if task_id in self._running_tasks:
            del self._running_tasks[task_id]

        auto_restarted = False
        if auto_restart:
            # Start the task again
            self.start_task(task_id)
            new_status = "in_progress"
            auto_restarted = True

        return TaskRecoverResponse(
            success=True,
            newStatus=new_status,
            message=f"Task recovered to {new_status}",
            autoRestarted=auto_restarted,
        )

    def get_feedback(self, task_id: str) -> str | None:
        """Get stored feedback for a task."""
        return self._task_feedback.get(task_id)
