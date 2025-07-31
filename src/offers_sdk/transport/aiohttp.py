import aiohttp
from typing import Any, Dict, Optional

from .base import BaseTransport


class AiohttpTransport(BaseTransport):
    """
    Async transport implementation using aiohttp.ClientSession.
    """

    def __init__(self, timeout: float = 10.0):
        self._timeout = timeout
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout)
        )

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        timeout: Optional[float] = None,
    ) -> aiohttp.ClientResponse:
        async with self._session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data,
            timeout=timeout or self._timeout,
        ) as response:
            return response

    async def close(self):
        await self._session.close()
