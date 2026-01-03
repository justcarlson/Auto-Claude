# API Routes
from .health import router as health_router
from .projects import router as projects_router
from .settings import router as settings_router
from .tasks import router as tasks_router

__all__ = ["health_router", "projects_router", "settings_router", "tasks_router"]
