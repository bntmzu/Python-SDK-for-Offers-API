from typing import Any

import httpx

from .base import BaseTransport
from .base import UnifiedResponse


class HttpxTransport(BaseTransport):
    """
    Async transport implementation using httpx.AsyncClient.
    """

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=self._timeout)

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
        response = await self._client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data,
            timeout=timeout or self._timeout,
        )
        return UnifiedResponse(response)

    async def close(self):
        await self._client.aclose()
