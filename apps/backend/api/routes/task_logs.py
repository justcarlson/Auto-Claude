"""
Task Logs Endpoints
===================

REST API for task log operations.
Provides access to task execution logs stored in spec directories.

SECURITY: All operations are sandboxed to the project directory.
Path traversal attacks are blocked.
"""

from api.services.task_logs_service import (
    PathTraversalError,
    TaskLogsNotFoundError,
    TaskLogsParseError,
    get_task_logs_service,
)
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(tags=["task-logs"])


# =============================================================================
# GET /api/tasks/{task_id}/logs - Get Task Logs
# =============================================================================


@router.get("/api/tasks/{task_id}/logs")
async def get_task_logs(task_id: str) -> JSONResponse:
    """
    Get task execution logs.

    Returns structured log data with phases (planning, coding, validation)
    and log entries for each phase.

    Security: Path traversal attacks are blocked.
    """
    service = get_task_logs_service()

    try:
        logs = service.get_logs(task_id)
        return JSONResponse(content=service.to_dict(logs))
    except PathTraversalError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except TaskLogsNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskLogsParseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        # Service not configured
        raise HTTPException(status_code=500, detail=str(e))
