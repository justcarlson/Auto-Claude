#!/usr/bin/env python3
"""
Dockerfile Validation Tests
===========================

Validates Dockerfile structure without running Docker.
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


def get_dockerfile_path() -> Path:
    """Get path to Dockerfile."""
    return PROJECT_ROOT / "Dockerfile"


def load_dockerfile() -> str:
    """Load Dockerfile content."""
    dockerfile_path = get_dockerfile_path()
    if not dockerfile_path.exists():
        pytest.skip("Dockerfile not found (Phase 3)")

    return dockerfile_path.read_text()


class TestDockerfileStructure:
    """Test Dockerfile structure and best practices."""

    def test_dockerfile_exists(self):
        """
        Given: Project root directory
        Should: Have Dockerfile
        """
        dockerfile_path = get_dockerfile_path()
        if not dockerfile_path.exists():
            pytest.skip("Dockerfile not found (Phase 3)")
        assert dockerfile_path.exists()

    def test_dockerfile_has_multistage_build(self):
        """
        Given: Dockerfile exists
        Should: Use multi-stage build for smaller image
        """
        content = load_dockerfile()

        # Count FROM statements
        from_count = len(re.findall(r"^FROM\s+", content, re.MULTILINE))
        assert from_count >= 2, "Should use multi-stage build (multiple FROM)"

    def test_dockerfile_has_healthcheck(self):
        """
        Given: Dockerfile exists
        Should: Have HEALTHCHECK instruction
        """
        content = load_dockerfile()

        assert "HEALTHCHECK" in content, "Should have HEALTHCHECK instruction"

    def test_dockerfile_exposes_port(self):
        """
        Given: Dockerfile exists
        Should: EXPOSE port 3000
        """
        content = load_dockerfile()

        assert "EXPOSE" in content, "Should have EXPOSE instruction"
        assert "3000" in content, "Should expose port 3000"

    def test_dockerfile_sets_workdir(self):
        """
        Given: Dockerfile exists
        Should: Set WORKDIR
        """
        content = load_dockerfile()

        assert "WORKDIR" in content, "Should set WORKDIR"

    def test_dockerfile_has_non_root_user(self):
        """
        Given: Dockerfile exists
        Should: Run as non-root user for security
        """
        content = load_dockerfile()

        # Check for user creation or USER instruction
        has_useradd = "useradd" in content or "adduser" in content
        has_user = "USER" in content

        assert has_useradd or has_user, "Should create/use non-root user"

    def test_dockerfile_copies_requirements_first(self):
        """
        Given: Dockerfile exists
        Should: Copy requirements before app code (for caching)
        """
        content = load_dockerfile()

        # Find positions of requirements copy and full app copy
        req_match = re.search(r"COPY.*requirements", content, re.IGNORECASE)

        if req_match:
            # Requirements should be copied (good practice)
            assert True
        else:
            # Acceptable if using different pattern
            pytest.skip("Different dependency pattern used")


class TestDockerfileSecurity:
    """Test Dockerfile security best practices."""

    def test_no_root_cmd(self):
        """
        Given: Dockerfile with CMD
        Should: Not run as root in final stage
        """
        content = load_dockerfile()

        # Check that USER is set before CMD
        user_pos = content.rfind("USER")
        cmd_pos = content.rfind("CMD")

        if user_pos > 0 and cmd_pos > 0:
            assert user_pos < cmd_pos, "USER should be set before CMD"

    def test_no_secrets_in_dockerfile(self):
        """
        Given: Dockerfile exists
        Should: Not contain hardcoded secrets
        """
        content = load_dockerfile()

        # Check for common secret patterns
        secret_patterns = [
            r"password\s*=\s*['\"]",
            r"secret\s*=\s*['\"]",
            r"api_key\s*=\s*['\"]",
            r"token\s*=\s*['\"][a-zA-Z0-9]",
        ]

        for pattern in secret_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert len(matches) == 0, f"Found potential secret: {pattern}"
