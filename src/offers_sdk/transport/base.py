import asyncio
from typing import Any


class UnifiedResponse:
    """
    Unified response wrapper that handles differences between HTTP clients.
    Provides consistent async interface regardless of the underlying transport.
    """

    def __init__(self, response):
        self._response = response
        self.status_code = response.status_code
        self.text = (
            response.text if hasattr(response, "text") else str(response.content)
        )
        self.headers = response.headers if hasattr(response, "headers") else {}

    async def json(self):
        """
        Unified JSON parsing that works with both sync and async HTTP clients.
        """
        if hasattr(self._response, "json") and callable(self._response.json):
            if asyncio.iscoroutinefunction(self._response.json):
                return await self._response.json()
            else:
                return self._response.json()
        raise NotImplementedError("Response doesn't support .json()")


class BaseTransport:
    """
    Abstract transport layer interface for Offers SDK.
    All HTTP client backends should inherit from this class.

    Supported transports:
    - httpx: Native async HTTP client
    - aiohttp: Native async HTTP client
    - requests: Sync HTTP client wrapped in async interface
    """

    async def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        timeout: float | None = None,
    ) -> UnifiedResponse:
        """
        Async request method for all transports.
        Override this method in transport implementations.
        """
        raise NotImplementedError(
            "Transport implementations must override this method."
        )
