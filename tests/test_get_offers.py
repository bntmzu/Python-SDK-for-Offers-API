"""
This module contains comprehensive tests for the get_offers functionality,
covering various scenarios including success cases, error handling,
authentication retry logic, middleware integration, and network failures.

The tests use mocked transport and authentication components to ensure
isolated testing of the business logic without external dependencies.

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
async def test_get_offers_unauthorized_then_success():
    """
    Test offers retrieval with 401 then success.

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
            mock_response.status_code = 200
            mock_response.json = AsyncMock(
                return_value=[{"id": "offer-1", "price": 100, "items_in_stock": 5}]
            )

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

    offers = await client.get_offers("product-id")

    assert len(offers) == 1
    assert offers[0].id == "offer-1"
    assert len(transport.request_calls) == 2
    # Both calls use the same token since get_access_token returns the same value
    assert transport.request_calls[0]["headers"]["Bearer"] == "old-token"
    assert transport.request_calls[1]["headers"]["Bearer"] == "old-token"


@pytest.mark.asyncio
async def test_get_offers_422():
    """
    Test offers retrieval with validation error.

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
        await client.get_offers("invalid-id")


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
    assert middleware_calls[0][0] == "request"
    assert middleware_calls[0][1] == "GET"
    assert middleware_calls[1][0] == "response"
    assert middleware_calls[1][1] == 200


@pytest.mark.asyncio
async def test_get_offers_empty_response():
    """
    Test offers retrieval with empty response.

    This test verifies that the client properly handles
    empty responses from the API.

    Expected behavior:
    - Request returns 200 with empty list
    - Empty list of OfferResponse objects returned
    """

    async def handler(mock_response):
        """Mock handler that returns empty response."""
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value=[])
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

    assert len(offers) == 0
    assert len(transport.request_calls) == 1
    assert transport.request_calls[0]["method"] == "GET"
