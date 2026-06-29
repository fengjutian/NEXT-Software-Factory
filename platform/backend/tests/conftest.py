"""Shared test fixtures."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def settings():
    """Override settings for testing."""
    from app.core.config import get_settings
    return get_settings()


@pytest_asyncio.fixture
async def async_client():
    """Async HTTP test client."""
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
