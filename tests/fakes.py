"""
Test utilities and mock objects for Offers SDK.

This module provides mock transport implementations and fake response objects
for testing the SDK without making real HTTP requests. These utilities help
isolate the SDK's business logic from external dependencies.
"""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from offers_sdk.transport.base import UnifiedResponse


class FakeResponse:
    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self._text = text
        self._json = json_data or {}

    @property
    def text(self):
        return self._text

    def json(self):
        return self._json


class MockTransport:
    """Mock transport for testing."""

    def __init__(self, handler=None):
        """
        Initialize mock transport.

        Args:
            handler: Optional async function that takes a request and returns a response.
                   If not provided, uses default mock response.
        """
        self.handler = handler
        self.request_calls = []
        self.closed = False

    @property
    def request_count(self):
        """Number of requests made to this transport."""
        return len(self.request_calls)

    async def request(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        json: dict | None = None,
        data: dict | None = None,
        timeout: float | None = None,
    ) -> UnifiedResponse:
        """Mock request method."""
        self.request_calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers or {},
                "params": params or {},
                "json": json,
                "data": data,
                "timeout": timeout,
            }
        )

        if self.handler:
            # Use custom handler if provided
            request = MagicMock()
            request.method = method
            request.url = url
            request.headers = headers or {}
            request.json = json

            response = await self.handler(request)
            return UnifiedResponse(response)
        else:
            # Use default mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_response.json = AsyncMock(return_value={"id": "test-product"})

            return UnifiedResponse(mock_response)

    async def close(self):
        """Mock close method."""
        self.closed = True
