"""
Aiohttp transport implementation for Offers SDK.

This module provides AiohttpTransport, an alternative async HTTP client for the SDK.
Aiohttp is a mature async HTTP client with advanced features like connection pooling,
automatic retries, and comprehensive timeout handling.

Features:
- Full async/await support
- Automatic connection pooling
- Advanced timeout configuration
- Built-in retry mechanisms
- WebSocket support (if needed)
"""

from typing import Any

import aiohttp

from .base import BaseTransport
from .base import UnifiedResponse


class AiohttpTransport(BaseTransport):
    """
    Async transport implementation using aiohttp.ClientSession.
    """

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout
        self._session: aiohttp.ClientSession | None = None

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
        # Create session if not exists
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout)
            )

        timeout_obj = aiohttp.ClientTimeout(total=timeout or self._timeout)
        async with self._session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data,
            timeout=timeout_obj,
        ) as response:
            return UnifiedResponse(response)

    async def close(self):
        if self._session:
            await self._session.close()
