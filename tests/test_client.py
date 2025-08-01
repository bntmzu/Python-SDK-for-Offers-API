"""
tests/test_client.py

Unit tests for OffersClient, covering register_product and get_offers workflows,
including success, retry on 401, conflict, not found, and validation errors.
"""

import pytest
import asyncio
from aiocache import caches
from http import HTTPStatus
from offers_sdk.client import OffersClient, OffersAPIError
from offers_sdk.config import OffersAPISettings
from offers_sdk.generated.models import (
    RegisterProductRequest,
    RegisterProductResponse,
    OfferResponse,
    HTTPValidationError,
    ValidationError,
)
from offers_sdk.generated.types import Response
from offers_sdk.generated.api.default import (
    register_product_api_v1_products_register_post,
    get_offers_api_v1_products_product_id_offers_get,
)


@pytest.fixture
def settings(monkeypatch):
    """
    Fixture to set environment variables and return configured OffersAPISettings.
    """
    monkeypatch.setenv("OFFERS_API_REFRESH_TOKEN", "rtoken")
    monkeypatch.setenv("OFFERS_API_BASE_URL", "https://api.test")
    monkeypatch.setenv("OFFERS_API_TIMEOUT", "1")
    monkeypatch.setenv("OFFERS_API_TRANSPORT", "httpx")
    return OffersAPISettings()


@pytest.fixture
def client(settings):
    """Fixture to instantiate OffersClient with provided settings."""
    return OffersClient(settings)


@pytest.mark.asyncio
async def test_register_product_success(monkeypatch, client):
    """
    GIVEN a valid RegisterProductRequest
    WHEN the register_product endpoint returns 201
    THEN the method returns a RegisterProductResponse instance.
    """

    async def _fake_get_access():
        return "atoken"

    monkeypatch.setattr(client.auth, "get_access_token", _fake_get_access)

    async def _fake_register(*_args, **_kwargs):
        return Response(
            status_code=HTTPStatus.CREATED,
            content=b"",
            headers={},
            parsed=RegisterProductResponse(id="1234"),
        )

    monkeypatch.setattr(
        register_product_api_v1_products_register_post,
        "asyncio_detailed",
        _fake_register,
    )

    req = RegisterProductRequest(id="1234", name="Name", description="Desc")
    result = await client.register_product(req)
    assert isinstance(result, RegisterProductResponse)
    assert result.id == "1234"


@pytest.mark.asyncio
async def test_register_product_401_then_success(monkeypatch, client):
    """
    GIVEN a stale access token causing 401
    WHEN refresh_access_token updates it and endpoint returns 201
    THEN register_product succeeds on retry.
    """

    async def _fake_get_access():
        return "old"

    async def _fake_refresh():
        setattr(client.auth, "_access_token", "new")

    monkeypatch.setattr(client.auth, "get_access_token", _fake_get_access)
    monkeypatch.setattr(client.auth, "refresh_access_token", _fake_refresh)

    calls = []

    async def _fake_register(*_args, **_kwargs):
        if not calls:
            calls.append(1)
            return Response(
                status_code=HTTPStatus.UNAUTHORIZED,
                content=b"",
                headers={},
                parsed=None,
            )
        return Response(
            status_code=HTTPStatus.CREATED,
            content=b"",
            headers={},
            parsed=RegisterProductResponse(id="xyz"),
        )

    monkeypatch.setattr(
        register_product_api_v1_products_register_post,
        "asyncio_detailed",
        _fake_register,
    )

    req = RegisterProductRequest(id="xyz", name="N", description="D")
    result = await client.register_product(req)
    assert result.id == "xyz"


@pytest.mark.asyncio
async def test_register_product_conflict(monkeypatch, client):
    """
    GIVEN a conflict response (409)
    WHEN register_product is called
    THEN an OffersAPIError indicating conflict is raised.
    """

    async def _fake_get_access():
        return "atoken"

    monkeypatch.setattr(client.auth, "get_access_token", _fake_get_access)

    async def _fake_register(*_args, **_kwargs):
        return Response(
            status_code=HTTPStatus.CONFLICT, content=b"", headers={}, parsed=None
        )

    monkeypatch.setattr(
        register_product_api_v1_products_register_post,
        "asyncio_detailed",
        _fake_register,
    )
    with pytest.raises(OffersAPIError) as exc:
        await client.register_product(
            RegisterProductRequest(id="1", name="N", description="D")
        )
    assert "already registered" in str(exc.value)


@pytest.mark.asyncio
async def test_get_offers_success(monkeypatch, client):
    """
    GIVEN a valid product_id
    WHEN get_offers endpoint returns 200 with list
    THEN method returns list of OfferResponse.
    """

    async def _fake_get_access():
        return "atoken"

    monkeypatch.setattr(client.auth, "get_access_token", _fake_get_access)

    async def _fake_offers(*_args, **_kwargs):
        return Response(
            status_code=HTTPStatus.OK,
            content=b"",
            headers={},
            parsed=[OfferResponse(id="o1", price=100, items_in_stock=5)],
        )

    monkeypatch.setattr(
        get_offers_api_v1_products_product_id_offers_get,
        "asyncio_detailed",
        _fake_offers,
    )
    offers = await client.get_offers("pid")
    assert isinstance(offers, list)
    assert offers[0].id == "o1"


