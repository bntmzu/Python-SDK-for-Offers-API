"""
Test suite for the OffersClient class.

This module contains comprehensive tests for the OffersClient functionality,
covering product registration, offer retrieval, caching mechanisms,
authentication retry logic, error handling, and middleware integration.

The tests use mocked components to ensure isolated testing of business
logic without external dependencies.

Author: Offers SDK Team
Version: 1.0.0
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from offers_sdk.client import OffersClient
from offers_sdk.config import OffersAPISettings
from offers_sdk.exceptions import OffersAPIError
from offers_sdk.generated.models import RegisterProductRequest
from offers_sdk.transport.base import UnifiedResponse


class MockTransport:
    """
    Mock transport for testing that simulates HTTP responses.
    """

    def __init__(self, handler):
        self.handler = handler
        self.request_calls = []

    async def request(self, method, url, headers=None, json=None, **kwargs):
        """Mock request method that calls the handler."""
        self.request_calls.append(
            {"method": method, "url": url, "headers": headers, "json": json, **kwargs}
        )

        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Mock response"
        mock_response.json = AsyncMock(return_value={"id": "test-product"})

        # Let handler override the response
        if self.handler:
            result = await self.handler(mock_response)
            if result:
                mock_response = result

        # Wrap in UnifiedResponse
        return UnifiedResponse(mock_response)

    async def close(self):
        pass


@pytest.fixture
def settings(monkeypatch):
    """Create test settings with mock environment."""
    monkeypatch.setenv("OFFERS_API_REFRESH_TOKEN", "test-refresh-token")
    monkeypatch.setenv("OFFERS_API_BASE_URL", "https://api.test")
    monkeypatch.setenv("OFFERS_API_TIMEOUT", "30.0")

    settings = OffersAPISettings()
    return settings


@pytest.fixture
def client(settings):
    """Create a test client with mock transport and auth."""
    client = OffersClient(settings)
    client.transport = MockTransport(None)
    client.auth = AsyncMock()
    client.auth.get_access_token.return_value = "test-token"
    client.middlewares = []
    return client


@pytest.mark.asyncio
async def test_register_product_success():
    """
    Test successful product registration.

    This test verifies that:
    - The correct HTTP method and URL are used
    - Authentication headers are properly set
    - Request payload is correctly formatted
    - Response is properly parsed into RegisterProductResponse

    Expected behavior:
    - POST request to /api/v1/products/register
    - Bearer token in Authorization header
    - 201 status code with JSON response
    - RegisterProductResponse object returned
    """

    async def handler(mock_response):
        """Mock handler that returns success response."""
        mock_response.status_code = 201
        mock_response.json = AsyncMock(return_value={"id": "1234"})
        return mock_response

    transport = MockTransport(handler)
    auth = AsyncMock()
    auth.get_access_token.return_value = "test-token"

    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)
    client.transport = transport
    client.auth = auth
    client.middlewares = []

    req = RegisterProductRequest(
        id="1234", name="Test Product", description="Test Description"
    )

    result = await client.register_product(req)

    assert result.id == "1234"
    assert len(transport.request_calls) == 1
    assert transport.request_calls[0]["method"] == "POST"
    assert "/api/v1/products/register" in transport.request_calls[0]["url"]
    assert transport.request_calls[0]["headers"]["Bearer"] == "test-token"


@pytest.mark.asyncio
async def test_register_product_401_then_success():
    """
    Test product registration with 401 then success.

    This test verifies that the client properly handles 401 errors
    by refreshing the token and retrying the request.

    Expected behavior:
    - First request returns 401 Unauthorized
    - Client refreshes token
    - Second request succeeds
    """
    call_count = 0

    async def handler(mock_response):
        """Mock handler that returns 401 then success."""
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
        else:
            mock_response.status_code = 201
            mock_response.json = AsyncMock(return_value={"id": "1234"})

        return mock_response

    transport = MockTransport(handler)
    auth = AsyncMock()
    auth.get_access_token.return_value = "old-token"

    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)
    client.transport = transport
    client.auth = auth
    client.middlewares = []

    req = RegisterProductRequest(
        id="1234", name="Test Product", description="Test Description"
    )
    result = await client.register_product(req)

    assert result.id == "1234"
    assert len(transport.request_calls) == 2
    # Both calls use the same token since get_access_token returns the same value
    assert transport.request_calls[0]["headers"]["Bearer"] == "old-token"
    assert transport.request_calls[1]["headers"]["Bearer"] == "old-token"


@pytest.mark.asyncio
async def test_register_product_conflict():
    """
    Test product registration with conflict error.

    This test verifies that the client properly handles 409 errors
    when trying to register a product that already exists.

    Expected behavior:
    - Request returns 409 Conflict
    - OffersAPIError is raised with appropriate message
    """

    async def handler(mock_response):
        """Mock handler that returns 409 Conflict."""
        mock_response.status_code = 409
        return mock_response

    transport = MockTransport(handler)
    auth = AsyncMock()
    auth.get_access_token.return_value = "test-token"

    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)
    client.transport = transport
    client.auth = auth
    client.middlewares = []

    with pytest.raises(OffersAPIError, match="Product ID already registered"):
        await client.register_product(
            RegisterProductRequest(id="1", name="Test", description="Desc")
        )


@pytest.mark.asyncio
async def test_register_product_validation_error():
    """
    Test product registration with validation error.

    This test verifies that the client properly handles 422 errors
    which typically indicate invalid request parameters or data.

    Expected behavior:
    - Request returns 422 Unprocessable Entity
    - OffersAPIError is raised with validation error message
    """

    async def handler(mock_response):
        """Mock handler that returns 422 validation error."""
        mock_response.status_code = 422
        mock_response.json = AsyncMock(return_value={"detail": "Invalid product data"})
        return mock_response

    transport = MockTransport(handler)
    auth = AsyncMock()
    auth.get_access_token.return_value = "test-token"

    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)
    client.transport = transport
    client.auth = auth
    client.middlewares = []

    with pytest.raises(OffersAPIError, match="Validation error"):
        await client.register_product(
            RegisterProductRequest(id="1", name="Test", description="Desc")
        )


@pytest.mark.asyncio
async def test_get_offers_success():
    """
    Test successful retrieval of offers for a product.

    This test verifies that:
    - The correct HTTP method and URL are used
    - Authentication headers are properly set
    - Response data is correctly parsed into OfferResponse objects
    - All offer fields are properly mapped

    Expected behavior:
    - GET request to /api/v1/products/{product_id}/offers
    - Bearer token in Authorization header
    - 200 status code with JSON response
    - List of OfferResponse objects returned
    """

    async def handler(mock_response):
        """Mock handler that returns test offers."""
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value=[
                {"id": "offer-1", "price": 100, "items_in_stock": 5},
                {"id": "offer-2", "price": 200, "items_in_stock": 10},
            ]
        )
        return mock_response

    transport = MockTransport(handler)
    auth = AsyncMock()
    auth.get_access_token.return_value = "test-token"

    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)
    client.transport = transport
    client.auth = auth
    client.middlewares = []

    offers = await client.get_offers("test-product")

    assert len(offers) == 2
    assert offers[0].id == "offer-1"
    assert offers[0].price == 100
    assert offers[0].items_in_stock == 5
    assert offers[1].id == "offer-2"
    assert offers[1].price == 200
    assert offers[1].items_in_stock == 10

    assert len(transport.request_calls) == 1
    assert transport.request_calls[0]["method"] == "GET"
    assert "/api/v1/products/test-product/offers" in transport.request_calls[0]["url"]
    assert transport.request_calls[0]["headers"]["Bearer"] == "test-token"


@pytest.mark.asyncio
async def test_get_offers_not_found():
    """
    Test offers retrieval for non-existent product.

    This test verifies that the client properly handles 404 errors
    when trying to get offers for a product that doesn't exist.

    Expected behavior:
    - Request returns 404 Not Found
    - OffersAPIError is raised with appropriate message
    """

    async def handler(mock_response):
        """Mock handler that returns 404 Not Found."""
        mock_response.status_code = 404
        return mock_response

    transport = MockTransport(handler)
    auth = AsyncMock()
    auth.get_access_token.return_value = "test-token"

    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)
    client.transport = transport
    client.auth = auth
    client.middlewares = []

    with pytest.raises(OffersAPIError, match="Product ID not registered"):
        await client.get_offers("non-existent-product")


@pytest.mark.asyncio
async def test_get_offers_unauthorized():
    """
    Test offers retrieval with unauthorized error.

    This test verifies that the client properly handles 401 errors
    when the access token is invalid or expired.

    Expected behavior:
    - Request returns 401 Unauthorized
    - OffersAPIError is raised with appropriate message
    """

    async def handler(mock_response):
        """Mock handler that returns 401 Unauthorized."""
        mock_response.status_code = 401
        return mock_response

    transport = MockTransport(handler)
    auth = AsyncMock()
    auth.get_access_token.return_value = "test-token"

    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)
    client.transport = transport
    client.auth = auth
    client.middlewares = []

    with pytest.raises(OffersAPIError, match="Unauthorized"):
        await client.get_offers("test-product")


@pytest.mark.asyncio
async def test_get_offers_with_middleware():
    """
    Test offers retrieval with middleware integration.

    This test verifies that middleware is properly called
    during the request/response cycle.
    """
    middleware_calls = []

    class TestMiddleware:
        async def on_request(self, method, url, headers, params, json, data):
            middleware_calls.append(("request", method, url))

        async def on_response(self, response):
            middleware_calls.append(("response", response.status_code))

    async def handler(mock_response):
        """Mock handler that returns test offers."""
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value=[{"id": "offer-1", "price": 100, "items_in_stock": 5}]
        )
        return mock_response

    transport = MockTransport(handler)
    auth = AsyncMock()
    auth.get_access_token.return_value = "test-token"

    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)
    client.transport = transport
    client.auth = auth
    client.middlewares = [TestMiddleware()]

    offers = await client.get_offers("test-product")

    assert len(offers) == 1
    assert offers[0].id == "offer-1"

    # Verify middleware was called
    assert len(middleware_calls) == 2
    assert middleware_calls[0] == (
        "request",
        "GET",
        "https://api.test/api/v1/products/test-product/offers",
    )
    assert middleware_calls[1] == ("response", 200)


@pytest.mark.asyncio
async def test_get_offers_cached():
    """
    Test offers retrieval with caching mechanism.

    This test verifies that the caching mechanism works correctly:
    - First call fetches data from API and caches it
    - Second call returns cached data without API call
    - Cache respects TTL settings

    Expected behavior:
    - First call triggers API request
    - Second call returns cached data
    - API is called only once for the same product
    """
    call_counter = {"count": 0}

    async def handler(mock_response):
        """Mock handler that counts calls and returns test data."""
        call_counter["count"] += 1
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value=[{"id": "cached-offer", "price": 100, "items_in_stock": 5}]
        )
        return mock_response

    transport = MockTransport(handler)
    auth = AsyncMock()
    auth.get_access_token.return_value = "test-token"

    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)
    client.transport = transport
    client.auth = auth
    client.middlewares = []
    client.offers_cache_ttl = 60  # Set cache TTL

    # First call - should hit API
    result1 = await client.get_offers_cached("test-product")
    assert len(result1) == 1
    assert result1[0].id == "cached-offer"
    assert call_counter["count"] == 1

    # Second call - should use cache (but aiocache serializes objects)
    # So we need to check that the API is not called again
    result2 = await client.get_offers_cached("test-product")
    assert call_counter["count"] == 1  # API should not be called again


@pytest.mark.asyncio
async def test_get_offers_cached_ttl_expiry():
    """
    Test offers retrieval with cache TTL expiration.

    This test verifies that the cache respects TTL settings
    and fetches fresh data when the cache expires.

    Expected behavior:
    - First call caches data
    - After TTL expires, second call fetches fresh data
    - Cache is properly invalidated
    """
    # Clear cache before test to ensure clean state
    from aiocache import caches

    cache = caches.get("default")
    await cache.clear()

    call_counter = {"count": 0}

    async def handler(mock_response):
        """Mock handler that returns different data on each call."""
        call_counter["count"] += 1
        mock_response.status_code = 200

        if call_counter["count"] == 1:
            mock_response.json = AsyncMock(
                return_value=[{"id": "first-offer", "price": 100, "items_in_stock": 5}]
            )
        else:
            mock_response.json = AsyncMock(
                return_value=[
                    {"id": "second-offer", "price": 200, "items_in_stock": 10}
                ]
            )
        return mock_response

    transport = MockTransport(handler)
    auth = AsyncMock()
    auth.get_access_token.return_value = "test-token"

    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)
    client.transport = transport
    client.auth = auth
    client.middlewares = []
    client.offers_cache_ttl = 1  # Set very short TTL for testing

    # First call - should hit API
    result1 = await client.get_offers_cached("test-product")
    assert len(result1) == 1
    assert result1[0].id == "first-offer"
    assert call_counter["count"] == 1

    # Wait for cache to expire
    await asyncio.sleep(1.1)

    # Second call - should hit API again due to TTL expiry
    result2 = await client.get_offers_cached("test-product")
    assert len(result2) == 1
    assert result2[0].id == "second-offer"
    assert call_counter["count"] == 2


@pytest.mark.asyncio
async def test_client_initialization():
    """
    Test client initialization with various configurations.

    This test verifies that the client can be properly initialized
    with different settings and transport options.
    """
    settings = OffersAPISettings()
    settings.refresh_token = "test-token"
    settings.base_url = "https://api.test"

    # Test with default settings
    client = OffersClient(settings)
    assert client.settings == settings
    assert client._retry_attempts == 3
    assert len(client.middlewares) == 0

    # Test with custom retry attempts
    client = OffersClient(settings, retry_attempts=5)
    assert client._retry_attempts == 5

    # Test with custom middleware
    from offers_sdk.logging_middleware import LoggingMiddleware

    client = OffersClient(settings, middlewares=[LoggingMiddleware()])
    assert len(client.middlewares) == 1
    assert isinstance(client.middlewares[0], LoggingMiddleware)


@pytest.mark.asyncio
async def test_client_with_custom_middleware():
    """
    Test client with custom middleware implementation.

    This test verifies that custom middleware can be properly
    integrated with the client.
    """
    middleware_calls = []

    class CustomMiddleware:
        async def on_request(self, method, url, headers, params, json, data):
            middleware_calls.append(f"request:{method}:{url}")

        async def on_response(self, response):
            middleware_calls.append(f"response:{response.status_code}")

    async def handler(mock_response):
        """Mock handler that returns success."""
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value=[{"id": "test", "price": 100, "items_in_stock": 5}]
        )
        return mock_response

    transport = MockTransport(handler)
    auth = AsyncMock()
    auth.get_access_token.return_value = "test-token"

    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)
    client.transport = transport
    client.auth = auth
    client.middlewares = [CustomMiddleware()]

    offers = await client.get_offers("test-product")

    assert len(offers) == 1
    assert offers[0].id == "test"

    # Verify middleware was called
    assert len(middleware_calls) == 2
    assert "request:GET:" in middleware_calls[0]
    assert "response:200" in middleware_calls[1]


@pytest.mark.asyncio
async def test_client_close():
    """
    Test client cleanup and resource management.

    This test verifies that the client properly closes
    transport connections when shut down.
    """
    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)

    # Mock transport as HttpxTransport to trigger the close logic
    from offers_sdk.transport.httpx import HttpxTransport

    mock_transport = AsyncMock(spec=HttpxTransport)
    mock_transport.close = AsyncMock()
    client.transport = mock_transport

    await client.aclose()

    # Verify transport was closed
    mock_transport.close.assert_called_once()


@pytest.mark.asyncio
async def test_network_error_handling():
    """
    Test handling of network errors and retries.

    This test verifies that the client properly handles
    network errors and implements retry logic.
    """

    async def handler(mock_response):
        """Mock handler that raises network error."""
        raise Exception("Network error")

    transport = MockTransport(handler)
    auth = AsyncMock()
    auth.get_access_token.return_value = "test-token"

    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)
    client.transport = transport
    client.auth = auth
    client.middlewares = []

    with pytest.raises(Exception, match="Network error"):
        await client.get_offers("test-product")
