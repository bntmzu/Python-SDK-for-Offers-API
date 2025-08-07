import pytest
from offers_sdk.auth import AuthManager
from offers_sdk.config import OffersAPISettings
from offers_sdk.client import OffersClient
from offers_sdk.generated.models import RegisterProductRequest
from unittest.mock import AsyncMock, patch

import time


@pytest.mark.asyncio
async def test_get_access_token_from_valid_cache():
    """
    GIVEN: a mock cache with valid token
    WHEN: we call get_access_token
    THEN: token should be returned from cache
    """
    # given: mock cache with valid token
    mock_token_data = {
        "access_token": "valid-token-123",
        "expires_at": time.time() + 300,  # 5 minutes from now
    }

    mock_token_store = AsyncMock()
    mock_token_store.load.return_value = mock_token_data

    settings = OffersAPISettings()
    settings.refresh_token = "test-refresh-token"
    settings.base_url = "https://api.test"

    auth = AuthManager(settings, token_store=mock_token_store)

    # when: we call get_access_token
    result = await auth.get_access_token()

    # then: token should be returned from cache
    assert result == "valid-token-123"
    mock_token_store.load.assert_called_once()


@pytest.mark.asyncio
async def test_expired_token_triggers_refresh():
    """
    GIVEN: expired token in cache
    WHEN: we call get_access_token
    THEN: refresh should occur
    """
    # given: expired token in cache
    expired_token_data = {
        "access_token": "expired-token-123",
        "expires_at": time.time() - 300,  # 5 minutes ago
    }

    # new token that should be returned from API
    new_token_data = {"access_token": "new-token-456", "expires_at": time.time() + 300}

    mock_token_store = AsyncMock()
    mock_token_store.load.return_value = expired_token_data

    settings = OffersAPISettings()
    settings.refresh_token = "test-refresh-token"
    settings.base_url = "https://api.test"

    auth = AuthManager(settings, token_store=mock_token_store)

    # Mock the HTTP response
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.json = AsyncMock(return_value=new_token_data)

        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.post.return_value = mock_response

        mock_client.return_value = mock_async_client

        # when: we request token
        result = await auth.get_access_token()

        # then: refresh should occur
        assert result == "new-token-456"
        mock_token_store.save.assert_called_once()


class DummyTransport:
    def __init__(self):
        self.call_count = 0

    async def request(self, method, url, headers=None, json=None):
        self.call_count += 1
        if self.call_count == 1:

            class Response:
                status_code = 401
                text = "Unauthorized"

                def json(self):
                    return {}

            return Response()
        else:

            class Response:
                status_code = 201

                def json(self):
                    return {"id": json["id"]}

            return Response()


class DummyAuth:
    def __init__(self):
        self.call_count = 0
        self._access_token = "old_token"

    async def get_access_token(self):
        self.call_count += 1
        return f"token_{self.call_count}"


@pytest.mark.asyncio
async def test_register_product_retry_on_401():
    """
    GIVEN: first request returns 401, second succeeds
    WHEN: we register a product
    THEN: it should retry and succeed
    """
    # First return 401
    first_response = AsyncMock()
    first_response.status_code = 401
    first_response.text = "Unauthorized"

    # Then success
    second_response = AsyncMock()
    second_response.status_code = 201
    second_response.json = AsyncMock(return_value={"id": "xyz"})

    mock_transport = AsyncMock()
    mock_transport.request.side_effect = [first_response, second_response]

    mock_auth = AsyncMock()
    mock_auth.get_access_token.side_effect = ["old-token", "new-token"]

    # Settings without .env
    settings = OffersAPISettings()
    settings.base_url = "https://api.test"

    client = OffersClient(settings)
    # Override transport and auth
    client.transport = mock_transport
    client.auth = mock_auth
    client.middlewares = []

    req = RegisterProductRequest(id="xyz", name="Test", description="Desc")
    result = await client.register_product(req)

    assert result.id == "xyz"
    assert mock_transport.request.call_count == 2
    assert mock_auth.get_access_token.call_count == 2
