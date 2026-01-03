"""
Task Execution API Endpoints
============================

Endpoints for task execution control:
- Start/stop task execution
- Submit reviews
- Update status
- Check running state
- Recover stuck tasks
"""

from api.models import (
    Task,
    TaskRecoverRequest,
    TaskRecoverResponse,
    TaskReviewRequest,
    TaskReviewResponse,
    TaskRunningResponse,
    TaskStartRequest,
    TaskStartResponse,
    TaskStatusUpdateRequest,
    TaskStopResponse,
)
from api.services import TaskExecutionService, TaskService
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/tasks", tags=["task-execution"])


def get_task_service() -> TaskService:
    """Get task service instance."""
    return TaskService.get_instance()


def get_execution_service() -> TaskExecutionService:
    """Get task execution service instance."""
    return TaskExecutionService.get_instance()


def find_task(task_id: str) -> Task:
    """
    Find a task by ID across all projects.

    Args:
        task_id: Task ID to find

    Returns:
        Task if found

    Raises:
        HTTPException: 404 if task not found
    """
    task_service = get_task_service()

    # Search through all projects for the task
    for project_id, tasks in task_service._tasks.items():
        if task_id in tasks:
            return tasks[task_id]

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task not found: {task_id}",
    )


@router.post("/{task_id}/start", response_model=TaskStartResponse)
async def start_task(task_id: str, request: TaskStartRequest) -> TaskStartResponse:
    """
    Start execution of a task.

    Args:
        task_id: ID of the task to start
        request: Start options (parallel, workers)

    Returns:
        TaskStartResponse with execution state

    Raises:
        404: If task not found
    """
    # Verify task exists
    find_task(task_id)

    service = get_execution_service()
    return service.start_task(
        task_id,
        parallel=request.parallel,
        workers=request.workers,
    )


@router.post("/{task_id}/stop", response_model=TaskStopResponse)
async def stop_task(task_id: str) -> TaskStopResponse:
    """
    Stop execution of a task.

    Args:
        task_id: ID of the task to stop

    Returns:
        TaskStopResponse with result

    Raises:
        404: If task not found
    """
    # Verify task exists
    find_task(task_id)

    service = get_execution_service()
    return service.stop_task(task_id)


@router.post("/{task_id}/review", response_model=TaskReviewResponse)
async def submit_review(task_id: str, request: TaskReviewRequest) -> TaskReviewResponse:
    """
    Submit a review for a task.

    Args:
        task_id: ID of the task to review
        request: Review data (approved, feedback)

    Returns:
        TaskReviewResponse with new status

    Raises:
        404: If task not found
    """
    # Verify task exists
    find_task(task_id)

    service = get_execution_service()
    return service.submit_review(
        task_id,
        approved=request.approved,
        feedback=request.feedback,
    )


@router.put("/{task_id}/status", response_model=Task)
async def update_task_status(task_id: str, request: TaskStatusUpdateRequest) -> Task:
    """
    Update a task's status.

    Args:
        task_id: ID of the task
        request: New status value

    Returns:
        Updated task

    Raises:
        400: If status is invalid
        404: If task not found
    """
    # Find task and its project
    task_service = get_task_service()
    task = None
    project_id = None

    for pid, tasks in task_service._tasks.items():
        if task_id in tasks:
            task = tasks[task_id]
            project_id = pid
            break

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )

    # Validate and update status
    exec_service = get_execution_service()
    try:
        new_status = exec_service.update_status(task_id, request.status)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Update task model
    task.status = new_status
    return task


@router.get("/{task_id}/running", response_model=TaskRunningResponse)
async def check_task_running(task_id: str) -> TaskRunningResponse:
    """
    Check if a task is currently running.

    Args:
        task_id: ID of the task

    Returns:
        TaskRunningResponse with running state

    Raises:
        404: If task not found
    """
    # Verify task exists
    find_task(task_id)

    service = get_execution_service()
    return TaskRunningResponse(running=service.is_running(task_id))


@router.post("/{task_id}/recover", response_model=TaskRecoverResponse)
async def recover_task(
    task_id: str, request: TaskRecoverRequest
) -> TaskRecoverResponse:
    """
    Recover a stuck task.

    Args:
        task_id: ID of the task to recover
        request: Recovery options (targetStatus, autoRestart)

    Returns:
        TaskRecoverResponse with recovery details

    Raises:
        404: If task not found
    """
    # Verify task exists
    find_task(task_id)

    service = get_execution_service()
    return service.recover_task(
        task_id,
        target_status=request.targetStatus,
        auto_restart=request.autoRestart,
    )
