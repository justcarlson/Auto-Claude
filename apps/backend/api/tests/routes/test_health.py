#!/usr/bin/env python3
"""
Health Endpoint Tests
=====================

TDD tests for the /api/health endpoint.
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health_returns_status_ok():
    """
    Given: API server is running
    Should: Return {"status": "ok", "version": "x.x.x"}
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_returns_json_content_type():
    """
    Given: API server is running
    Should: Return application/json content type
    """
    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/health")

    assert "application/json" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_health_is_fast():
    """
    Given: API server is running
    Should: Respond within 100ms (fast health check)
    """
    import time

    from api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        start = time.time()
        response = await client.get("/api/health")
        duration = time.time() - start

    assert response.status_code == 200
    assert duration < 0.1, f"Health check took {duration:.3f}s, expected < 0.1s"
