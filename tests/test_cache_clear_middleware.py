import logging

import pytest
from aiocache import caches

from offers_sdk.cache_clear_middleware import CacheClearMiddleware
from offers_sdk.transport.base import UnifiedResponse


class MockResponse:
    """Mock response for testing."""

    def __init__(self, status_code, json_data=None, text="", url=""):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data or {}
        self._url = url

    async def json(self):
        return self._json_data


@pytest.mark.asyncio
async def test_cache_clear_middleware_deletes_correct_key():
    """
    Test that CacheClearMiddleware deletes the correct cache key
    when a product is successfully registered.
    """
    # Setup cache with test data
    cache = caches.get("default")
    await cache.set("offers:test-product", "cached data")

    # Verify data exists
    value = await cache.get("offers:test-product")
    assert value == "cached data"

    # Create middleware
    middleware = CacheClearMiddleware()

    # Create mock response for successful registration
    mock_response = MockResponse(
        201, {"id": "test-product"}, url="/api/v1/products/register"
    )
    unified_response = UnifiedResponse(mock_response)

    # Simulate successful registration
    await middleware.on_response(unified_response)

    # Verify cache was cleared
    value = await cache.get("offers:test-product")
    assert value is None


@pytest.mark.asyncio
async def test_cache_clear_middleware_does_not_clear_on_non_201():
    """
    Test that CacheClearMiddleware does not clear cache
    when response status is not 201.
    """
    # Setup cache with test data
    cache = caches.get("default")
    await cache.set("offers:test-product", "cached data")

    # Create middleware
    middleware = CacheClearMiddleware()

    # Create mock response for non-201 status
    mock_response = MockResponse(
        200, {"id": "test-product"}, url="/api/v1/products/register"
    )
    unified_response = UnifiedResponse(mock_response)

    # Simulate non-201 response
    await middleware.on_response(unified_response)

    # Verify cache was not cleared
    value = await cache.get("offers:test-product")
    assert value == "cached data"


@pytest.mark.asyncio
async def test_cache_clear_middleware_skips_if_parsed_is_none():
    """
    Test that CacheClearMiddleware skips cache clearing
    when response JSON parsing fails.
    """
    # Setup cache with test data
    cache = caches.get("default")
    await cache.set("offers:test-product", "cached data")

    # Create middleware
    middleware = CacheClearMiddleware()

    # Create mock response with None JSON data
    mock_response = MockResponse(201, None, url="/api/v1/products/register")
    unified_response = UnifiedResponse(mock_response)

    # Simulate response with None JSON
    await middleware.on_response(unified_response)

    # Verify cache was not cleared
    value = await cache.get("offers:test-product")
    assert value == "cached data"


@pytest.mark.asyncio
async def test_cache_clear_middleware_skips_if_no_id():
    """
    Test that CacheClearMiddleware skips cache clearing
    when response does not contain product ID.
    """
    # Setup cache with test data
    cache = caches.get("default")
    await cache.set("offers:test-product", "cached data")

    # Create middleware
    middleware = CacheClearMiddleware()

    # Create mock response without product ID
    mock_response = MockResponse(
        201, {"name": "test-product"}, url="/api/v1/products/register"
    )
    unified_response = UnifiedResponse(mock_response)

    # Simulate response without product ID
    await middleware.on_response(unified_response)

    # Verify cache was not cleared
    value = await cache.get("offers:test-product")
    assert value == "cached data"


@pytest.mark.asyncio
async def test_cache_clear_skips_on_409():
    """
    Test that CacheClearMiddleware does not clear cache
    when response status is 409 (Conflict).
    """
    # Setup cache with test data
    cache = caches.get("default")
    await cache.set("offers:test-product", "cached data")

    # Create middleware
    middleware = CacheClearMiddleware()

    # Create mock response for 409 status
    mock_response = MockResponse(
        409, {"id": "test-product"}, url="/api/v1/products/register"
    )
    unified_response = UnifiedResponse(mock_response)

    # Simulate 409 response
    await middleware.on_response(unified_response)

    # Verify cache was not cleared
    value = await cache.get("offers:test-product")
    assert value == "cached data"


@pytest.mark.asyncio
async def test_cache_clear_ignores_non_201_status():
    """
    Test that CacheClearMiddleware ignores all non-201 status codes.
    """
    # Setup cache with test data
    cache = caches.get("default")
    await cache.set("offers:test-product", "cached data")

    # Create middleware
    middleware = CacheClearMiddleware()

    # Test various non-201 status codes
    for status_code in [200, 400, 401, 403, 404, 409, 422, 500]:
        mock_response = MockResponse(
            status_code, {"id": "test-product"}, url="/api/v1/products/register"
        )
        unified_response = UnifiedResponse(mock_response)

        await middleware.on_response(unified_response)

        # Verify cache was not cleared
        value = await cache.get("offers:test-product")
        assert value == "cached data"


@pytest.mark.asyncio
async def test_cache_clear_handles_deletion_error(caplog):
    """
    Test that CacheClearMiddleware handles cache deletion errors gracefully.
    """
    # Setup logging
    caplog.set_level(logging.ERROR)

    # Setup cache with test data
    cache = caches.get("default")
    await cache.set("offers:test-product", "cached data")

    # Create middleware with mock cache that raises exception
    middleware = CacheClearMiddleware()

    # Mock the cache delete method to raise an exception
    async def failing_delete(key):
        raise Exception("Cache deletion failed")

    middleware._cache.delete = failing_delete

    # Create mock response for successful registration
    mock_response = MockResponse(
        201, {"id": "test-product"}, url="/api/v1/products/register"
    )
    unified_response = UnifiedResponse(mock_response)

    # Simulate successful registration with failing cache
    await middleware.on_response(unified_response)

    # Verify error was logged
    assert "Failed to delete cache" in caplog.text
