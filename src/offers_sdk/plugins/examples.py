"""
Example plugins for the Offers SDK.

This module provides example plugins that demonstrate how to extend
the SDK's functionality with custom request/response processing.
"""

import logging
import time
from typing import Any, Dict, Optional

from . import RequestPlugin, ResponsePlugin
from ..transport.base import UnifiedResponse

logger = logging.getLogger(__name__)


class LoggingPlugin(RequestPlugin, ResponsePlugin):
    """
    Example plugin that logs all requests and responses.
    """

    def __init__(self, log_level: int = logging.INFO):
        self.log_level = log_level
        self._start_time = None

    async def process_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
    ) -> tuple[str, str, Dict[str, str], Optional[Dict[str, Any]], Any, Any]:
        """Log request details."""
        self._start_time = time.monotonic()
        logger.log(
            self.log_level,
            f"Request: {method} {url} | headers={headers} | params={params} | json={json}",
        )
        return method, url, headers, params, json, data

    async def process_response(self, response: UnifiedResponse) -> UnifiedResponse:
        """Log response details."""
        elapsed = (time.monotonic() - self._start_time) if self._start_time else None
        logger.log(
            self.log_level,
            (
                f"Response: {response.status_code} | elapsed={elapsed:.3f}s"
                if elapsed
                else f"Response: {response.status_code}"
            ),
        )
        return response


class RetryPlugin(RequestPlugin):
    """
    Example plugin that adds retry headers to requests.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def process_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
    ) -> tuple[str, str, Dict[str, str], Optional[Dict[str, Any]], Any, Any]:
        """Add retry headers to request."""
        headers["X-Retry-Count"] = "0"
        headers["X-Max-Retries"] = str(self.max_retries)
        return method, url, headers, params, json, data


class RateLimitPlugin(ResponsePlugin):
    """
    Example plugin that handles rate limiting.
    """

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self._last_request_time = 0

    async def process_response(self, response: UnifiedResponse) -> UnifiedResponse:
        """Handle rate limiting based on response headers."""
        if response.status_code == 429:  # Too Many Requests
            retry_after = response.headers.get("Retry-After", "60")
            logger.warning(f"Rate limited. Retry after {retry_after} seconds")

        # Update last request time for rate limiting
        self._last_request_time = time.monotonic()
        return response


class AuthenticationPlugin(RequestPlugin):
    """
    Example plugin that adds custom authentication headers.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def process_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
    ) -> tuple[str, str, Dict[str, str], Optional[Dict[str, Any]], Any, Any]:
        """Add custom authentication headers."""
        headers["X-API-Key"] = self.api_key
        headers["X-Client-Version"] = "1.0.0"
        return method, url, headers, params, json, data


class MetricsPlugin(ResponsePlugin):
    """
    Example plugin that collects metrics from responses.
    """

    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0

    async def process_response(self, response: UnifiedResponse) -> UnifiedResponse:
        """Collect metrics from response."""
        self.request_count += 1

        if response.status_code >= 400:
            self.error_count += 1

        # In a real implementation, you would send metrics to a monitoring system
        logger.info(
            f"Metrics: requests={self.request_count}, errors={self.error_count}"
        )

        return response
