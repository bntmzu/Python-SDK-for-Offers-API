import asyncio
from typing import Any

import requests

from .base import BaseTransport
from .base import UnifiedResponse


class RequestsTransport(BaseTransport):
    """
    Sync transport implementation using requests.Session.

    This transport wraps the synchronous requests library in an async interface
    to provide compatibility with the async-first SDK design.

    Note: This is a compatibility layer for users who need to use requests
    in an async context. For best performance, use httpx or aiohttp.
    """

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout
        self._session = requests.Session()

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
        Async wrapper around synchronous requests.

        This method runs the synchronous requests call in a thread pool
        to avoid blocking the event loop.
        """
        # Run sync requests in thread pool to avoid blocking
        loop = asyncio.get_event_loop()

        def make_request() -> requests.Response:
            return self._session.request(
                method=method,
                url=url,
                headers=headers or {},
                params=params or {},
                json=json,
                data=data,
                timeout=timeout or self._timeout,
            )

        response = await loop.run_in_executor(None, make_request)
        return UnifiedResponse(response)

    async def close(self):
        """
        Async wrapper for closing the session.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._session.close)
