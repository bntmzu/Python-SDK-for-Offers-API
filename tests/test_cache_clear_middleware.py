import pytest
import logging
from http import HTTPStatus
from aiocache import caches
from offers_sdk.cache_clear_middleware import CacheClearMiddleware
from offers_sdk.generated.models import RegisterProductResponse
from offers_sdk.generated.types import Response


@pytest.mark.asyncio
async def test_cache_clear_middleware_deletes_correct_key():
    """
    GIVEN a cached offer for a product_id
    WHEN register_product returns 201 Created
    THEN CacheClearMiddleware should delete the corresponding cache entry
    """
    # Setup: create cache and set key
    product_id = "test-product-123"
    cache_key = f"offers:{product_id}"
    cache = caches.get("default")
    await cache.set(cache_key, "cached data", ttl=60)
    assert await cache.get(cache_key) == "cached data"

    # Create a fake successful response from register_product
    response = Response(
        status_code=HTTPStatus.CREATED,
        content=b"",
        headers={},
        parsed=RegisterProductResponse(id=product_id),
    )

    # Act: pass response to middleware
    middleware = CacheClearMiddleware()
    await middleware.on_response(response)

    # Assert: cache entry is deleted
    value = await cache.get(cache_key)
    assert value is None

@pytest.mark.asyncio
async def test_cache_clear_middleware_does_not_clear_on_non_201():
    """
    GIVEN a response with status != 201
    WHEN on_response is called
    THEN the cache should not be touched
    """
    product_id = "non-201-product"
    key = f"offers:{product_id}"
    cache = caches.get("default")
    await cache.set(key, "data", ttl=60)

    response = Response(
        status_code=HTTPStatus.BAD_REQUEST,
        content=b"",
        headers={},
        parsed=RegisterProductResponse(id=product_id),
    )

    middleware = CacheClearMiddleware()
    await middleware.on_response(response)

    assert await cache.get(key) == "data"
    await cache.delete(key)

@pytest.mark.asyncio
async def test_cache_clear_middleware_skips_if_parsed_is_none():
    """
    GIVEN a response with status 201 but no parsed data
    WHEN on_response is called
    THEN cache should not be cleared
    """
    cache = caches.get("default")
    await cache.set("offers:xyz", "something", ttl=60)

    response = Response(
        status_code=HTTPStatus.CREATED,
        content=b"",
        headers={},
        parsed=None,
    )

    middleware = CacheClearMiddleware()
    await middleware.on_response(response)

    assert await cache.get("offers:xyz") == "something"
    await cache.delete("offers:xyz")

class FakeParsed:
    def __init__(self):
        self.id = None  # no product_id


@pytest.mark.asyncio
async def test_cache_clear_middleware_skips_if_no_id():
    """
    GIVEN a response with parsed object but no ID
    WHEN on_response is called
    THEN cache should not be cleared
    """
    cache = caches.get("default")
    await cache.set("offers:none", "something", ttl=60)

    response = Response(
        status_code=HTTPStatus.CREATED,
        content=b"",
        headers={},
        parsed=FakeParsed(),
    )

    middleware = CacheClearMiddleware()
    await middleware.on_response(response)

    assert await cache.get("offers:none") == "something"
    await cache.delete("offers:none")

@pytest.mark.asyncio
async def test_cache_clear_skips_on_409(monkeypatch):
    """
    GIVEN a 409 Conflict response (product already exists)
    WHEN on_response is called
    THEN cache should not be cleared
    """
    mw = CacheClearMiddleware()
    from aiocache import caches
    cache = caches.get("default")
    await cache.set("offers:prod-409", "keep", ttl=60)

    response = Response(
        status_code=HTTPStatus.CONFLICT,
        content=b"",
        headers={},
        parsed=RegisterProductResponse(id="prod-409"),
    )

    await mw.on_response(response)

    value = await cache.get("offers:prod-409")
    assert value == "keep"

@pytest.mark.asyncio
async def test_cache_clear_ignores_non_201_status(monkeypatch):
    """
    GIVEN a 200 OK response
    WHEN on_response is called
    THEN middleware should skip cache deletion
    """
    mw = CacheClearMiddleware()
    from aiocache import caches
    cache = caches.get("default")
    await cache.set("offers:prod-200", "keep", ttl=60)

    response = Response(
        status_code=HTTPStatus.OK,
        content=b"",
        headers={},
        parsed=RegisterProductResponse(id="prod-200"),
    )

    await mw.on_response(response)

    value = await cache.get("offers:prod-200")
    assert value == "keep"

@pytest.mark.asyncio
async def test_cache_clear_handles_deletion_error(monkeypatch, caplog):
    """
    GIVEN a cache backend that raises an error on delete
    WHEN on_response is called
    THEN middleware logs the error but does not crash
    """
    mw = CacheClearMiddleware()

    async def failing_delete(*_args, **_kwargs):
        raise Exception("boom")

    from aiocache import caches
    monkeypatch.setattr(caches.get("default"), "delete", failing_delete)

    caplog.set_level(logging.ERROR, logger="offers_sdk.middleware.cache_clear")

    response = Response(
        status_code=HTTPStatus.CREATED,
        content=b"",
        headers={},
        parsed=RegisterProductResponse(id="prod-error"),
    )

    await mw.on_response(response)

    assert "Failed to delete cache" in caplog.text
