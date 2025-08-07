import aiohttp
from typing import Any, Dict, Optional

from .base import BaseTransport, UnifiedResponse


class AiohttpTransport(BaseTransport):
    """
    Async transport implementation using aiohttp.ClientSession.
    """

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

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
