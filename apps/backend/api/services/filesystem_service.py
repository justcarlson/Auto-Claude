"""
Filesystem Service
==================

Web API service for filesystem operations.
Provides directory listing and file reading with security sandboxing.

SECURITY: All operations are sandboxed to the project directory.
Path traversal attacks are blocked by resolving paths and verifying
they remain within the project root.
"""

import os
import urllib.parse
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileNode:
    """Information about a file or directory."""

    name: str
    path: str
    type: str  # 'file' or 'directory'
    size: int | None = None


@dataclass
class FileContent:
    """Content of a file."""

    path: str
    content: str | None
    is_binary: bool
    size: int


class PathTraversalError(Exception):
    """Raised when a path traversal attack is detected."""

    pass


class FilesystemService:
    """
    Singleton service for filesystem operations.

    All paths are validated to prevent traversal attacks.
    Operations are sandboxed to the configured project directory.
    """

    _instance: "FilesystemService | None" = None

    # Binary file extensions (common ones)
    BINARY_EXTENSIONS = frozenset(
        {
            # Images
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".ico",
            ".webp",
            ".svg",
            ".tiff",
            ".tif",
            # Audio
            ".mp3",
            ".wav",
            ".ogg",
            ".flac",
            ".aac",
            ".m4a",
            # Video
            ".mp4",
            ".avi",
            ".mkv",
            ".mov",
            ".webm",
            ".wmv",
            # Archives
            ".zip",
            ".tar",
            ".gz",
            ".bz2",
            ".xz",
            ".7z",
            ".rar",
            # Executables
            ".exe",
            ".dll",
            ".so",
            ".dylib",
            ".bin",
            # Documents
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            # Fonts
            ".ttf",
            ".otf",
            ".woff",
            ".woff2",
            ".eot",
            # Other
            ".pyc",
            ".pyo",
            ".class",
            ".o",
            ".a",
            ".lib",
            ".node",
        }
    )

    def __init__(self):
        self._project_dir: Path | None = None

    @classmethod
    def get_instance(cls) -> "FilesystemService":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance. Used for testing."""
        cls._instance = None

    def set_project_dir(self, project_dir: Path) -> None:
        """
        Set the project directory for filesystem operations.

        Args:
            project_dir: Path to the project root
        """
        self._project_dir = project_dir.resolve()

    def _get_project_dir(self) -> Path:
        """Get the project directory, raising if not configured."""
        if self._project_dir is None:
            raise RuntimeError(
                "FilesystemService not configured. Call set_project_dir first."
            )
        return self._project_dir

    def _validate_path(self, relative_path: str) -> Path:
        """
        Validate and resolve a path, ensuring it's within the project.

        Args:
            relative_path: Path relative to project root

        Returns:
            Resolved absolute path

        Raises:
            PathTraversalError: If path would escape project directory
        """
        project_dir = self._get_project_dir()

        # Decode URL-encoded characters
        decoded_path = urllib.parse.unquote(relative_path)

        # Normalize path separators
        normalized = decoded_path.replace("\\", "/")

        # Block obvious traversal patterns before resolution
        if ".." in normalized:
            raise PathTraversalError(f"Path traversal detected: {relative_path}")

        # Block absolute paths
        if normalized.startswith("/"):
            raise PathTraversalError(f"Absolute path not allowed: {relative_path}")

        # Resolve the full path
        if normalized:
            full_path = (project_dir / normalized).resolve()
        else:
            full_path = project_dir

        # Verify the resolved path is within project directory
        try:
            full_path.relative_to(project_dir)
        except ValueError:
            raise PathTraversalError(f"Path outside project: {relative_path}")

        return full_path

    def list_directory(self, relative_path: str = "") -> list[FileNode]:
        """
        List contents of a directory.

        Args:
            relative_path: Path relative to project root (empty for root)

        Returns:
            List of FileNode objects

        Raises:
            PathTraversalError: If path would escape project directory
            FileNotFoundError: If directory doesn't exist
            NotADirectoryError: If path is not a directory
        """
        full_path = self._validate_path(relative_path)

        if not full_path.exists():
            raise FileNotFoundError(f"Directory not found: {relative_path or '.'}")

        if not full_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {relative_path}")

        project_dir = self._get_project_dir()
        nodes = []

        for item in full_path.iterdir():
            # Get path relative to project root
            try:
                rel_path = item.relative_to(project_dir)
            except ValueError:
                continue  # Skip items outside project

            node = FileNode(
                name=item.name,
                path=str(rel_path).replace(os.sep, "/"),
                type="directory" if item.is_dir() else "file",
                size=item.stat().st_size if item.is_file() else None,
            )
            nodes.append(node)

        # Sort: directories first, then files, both alphabetically
        nodes.sort(key=lambda n: (n.type != "directory", n.name.lower()))

        return nodes

    def read_file(self, relative_path: str) -> FileContent:
        """
        Read contents of a file.

        Args:
            relative_path: Path relative to project root

        Returns:
            FileContent with content and metadata

        Raises:
            PathTraversalError: If path would escape project directory
            FileNotFoundError: If file doesn't exist
            IsADirectoryError: If path is a directory
        """
        full_path = self._validate_path(relative_path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")

        if full_path.is_dir():
            raise IsADirectoryError(f"Path is a directory: {relative_path}")

        size = full_path.stat().st_size

        # Check if binary by extension first
        is_binary = self._is_binary_file(full_path)

        if is_binary:
            return FileContent(
                path=relative_path,
                content=None,
                is_binary=True,
                size=size,
            )

        # Try to read as text
        try:
            content = full_path.read_text(encoding="utf-8")
            return FileContent(
                path=relative_path,
                content=content,
                is_binary=False,
                size=size,
            )
        except UnicodeDecodeError:
            # File is binary despite extension
            return FileContent(
                path=relative_path,
                content=None,
                is_binary=True,
                size=size,
            )

    def _is_binary_file(self, path: Path) -> bool:
        """
        Determine if a file is binary based on extension and content.

        Args:
            path: Path to the file

        Returns:
            True if file appears to be binary
        """
        # Check extension first
        ext = path.suffix.lower()
        if ext in self.BINARY_EXTENSIONS:
            return True

        # Check file content (first 8KB)
        try:
            with open(path, "rb") as f:
                chunk = f.read(8192)

            # Look for null bytes (common in binary files)
            if b"\x00" in chunk:
                return True

        except Exception:
            # If we can't read, assume text
            pass

        return False


def get_filesystem_service() -> FilesystemService:
    """Dependency injection helper for FastAPI."""
    return FilesystemService.get_instance()
