"""
Logging middleware for Offers SDK.

This module provides LoggingMiddleware, a built-in middleware that logs
all HTTP requests and responses with timing information. Useful for
debugging, monitoring, and understanding SDK behavior.

Features:
- Request logging with method, URL, headers, and payload
- Response logging with status code and timing
- Automatic timing measurement
- Configurable log levels
"""

import logging
import time

from offers_sdk.transport.base import UnifiedResponse

logger = logging.getLogger("offers_sdk.middleware.logging")


class LoggingMiddleware:
    """
    Middleware for logging HTTP requests and responses in OffersClient.
    Uses standard Python logging.
    """

    def __init__(self):
        self._start_time = None

    async def on_request(
        self,
        method: str,
        url: str,
        headers: dict,
        params,
        json,
        data,
    ):
        self._start_time = time.monotonic()
        logger.info(
            f"Request: {method} {url} | headers={headers} | params={params} | json={json} | data={data}"
        )

    async def on_response(self, response: UnifiedResponse):
        elapsed = (time.monotonic() - self._start_time) if self._start_time else None
        logger.info(
            f"Response: {response.status_code}"
            + (f" | elapsed={elapsed:.3f}s" if elapsed is not None else "")
        )
