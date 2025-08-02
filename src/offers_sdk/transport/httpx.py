import httpx
from typing import Any, Dict, Optional

from .base import BaseTransport, UnifiedResponse


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
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        timeout: Optional[float] = None,
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
