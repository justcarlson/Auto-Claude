#!/usr/bin/env python3
"""
File System Endpoints Tests
===========================

TDD tests for the /api/fs endpoints.
Tests written BEFORE implementation to drive development.

Security is critical - tests MUST verify path traversal attacks are blocked.
"""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def project_with_files(tmp_path: Path):
    """
    Create a temporary project with a file structure for testing.
    """
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Create directories
    (project_dir / "src").mkdir()
    (project_dir / "src" / "components").mkdir()
    (project_dir / "tests").mkdir()

    # Create files
    (project_dir / "README.md").write_text("# Test Project\n\nThis is a test.")
    (project_dir / "package.json").write_text('{"name": "test", "version": "1.0.0"}')
    (project_dir / "src" / "index.ts").write_text('export const main = () => "hello";')
    (project_dir / "src" / "components" / "Button.tsx").write_text(
        "export const Button = () => <button>Click</button>;"
    )
    (project_dir / "tests" / "test_main.py").write_text("def test_main():\n    pass")

    # Create a hidden file
    (project_dir / ".gitignore").write_text("node_modules/\n.env\n")

    return project_dir


@pytest.fixture
def project_with_binary(tmp_path: Path):
    """
    Create a project with a binary file for testing.
    """
    project_dir = tmp_path / "binary-project"
    project_dir.mkdir()

    # Create a text file
    (project_dir / "text.txt").write_text("Hello, world!")

    # Create a binary file (PNG header bytes)
    png_header = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
    (project_dir / "image.png").write_bytes(png_header + b"\x00" * 100)

    return project_dir


@pytest.fixture(autouse=True)
def isolated_filesystem_service(tmp_path: Path):
    """Ensure each test uses isolated filesystem service."""
    from api.services.filesystem_service import FilesystemService

    # Reset filesystem service for fresh state
    FilesystemService.reset()

    yield

    # Cleanup after test
    FilesystemService.reset()


# =============================================================================
# GET /api/fs/list - List Directory
# =============================================================================


@pytest.mark.asyncio
async def test_list_directory_returns_nodes(project_with_files: Path):
    """
    Given: A project directory with files and subdirectories
    Should: Return list of nodes with type, name, and path
    """
    from api.main import app
    from api.services.filesystem_service import FilesystemService

    service = FilesystemService.get_instance()
    service.set_project_dir(project_with_files)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/fs/list", params={"path": "", "project_id": "test-project-id"}
        )

    assert response.status_code == 200
    data = response.json()

    # Should have a nodes list
    assert "nodes" in data
    assert isinstance(data["nodes"], list)

    # Should have expected items
    node_names = [n["name"] for n in data["nodes"]]
    assert "README.md" in node_names
    assert "package.json" in node_names
    assert "src" in node_names
    assert "tests" in node_names
    assert ".gitignore" in node_names

    # Check node structure
    readme_node = next(n for n in data["nodes"] if n["name"] == "README.md")
    assert readme_node["type"] == "file"
    assert readme_node["path"] == "README.md"

    src_node = next(n for n in data["nodes"] if n["name"] == "src")
    assert src_node["type"] == "directory"
    assert src_node["path"] == "src"


@pytest.mark.asyncio
async def test_list_subdirectory(project_with_files: Path):
    """
    Given: A subdirectory path
    Should: Return contents of that subdirectory
    """
    from api.main import app
    from api.services.filesystem_service import FilesystemService

    service = FilesystemService.get_instance()
    service.set_project_dir(project_with_files)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/fs/list", params={"path": "src", "project_id": "test-project-id"}
        )

    assert response.status_code == 200
    data = response.json()

    node_names = [n["name"] for n in data["nodes"]]
    assert "index.ts" in node_names
    assert "components" in node_names


@pytest.mark.asyncio
async def test_list_directory_path_traversal_blocked(project_with_files: Path):
    """
    Given: A path traversal attempt (../)
    Should: Return 403 Forbidden
    """
    from api.main import app
    from api.services.filesystem_service import FilesystemService

    service = FilesystemService.get_instance()
    service.set_project_dir(project_with_files)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Try various path traversal attacks
        attacks = [
            "../",
            "../../",
            "../../../etc/passwd",
            "src/../../../",
            "src/components/../../../..",
            "/etc/passwd",
            "..\\",  # Windows-style
            "%2e%2e%2f",  # URL-encoded
        ]

        for attack in attacks:
            response = await client.get(
                "/api/fs/list",
                params={"path": attack, "project_id": "test-project-id"},
            )
            assert response.status_code == 403, f"Path traversal not blocked: {attack}"


