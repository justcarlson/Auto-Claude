"""
Auto-Claude Web API
===================

FastAPI backend for Docker/Dokploy deployment.
Provides REST and WebSocket endpoints for the React frontend.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health_router, projects_router, tasks_router
from api.services import ProjectService, TaskService
from api.websocket.terminal import terminal_websocket, reset_terminal_manager


def get_cors_origins() -> list[str]:
    """Get allowed CORS origins from environment or use defaults."""
    origins_env = os.getenv("CORS_ORIGINS", "")
    if origins_env:
        return [origin.strip() for origin in origins_env.split(",") if origin.strip()]
    if os.getenv("DEBUG", "").lower() in ("true", "1"):
        return ["*"]
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


# Create FastAPI app
app = FastAPI(
    title="Auto-Claude API",
    description="Backend API for Auto-Claude autonomous coding framework",
    version="0.1.0",
)

# Configure CORS - reads from CORS_ORIGINS env var, defaults to localhost:3000
cors_origins = get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(projects_router)
app.include_router(tasks_router)

# WebSocket routes
app.websocket("/ws/terminal/{terminal_id}")(terminal_websocket)


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    # Reset services for fresh start
    ProjectService.reset()
    TaskService.reset()
    reset_terminal_manager()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    reset_terminal_manager()
