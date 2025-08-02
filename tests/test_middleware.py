import pytest
import logging
from typing import Any, Dict
from http import HTTPStatus
from offers_sdk.client import OffersClient
from offers_sdk.config import OffersAPISettings
from offers_sdk.generated.models import RegisterProductRequest, RegisterProductResponse
from offers_sdk.generated.types import Response
from offers_sdk.generated.api.default import register_product_api_v1_products_register_post
from offers_sdk.logging_middleware import LoggingMiddleware
from offers_sdk.cache_clear_middleware import CacheClearMiddleware
from offers_sdk.middleware import Middleware


class SpyMiddleware(Middleware):
    """
    Middleware that records calls to on_request and on_response for testing purposes.
    """

    def __init__(self):
        self.request_calls: list[Dict[str, Any]] = []
        self.response_calls: list[Response] = []

    async def on_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, Any] | None,
        json: Any,
        data: Any,
    ) -> None:
        self.request_calls.append({
            "method": method,
            "url": url,
            "headers": headers,
            "params": params,
            "json": json,
            "data": data
        })

    async def on_response(self, response: Response) -> None:
        self.response_calls.append(response)


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> OffersAPISettings:
    """
    Fixture to prepare environment variables and return SDK settings.
    """
    monkeypatch.setenv("OFFERS_API_REFRESH_TOKEN", "test")
    monkeypatch.setenv("OFFERS_API_BASE_URL", "https://api.test")
    return OffersAPISettings()


@pytest.mark.asyncio
async def test_register_product_middleware(monkeypatch: pytest.MonkeyPatch, settings: OffersAPISettings):
    """
    Test that middleware is properly invoked during the register_product call.
    """
    spy = SpyMiddleware()
    client = OffersClient(settings, middlewares=[spy])

    async def _fake_get_access_token() -> str:
        return "tok"

    monkeypatch.setattr(client.auth, "get_access_token", _fake_get_access_token)

    async def _fake_register(*_a, **_k) -> Response:
        return Response(
            status_code=HTTPStatus.CREATED,
            content=b"",
            headers={},
            parsed=RegisterProductResponse(id="mid1"),
        )

    monkeypatch.setattr(
        register_product_api_v1_products_register_post,
        "asyncio_detailed",
        _fake_register,
    )

    req = RegisterProductRequest(id="mid1", name="Test", description="Desc")
    result = await client.register_product(req)

    assert result.id == "mid1"
    assert len(spy.request_calls) == 1
    assert len(spy.response_calls) == 1

    request_info = spy.request_calls[0]
    assert request_info["method"] == "POST"
    assert "url" in request_info


@pytest.mark.asyncio
async def test_logging_middleware_logs(caplog: pytest.LogCaptureFixture):
    """
    Test that LoggingMiddleware correctly logs HTTP request and response information.
    """
    middleware = LoggingMiddleware()
    caplog.set_level(logging.INFO, logger="offers_sdk.middleware.logging")

    # Create a valid fake Response object
    response = Response(
        status_code=HTTPStatus.OK,
        content=b"",
        headers={},
        parsed=None,
    )

    await middleware.on_request(
        method="GET",
        url="https://api.test/test",
        headers={"Authorization": "Bearer x"},
        params=None,
        json=None,
        data=None,
    )

    await middleware.on_response(response)

    logs = caplog.text
    assert "Request: GET https://api.test/test" in logs
    assert "Response: 200" in logs
    assert "elapsed=" in logs

@pytest.mark.asyncio
async def test_logging_and_cache_clear_middleware(monkeypatch: pytest.MonkeyPatch,
                                                  settings: OffersAPISettings,
                                                  caplog: pytest.LogCaptureFixture):
    """
    Test that both LoggingMiddleware and CacheClearMiddleware are invoked correctly.
    LoggingMiddleware should log request/response.
    CacheClearMiddleware should remove the cached offer by product_id.
    """
    # Prepare product and cache
    product_id = "test-mw-combo"
    cache_key = f"offers:{product_id}"
    from aiocache import caches
    cache = caches.get("default")
    await cache.set(cache_key, "cached_offer", ttl=60)

    # Init middlewares
    log_mw = LoggingMiddleware()
    clear_mw = CacheClearMiddleware()
    caplog.set_level(logging.INFO, logger="offers_sdk.middleware.logging")

    client = OffersClient(settings, middlewares=[log_mw, clear_mw])

    async def _fake_get_access_token() -> str:
        return "tok"

    monkeypatch.setattr(client.auth, "get_access_token", _fake_get_access_token)

    # Stub register_product response
    async def _fake_register(*_args, **_kwargs):
        return Response(
            status_code=HTTPStatus.CREATED,
            content=b"",
            headers={},
            parsed=RegisterProductResponse(id=product_id),
        )

    monkeypatch.setattr(
        register_product_api_v1_products_register_post,
        "asyncio_detailed",
        _fake_register,
    )

    # Run the call
    req = RegisterProductRequest(id=product_id, name="MW test", description="...")
    result = await client.register_product(req)

    # Assert product registered
    assert result.id == product_id

    # Assert log middleware triggered
    logs = caplog.text
    assert f"Request: POST" in logs
    assert f"Response: 201" in logs
    assert "elapsed=" in logs

    # Assert cache was cleared
    assert await cache.get(cache_key) is None
