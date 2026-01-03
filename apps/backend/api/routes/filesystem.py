"""
Filesystem Operations Endpoints
===============================

REST API for filesystem operations.
Supports directory listing and file reading with security sandboxing.

SECURITY: All operations are sandboxed to the project directory.
Path traversal attacks are blocked.
"""

from api.models import DirectoryListResponse, FileContentResponse, FileNode
from api.services import get_filesystem_service
from api.services.filesystem_service import PathTraversalError
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["filesystem"])


# =============================================================================
# GET /api/fs/list - List Directory Contents
# =============================================================================


@router.get("/api/fs/list", response_model=DirectoryListResponse)
async def list_directory(
    path: str = Query(default="", description="Path relative to project root"),
    project_id: str = Query(..., description="Project ID"),
) -> DirectoryListResponse:
    """
    List contents of a directory within the project.

    Returns list of files and directories with metadata.

    Security: Path traversal attacks are blocked.
    """
    service = get_filesystem_service()

    try:
        nodes = service.list_directory(path)
        return DirectoryListResponse(
            nodes=[
                FileNode(name=n.name, path=n.path, type=n.type, size=n.size)
                for n in nodes
            ]
        )
    except PathTraversalError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# GET /api/fs/read - Read File Content
# =============================================================================


@router.get("/api/fs/read", response_model=FileContentResponse)
async def read_file(
    path: str = Query(..., description="File path relative to project root"),
    project_id: str = Query(..., description="Project ID"),
) -> FileContentResponse:
    """
    Read contents of a file within the project.

    Returns file content as text (or marks as binary if not readable as text).

    Security: Path traversal attacks are blocked.
    """
    service = get_filesystem_service()

    try:
        file_content = service.read_file(path)
        return FileContentResponse(
            path=file_content.path,
            content=file_content.content,
            isBinary=file_content.is_binary,
            size=file_content.size,
        )
    except PathTraversalError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IsADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))