@pytest.mark.asyncio
async def test_list_nonexistent_directory_returns_404(project_with_files: Path):
    """
    Given: A path that doesn't exist
    Should: Return 404 Not Found
    """
    from api.main import app
    from api.services.filesystem_service import FilesystemService

    service = FilesystemService.get_instance()
    service.set_project_dir(project_with_files)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/fs/list",
            params={"path": "nonexistent", "project_id": "test-project-id"},
        )

    assert response.status_code == 404


# =============================================================================
# GET /api/fs/read - Read File
# =============================================================================


@pytest.mark.asyncio
async def test_read_file_returns_content(project_with_files: Path):
    """
    Given: A valid file path
    Should: Return file content as text
    """
    from api.main import app
    from api.services.filesystem_service import FilesystemService

    service = FilesystemService.get_instance()
    service.set_project_dir(project_with_files)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/fs/read",
            params={"path": "README.md", "project_id": "test-project-id"},
        )

    assert response.status_code == 200
    data = response.json()

    assert "content" in data
    assert data["content"] == "# Test Project\n\nThis is a test."
    assert data["path"] == "README.md"
    assert data["isBinary"] is False


@pytest.mark.asyncio
async def test_read_file_in_subdirectory(project_with_files: Path):
    """
    Given: A file path in a subdirectory
    Should: Return file content
    """
    from api.main import app
    from api.services.filesystem_service import FilesystemService

    service = FilesystemService.get_instance()
    service.set_project_dir(project_with_files)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/fs/read",
            params={"path": "src/index.ts", "project_id": "test-project-id"},
        )

    assert response.status_code == 200
    data = response.json()

    assert data["content"] == 'export const main = () => "hello";'
    assert data["path"] == "src/index.ts"


@pytest.mark.asyncio
async def test_read_file_outside_project_blocked(project_with_files: Path):
    """
    Given: A path traversal attempt to read file outside project
    Should: Return 403 Forbidden
    """
    from api.main import app
    from api.services.filesystem_service import FilesystemService

    service = FilesystemService.get_instance()
    service.set_project_dir(project_with_files)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Try various path traversal attacks
        attacks = [
            "../../../etc/passwd",
            "/etc/passwd",
            "src/../../../.bashrc",
            "..\\..\\windows\\system32\\config\\sam",  # Windows-style
        ]

        for attack in attacks:
            response = await client.get(
                "/api/fs/read",
                params={"path": attack, "project_id": "test-project-id"},
            )
            assert response.status_code == 403, f"Path traversal not blocked: {attack}"


@pytest.mark.asyncio
async def test_read_nonexistent_file_returns_404(project_with_files: Path):
    """
    Given: A file path that doesn't exist
    Should: Return 404 Not Found
    """
    from api.main import app
    from api.services.filesystem_service import FilesystemService

    service = FilesystemService.get_instance()
    service.set_project_dir(project_with_files)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/fs/read",
            params={"path": "nonexistent.txt", "project_id": "test-project-id"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_read_directory_returns_400(project_with_files: Path):
    """
    Given: A path to a directory (not a file)
    Should: Return 400 Bad Request
    """
    from api.main import app
    from api.services.filesystem_service import FilesystemService

    service = FilesystemService.get_instance()
    service.set_project_dir(project_with_files)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/fs/read", params={"path": "src", "project_id": "test-project-id"}
        )

    assert response.status_code == 400


# =============================================================================
# Binary File Handling
# =============================================================================


@pytest.mark.asyncio
async def test_binary_file_handled(project_with_binary: Path):
    """
    Given: A binary file (e.g., image)
    Should: Return with isBinary=True and no content (or base64)
    """
    from api.main import app
    from api.services.filesystem_service import FilesystemService

    service = FilesystemService.get_instance()
    service.set_project_dir(project_with_binary)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/fs/read",
            params={"path": "image.png", "project_id": "test-project-id"},
        )

    assert response.status_code == 200
    data = response.json()

    assert data["isBinary"] is True
    assert data["path"] == "image.png"
    # Binary content should be empty or base64-encoded
    # For now, we just mark it as binary and don't return raw content


@pytest.mark.asyncio
async def test_text_file_detected_correctly(project_with_binary: Path):
    """
    Given: A text file
    Should: Return with isBinary=False and content
    """
    from api.main import app
    from api.services.filesystem_service import FilesystemService

    service = FilesystemService.get_instance()
    service.set_project_dir(project_with_binary)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/fs/read",
            params={"path": "text.txt", "project_id": "test-project-id"},
        )

    assert response.status_code == 200
    data = response.json()

    assert data["isBinary"] is False
    assert data["content"] == "Hello, world!"
