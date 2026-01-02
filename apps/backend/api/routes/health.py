"""
Health Endpoint
===============

Provides health check endpoint for monitoring and load balancers.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        dict: {"status": "ok", "version": "x.x.x"}
    """
    return {
        "status": "ok",
        "version": "0.1.0",  # TODO: Get from package
    }