@pytest.mark.asyncio
async def test_get_offers_not_found(monkeypatch, client):
    """
    GIVEN a non-existent product_id
    WHEN get_offers returns 404
    THEN an OffersAPIError for not registered is raised.
    """

    async def _fake_get_access():
        return "atoken"

    monkeypatch.setattr(client.auth, "get_access_token", _fake_get_access)

    async def _fake_offers_nf(*_args, **_kwargs):
        return Response(
            status_code=HTTPStatus.NOT_FOUND, content=b"", headers={}, parsed=None
        )

    monkeypatch.setattr(
        get_offers_api_v1_products_product_id_offers_get,
        "asyncio_detailed",
        _fake_offers_nf,
    )
    with pytest.raises(OffersAPIError) as exc:
        await client.get_offers("pid")
    assert "not registered" in str(exc.value)


@pytest.mark.asyncio
async def test_validation_error(monkeypatch, client):
    """
    GIVEN invalid request body
    WHEN API returns 422 with HTTPValidationError
    THEN OffersAPIError with details is raised.
    """

    async def _fake_get_access():
        return "atoken"

    monkeypatch.setattr(client.auth, "get_access_token", _fake_get_access)

    err = HTTPValidationError(
        detail=[ValidationError(loc=["body"], msg="bad", type="value_error")]
    )

    async def _fake_register_err(*_args, **_kwargs):
        return Response(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            content=b"",
            headers={},
            parsed=err,
        )

    monkeypatch.setattr(
        register_product_api_v1_products_register_post,
        "asyncio_detailed",
        _fake_register_err,
    )
    with pytest.raises(OffersAPIError) as exc:
        await client.register_product(
            RegisterProductRequest(id="1", name="n", description="d")
        )
    assert "Validation error" in str(exc.value)
    assert exc.value.details == err.detail

# === Tests for caching and TTL ===

@pytest.mark.asyncio
async def test_get_offers_cached(monkeypatch, client):
    """
    GIVEN multiple calls to get_offers_cached with the same product_id
    WHEN the data is requested for the second time within TTL
    THEN the result should come from cache and not trigger a second API call
    """
    async def _fake_get_access():
        return "atoken"
    monkeypatch.setattr(client.auth, "get_access_token", _fake_get_access)

    call_counter = {"n": 0}

    async def _fake_offers(*_args, **_kwargs):
        call_counter["n"] += 1
        return Response(
            status_code=HTTPStatus.OK,
            content=b"",
            headers={},
            parsed=[OfferResponse(id="c1", price=99, items_in_stock=99)],
        )

    monkeypatch.setattr(
        get_offers_api_v1_products_product_id_offers_get,
        "asyncio_detailed",
        _fake_offers,
    )

    result1 = await client.get_offers_cached("cachetest1")
    result2 = await client.get_offers_cached("cachetest1")

    assert result1[0].id == "c1"
    assert result2[0].id == "c1"
    assert call_counter["n"] == 1  # API should be called only once (cached)


@pytest.mark.asyncio
async def test_get_offers_cached_ttl(monkeypatch, client):
    """
    GIVEN a short cache TTL and two sequential calls outside TTL window
    WHEN the cache expires between calls
    THEN the method should fetch fresh data from the API on the second call
    """
    async def _fake_get_access():
        return "atoken"
    monkeypatch.setattr(client.auth, "get_access_token", _fake_get_access)

    offers_first = [OfferResponse(id="ttlA", price=10, items_in_stock=1)]
    offers_second = [OfferResponse(id="ttlB", price=20, items_in_stock=2)]
    resp_first = Response(status_code=HTTPStatus.OK, content=b"", headers={}, parsed=offers_first)
    resp_second = Response(status_code=HTTPStatus.OK, content=b"", headers={}, parsed=offers_second)

    sequence = [resp_first, resp_second]

    async def _mock_response(*_args, **_kwargs):
        return sequence.pop(0)

    monkeypatch.setattr(
        get_offers_api_v1_products_product_id_offers_get,
        "asyncio_detailed",
        _mock_response,
    )

    client.offers_cache_ttl = 1  # Set very short TTL (1s)

    r1 = await client.get_offers_cached("prodTTL")
    assert r1[0].id == "ttlA"

    r2 = await client.get_offers_cached("prodTTL")
    assert r2[0].id == "ttlA"  # Still cached

    await asyncio.sleep(1.1)  # Wait until TTL expires

    r3 = await client.get_offers_cached("prodTTL")
    assert r3[0].id == "ttlB"  # Fresh value

    await caches.get('default').clear()  # Cleanup cache