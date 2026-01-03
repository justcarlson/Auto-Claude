"""
Settings Service
=================

Business logic for application settings management.
Uses in-memory storage with file persistence.
"""

import json
import os
from pathlib import Path
from typing import Any

from api.models import AppSettings, AppSettingsUpdate, ThemeType

# Default data directory (can be overridden by DATA_DIR env var)
DEFAULT_DATA_DIR = Path.home() / ".auto-claude"


def get_data_dir() -> Path:
    """Get the data directory path."""
    data_dir = os.environ.get("DATA_DIR")
    if data_dir:
        return Path(data_dir)
    return DEFAULT_DATA_DIR


def get_settings_path() -> Path:
    """Get the settings file path."""
    return get_data_dir() / "settings.json"


class SettingsService:
    """
    Service for managing application settings.

    Settings are stored in-memory and persisted to a JSON file.
    """

    _instance: "SettingsService | None" = None

    def __init__(self):
        self._settings: AppSettings = AppSettings()
        self._load_from_file()

    @classmethod
    def get_instance(cls) -> "SettingsService":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = SettingsService()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None

    def _load_from_file(self) -> None:
        """Load settings from file if it exists."""
        settings_path = get_settings_path()
        if settings_path.exists():
            try:
                data = json.loads(settings_path.read_text())
                # Validate and convert theme string to enum
                if "theme" in data and isinstance(data["theme"], str):
                    try:
                        data["theme"] = ThemeType(data["theme"])
                    except ValueError:
                        data["theme"] = ThemeType.system
                self._settings = AppSettings(**data)
            except (json.JSONDecodeError, ValueError):
                # Invalid file, use defaults
                self._settings = AppSettings()

    def _save_to_file(self) -> None:
        """Persist settings to file."""
        settings_path = get_settings_path()
        settings_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict with string enum values for JSON
        data = self._settings.model_dump()
        if isinstance(data.get("theme"), ThemeType):
            data["theme"] = data["theme"].value
        elif hasattr(data.get("theme"), "value"):
            data["theme"] = data["theme"].value

        settings_path.write_text(json.dumps(data, indent=2))

    def get_settings(self) -> AppSettings:
        """Get current settings."""
        return self._settings

    def update_settings(self, updates: AppSettingsUpdate) -> AppSettings:
        """
        Update settings with partial data.

        Args:
            updates: Partial settings to merge

        Returns:
            Updated settings
        """
        # Get current settings as dict
        current = self._settings.model_dump()

        # Merge updates (only non-None values)
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                current[key] = value

        # Create new settings object (validates data)
        self._settings = AppSettings(**current)

        # Persist
        self._save_to_file()

        return self._settings

    def get_version(self) -> str:
        """Get application version."""
        # Try to read from package or use default
        try:
            # Check if there's a version file
            version_file = Path(__file__).parent.parent.parent / "__init__.py"
            if version_file.exists():
                content = version_file.read_text()
                for line in content.split("\n"):
                    if line.startswith("__version__"):
                        return line.split("=")[1].strip().strip('"').strip("'")
        except Exception:
            pass

        # Default version
        return "0.1.0"
