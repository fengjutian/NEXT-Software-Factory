"""Tests for the health check endpoint."""

import pytest


@pytest.mark.asyncio
async def test_health_check(async_client):
    """Health check returns ok status."""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_app_title(async_client):
    """App title is set correctly."""
    response = await async_client.get("/api/health")
    assert response.json()["app"] == "AI Project Factory"
