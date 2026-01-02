"""
Tasks API Endpoints
===================

CRUD operations for task management within projects.
"""

from fastapi import APIRouter, HTTPException, Response, status

from api.models import Task, TaskCreate, TaskUpdate
from api.services import ProjectService, TaskService

router = APIRouter(prefix="/api/projects/{project_id}/tasks", tags=["tasks"])


def get_project_service() -> ProjectService:
    """Get project service instance."""
    return ProjectService.get_instance()


def get_task_service() -> TaskService:
    """Get task service instance."""
    return TaskService.get_instance()


def verify_project_exists(project_id: str) -> None:
    """Verify project exists or raise 404."""
    project_service = get_project_service()
    if not project_service.get_project(project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )


@router.get("", response_model=list[Task])
async def list_tasks(project_id: str) -> list[Task]:
    """
    List all tasks for a project.

    Args:
        project_id: Parent project ID

    Returns:
        List of tasks in the project

    Raises:
        404: If project not found
    """
    verify_project_exists(project_id)
    service = get_task_service()
    return service.list_tasks(project_id)


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(project_id: str, data: TaskCreate) -> Task:
    """
    Create a new task in a project.

    Args:
        project_id: Parent project ID
        data: Task creation data with title and description

    Returns:
        Created task

    Raises:
        404: If project not found
        422: If validation fails
    """
    verify_project_exists(project_id)
    service = get_task_service()
    return service.create_task(project_id, data)


@router.get("/{task_id}", response_model=Task)
async def get_task(project_id: str, task_id: str) -> Task:
    """
    Get task by ID.

    Args:
        project_id: Parent project ID
        task_id: Task ID

    Returns:
        Task details

    Raises:
        404: If project or task not found
    """
    verify_project_exists(project_id)
    service = get_task_service()
    task = service.get_task(project_id, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )

    return task


@router.put("/{task_id}", response_model=Task)
async def update_task(project_id: str, task_id: str, data: TaskUpdate) -> Task:
    """
    Update a task.

    Args:
        project_id: Parent project ID
        task_id: Task ID
        data: Fields to update (title, description, status)

    Returns:
        Updated task

    Raises:
        404: If project or task not found
    """
    verify_project_exists(project_id)
    service = get_task_service()
    task = service.update_task(project_id, task_id, data)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(project_id: str, task_id: str) -> Response:
    """
    Delete a task.

    Args:
        project_id: Parent project ID
        task_id: Task ID to delete

    Returns:
        204 No Content on success

    Raises:
        404: If project or task not found
    """
    verify_project_exists(project_id)
    service = get_task_service()

    if not service.delete_task(project_id, task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
