#!/usr/bin/env python3
"""
Test script to verify all SDK components work correctly.
"""

import asyncio
import pytest


def test_imports():
    from offers_sdk import (
        OffersClient,
        OffersClientSync,
        OffersAPISettings,
        AuthManager,
        AuthError,
        OffersAPIError,
        Middleware,
        PluginManager,
        RequestPlugin,
        ResponsePlugin,
        TokenStore,
        FileTokenStore,
    )
    from offers_sdk.transport import get_transport
    from offers_sdk.plugins.examples import (
        LoggingPlugin,
        AuthenticationPlugin,
        MetricsPlugin,
    )

    assert True


def test_transports():
    from offers_sdk.transport import get_transport

    get_transport("httpx")
    get_transport("aiohttp")
    get_transport("requests")
    assert True


def test_config():
    from offers_sdk import OffersAPISettings

    settings = OffersAPISettings(
        refresh_token="test-token", base_url="https://api.example.com"
    )
    assert settings.base_url == "https://api.example.com"
    assert settings.transport in ["httpx", "aiohttp", "requests"]
    assert settings.timeout > 0


def test_sync_wrapper():
    from offers_sdk import OffersClientSync, OffersAPISettings

    settings = OffersAPISettings(
        refresh_token="test-token", base_url="https://api.example.com"
    )
    client = OffersClientSync(settings)
    with client as _:
        assert True


def test_cli():
    import subprocess

    result = subprocess.run(
        ["poetry", "run", "offers-cli", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "register" in result.stdout or "get-offers" in result.stdout


@pytest.mark.asyncio
async def test_plugin_manager():
    from offers_sdk import PluginManager
    from offers_sdk.plugins.examples import LoggingPlugin

    manager = PluginManager()
    plugin = LoggingPlugin()
    manager.add_request_plugin(plugin)
    manager.add_response_plugin(plugin)
    await manager.process_request(
        "GET", "https://test.com", {"x": "y"}, None, None, None
    )
    from offers_sdk.transport.base import UnifiedResponse
    from unittest.mock import MagicMock

    resp = UnifiedResponse(MagicMock(status_code=200))
    result = await manager.process_response(resp)
    assert result is not None


@pytest.mark.asyncio
async def test_token_store(tmp_path):
    from offers_sdk import FileTokenStore
    import time

    store = FileTokenStore(tmp_path / "token.json")
    token = "abc123"
    expiry = time.time() + 3600
    await store.save(token, expiry)
    data = await store.load()
    assert data["access_token"] == token
    assert abs(data["expires_at"] - expiry) < 1
    await store.clear()
    assert await store.load() is None


@pytest.mark.asyncio
async def test_middleware():
    from offers_sdk.transport.base import UnifiedResponse
    from unittest.mock import MagicMock

    class DummyMiddleware:
        async def on_request(self, *a, **kw):
            return None

        async def on_response(self, r):
            return r

    mw = DummyMiddleware()
    await mw.on_request("GET", "https://x", {}, None, None, None)
    resp = UnifiedResponse(MagicMock(status_code=200))
    await mw.on_response(resp)
    assert True
