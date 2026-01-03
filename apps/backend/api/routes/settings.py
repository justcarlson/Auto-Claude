"""
Settings Endpoints
==================

Provides endpoints for application settings management.
"""

from api.models import AppSettings, AppSettingsUpdate, VersionResponse
from api.services import SettingsService
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["settings"])


def get_settings_service() -> SettingsService:
    """Get settings service instance."""
    return SettingsService.get_instance()


@router.get("/settings", response_model=AppSettings)
async def get_settings() -> AppSettings:
    """
    Get current application settings.

    Returns:
        AppSettings: Current settings including theme, defaultModel, graphitiEnabled
    """
    service = get_settings_service()
    return service.get_settings()


@router.put("/settings", response_model=AppSettings)
async def save_settings(updates: AppSettingsUpdate) -> AppSettings:
    """
    Update application settings.

    Performs a partial update - only provided fields are changed.

    Args:
        updates: Partial settings to merge

    Returns:
        AppSettings: Updated settings
    """
    service = get_settings_service()
    return service.update_settings(updates)


@router.get("/version", response_model=VersionResponse)
async def get_version() -> VersionResponse:
    """
    Get application version.

    Returns:
        VersionResponse: Application version string
    """
    service = get_settings_service()
    return VersionResponse(version=service.get_version())
