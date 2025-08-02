import asyncio
import requests
from typing import Any, Dict, Optional

from .base import BaseTransport, UnifiedResponse


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
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        timeout: Optional[float] = None,
    ) -> UnifiedResponse:
        """
        Async wrapper around synchronous requests.

        This method runs the synchronous requests call in a thread pool
        to avoid blocking the event loop.
        """
        # Run sync requests in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self._session.request,
            method,
            url,
            headers or {},
            params or {},
            json,
            data,
            timeout or self._timeout,
        )
        return UnifiedResponse(response)

    async def close(self):
        """
        Async wrapper for closing the session.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._session.close)
