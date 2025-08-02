"""
Integration tests for plugin system with OffersClient.

This module tests how plugins integrate with the main OffersClient including:
- Plugin integration with client requests
- Multiple plugins working together
- Plugin behavior in real client scenarios
- Error handling in plugin integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from offers_sdk.client import OffersClient
from offers_sdk.generated.models import RegisterProductRequest
from offers_sdk.plugins.examples import (
    LoggingPlugin,
    AuthenticationPlugin,
    MetricsPlugin
)
from offers_sdk.transport.base import UnifiedResponse
from offers_sdk.config import OffersAPISettings
from tests.fakes import MockTransport


@pytest.fixture
def success_response():
    mock = MagicMock()
    mock.status_code = 201
    mock.text = "OK"
    mock.json = AsyncMock(return_value={"id": "product"})
    return UnifiedResponse(mock)


@pytest.fixture
def error_response():
    mock = MagicMock()
    mock.status_code = 401
    mock.text = "Unauthorized"
    return UnifiedResponse(mock)


@pytest.fixture
def test_product():
    return RegisterProductRequest(
        id="product",
        name="Test",
        description="Test Product"
    )


@pytest.fixture
def mock_transport():
    return MockTransport()


@pytest.fixture
def client_with_plugin(mock_transport):
    """Provides an OffersClient with injected transport and plugins."""
    with patch("offers_sdk.client.get_transport", return_value=mock_transport):
        settings = OffersAPISettings(refresh_token="token")
        plugin = LoggingPlugin()
        client = OffersClient(settings=settings, plugins=[plugin])
        client.auth.get_access_token = AsyncMock(return_value="token")
        yield client


@pytest.mark.asyncio
async def test_register_with_logging_plugin(client_with_plugin, success_response, test_product):
    client = client_with_plugin
    client.transport.request = AsyncMock(return_value=success_response)
    result = await client.register_product(test_product)
    assert result.id == "product"
    client.transport.request.assert_called_once()


@pytest.mark.asyncio
async def test_authentication_plugin_sets_header(mock_transport, success_response, test_product):
    with patch("offers_sdk.client.get_transport", return_value=mock_transport):
        plugin = AuthenticationPlugin("secret")
        settings = OffersAPISettings(refresh_token="token")
        client = OffersClient(settings=settings, plugins=[plugin])
        client.auth.get_access_token = AsyncMock(return_value="token")
        client.transport.request = AsyncMock(return_value=success_response)

        await client.register_product(test_product)

        headers = client.transport.request.call_args[1]["headers"]
        assert headers.get("X-API-Key") == "secret"


@pytest.mark.asyncio
async def test_metrics_plugin_counts_success(mock_transport, success_response, test_product):
    metrics = MetricsPlugin()
    with patch("offers_sdk.client.get_transport", return_value=mock_transport):
        settings = OffersAPISettings(refresh_token="token")
        client = OffersClient(settings=settings, plugins=[metrics])
        client.auth.get_access_token = AsyncMock(return_value="token")
        client.transport.request = AsyncMock(return_value=success_response)

        await client.register_product(test_product)

        assert metrics.request_count == 1
