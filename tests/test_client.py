"""
tests/test_client.py

Unit tests for OffersClient, covering register_product and get_offers workflows,
including success, retry on 401, conflict, not found, and validation errors.
"""
import pytest

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
            return Response(status_code=HTTPStatus.UNAUTHORIZED, content=b"", headers={}, parsed=None)
        return Response(status_code=HTTPStatus.CREATED, content=b"", headers={}, parsed=RegisterProductResponse(id="xyz"))
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
        return Response(status_code=HTTPStatus.CONFLICT, content=b"", headers={}, parsed=None)
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
        return Response(status_code=HTTPStatus.OK, content=b"", headers={}, parsed=[OfferResponse(id="o1", price=100, items_in_stock=5)])
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
        return Response(status_code=HTTPStatus.NOT_FOUND, content=b"", headers={}, parsed=None)
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

    err = HTTPValidationError(detail=[ValidationError(loc=["body"], msg="bad", type="value_error")])

    async def _fake_register_err(*_args, **_kwargs):
        return Response(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, content=b"", headers={}, parsed=err)
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
