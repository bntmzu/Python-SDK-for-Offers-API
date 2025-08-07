"""
Middleware interface for OffersClient.

This module defines the `Middleware` protocol used in Offers SDK.
It allows users to hook into the request/response lifecycle of all HTTP operations
performed by the `OffersClient`.

Any class that implements this interface can be passed to the client as a middleware.

Current implementations:
- Logging (see: LoggingMiddleware) - logs requests/responses with timing
- Cache invalidation (see: CacheClearMiddleware) - clears cache after product registration

Planned implementations:
- Metrics collection - for monitoring and observability
- Rate limiting - for API call throttling
- Retry logic - for automatic retry with backoff
- Header injection - for trace IDs and correlation

The middleware class was extracted separately to enable easy addition of new
cross-cutting concerns without modifying the core client logic.
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
        - Log request details (current: LoggingMiddleware)
        - Add or modify headers (planned: HeaderInjectionMiddleware)
        - Record metrics (planned: MetricsMiddleware)
        - Rate limiting checks (planned: RateLimitMiddleware)
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
        - Log response status and timing (current: LoggingMiddleware)
        - Extract metrics (planned: MetricsMiddleware)
        - Modify or inspect the response
        - Perform cache invalidation (current: CacheClearMiddleware)
        - Handle retry logic (planned: RetryMiddleware)

        Args:
            response (UnifiedResponse): Unified response object from transport layer
        """
