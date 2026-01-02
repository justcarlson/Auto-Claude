"""
Projects API Endpoints
======================

CRUD operations for project management.
"""

from api.models import Project, ProjectCreate
from api.services import ProjectService
from fastapi import APIRouter, HTTPException, Response, status

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_service() -> ProjectService:
    """Get project service instance."""
    return ProjectService.get_instance()


@router.get("", response_model=list[Project])
async def list_projects() -> list[Project]:
    """
    List all projects.

    Returns:
        List of all projects
    """
    service = get_service()
    return service.list_projects()


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate) -> Project:
    """
    Create a new project.

    Args:
        data: Project creation data with path

    Returns:
        Created project

    Raises:
        409: If project with path already exists
    """
    service = get_service()

    try:
        return service.create_project(data.path)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str) -> Project:
    """
    Get project by ID.

    Args:
        project_id: Project ID

    Returns:
        Project details

    Raises:
        404: If project not found
    """
    service = get_service()
    project = service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str) -> Response:
    """
    Delete a project.

    Args:
        project_id: Project ID to delete

    Returns:
        204 No Content on success

    Raises:
        404: If project not found
    """
    service = get_service()

    if not service.delete_project(project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
