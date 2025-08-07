"""
Middleware interface for OffersClient.

This module defines the `Middleware` protocol used in Offers SDK.
It allows users to hook into the request/response lifecycle of all HTTP operations
performed by the `OffersClient`.

Any class that implements this interface can be passed to the client as a middleware.

Typical use cases:
- Logging (see: LoggingMiddleware)
- Metrics collection
- Header injection (e.g., trace IDs)
- Cache invalidation (e.g., CacheClearMiddleware)
"""

from typing import Any
from typing import Protocol

from offers_sdk.transport.base import UnifiedResponse


class Middleware(Protocol):
    async def on_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        json: Any,
        data: Any,
    ) -> None:
        """
        Called before the HTTP request is executed.

        This can be used to:
        - Log request details
        - Add or modify headers
        - Record metrics
        - Cancel or abort execution (by raising)

        Args:
            method (str): HTTP method, e.g., 'GET', 'POST'
            url (str): Full URL of the request
            headers (dict): Request headers (modifiable)
            params (dict | None): Query parameters
            json (Any): JSON body payload
            data (Any): Alternative body (e.g., for form-data)
        """

    async def on_response(self, response: UnifiedResponse) -> None:
        """
        Called after the HTTP response is received (but before it's parsed).

        This can be used to:
        - Log response status and timing
        - Extract metrics
        - Modify or inspect the response
        - Perform cache invalidation or alerts

        Args:
            response (UnifiedResponse): Unified response object from transport layer
        """
