#!/usr/bin/env python3
"""
Docker Compose Validation Tests
===============================

Validates docker-compose.yml structure for Dokploy deployment.
These tests run without Docker - they validate the YAML structure.
"""

from pathlib import Path

import pytest

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


def get_compose_path() -> Path:
    """Get path to docker-compose.yml."""
    return PROJECT_ROOT / "docker-compose.yml"


def load_compose() -> dict:
    """Load and parse docker-compose.yml."""
    import yaml

    compose_path = get_compose_path()
    if not compose_path.exists():
        pytest.skip("docker-compose.yml not found (Phase 3)")

    with open(compose_path) as f:
        return yaml.safe_load(f)


class TestDockerComposeStructure:
    """Test docker-compose.yml structure and configuration."""

    def test_compose_file_exists(self):
        """
        Given: Project root directory
        Should: Have docker-compose.yml file
        """
        compose_path = get_compose_path()
        if not compose_path.exists():
            pytest.skip("docker-compose.yml not found (Phase 3)")
        assert compose_path.exists()

    def test_compose_has_app_service(self):
        """
        Given: docker-compose.yml exists
        Should: Have 'app' service defined
        """
        compose = load_compose()

        assert "services" in compose, "Missing 'services' key"
        assert "app" in compose["services"], "Missing 'app' service"

    def test_compose_exposes_port_3000(self):
        """
        Given: docker-compose.yml with app service
        Should: Expose port 3000 for Caddy
        """
        compose = load_compose()

        app = compose["services"]["app"]
        ports = app.get("ports", [])

        port_found = any("3000" in str(p) for p in ports)
        assert port_found, "App service should expose port 3000"

    def test_compose_has_required_volumes(self):
        """
        Given: docker-compose.yml
        Should: Have named volumes for data persistence
        """
        compose = load_compose()

        assert "volumes" in compose, "Missing 'volumes' key"
        assert "auto-claude-data" in compose["volumes"], (
            "Missing 'auto-claude-data' volume"
        )

    def test_compose_has_env_vars(self):
        """
        Given: docker-compose.yml with app service
        Should: Have required environment variables
        """
        compose = load_compose()

        app = compose["services"]["app"]
        env = app.get("environment", [])
        env_str = str(env)

        assert "CLAUDE_CODE_OAUTH_TOKEN" in env_str, (
            "Missing CLAUDE_CODE_OAUTH_TOKEN env var"
        )

    def test_compose_no_host_network(self):
        """
        Given: docker-compose.yml for Dokploy
        Should: NOT use host network (Dokploy requires bridge)
        """
        compose = load_compose()

        app = compose["services"]["app"]
        network_mode = app.get("network_mode", "")

        assert network_mode != "host", "Dokploy requires bridge network, not host"

    def test_compose_has_traefik_labels(self):
        """
        Given: docker-compose.yml for Dokploy
        Should: Have Traefik labels for routing
        """
        compose = load_compose()

        app = compose["services"]["app"]
        labels = app.get("labels", [])
        labels_str = str(labels)

        assert "traefik.enable" in labels_str, "Missing Traefik enable label"

    def test_compose_has_healthcheck(self):
        """
        Given: docker-compose.yml with app service
        Should: Have healthcheck or rely on Dockerfile HEALTHCHECK
        """
        compose = load_compose()

        app = compose["services"]["app"]
        # Either has healthcheck in compose or relies on Dockerfile
        # We'll accept either
        has_healthcheck = "healthcheck" in app
        has_build = "build" in app

        assert has_healthcheck or has_build, (
            "Should have healthcheck or build (which uses Dockerfile HEALTHCHECK)"
        )


class TestDockerComposeVolumes:
    """Test volume configuration for data persistence."""

    def test_data_volume_mounted(self):
        """
        Given: docker-compose.yml with app service
        Should: Mount auto-claude-data to /data
        """
        compose = load_compose()

        app = compose["services"]["app"]
        volumes = app.get("volumes", [])

        data_mount = any("/data" in str(v) for v in volumes)
        assert data_mount, "Should mount volume to /data"

    def test_projects_volume_or_bind(self):
        """
        Given: docker-compose.yml with app service
        Should: Have projects volume or bind mount
        """
        compose = load_compose()

        app = compose["services"]["app"]
        volumes = app.get("volumes", [])

        projects_mount = any("/projects" in str(v) for v in volumes)
        assert projects_mount, "Should mount volume to /projects"
