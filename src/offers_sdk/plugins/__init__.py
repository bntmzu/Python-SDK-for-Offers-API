"""
Plugin architecture for extensible request/response processing.

This module provides a plugin system that allows developers to extend
the SDK's functionality with custom request/response processing.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..transport.base import UnifiedResponse


class RequestPlugin(ABC):
    """
    Base class for request processing plugins.

    Plugins can modify requests before they are sent to the API.
    """

    @abstractmethod
    async def process_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
    ) -> tuple[str, str, Dict[str, str], Optional[Dict[str, Any]], Any, Any]:
        """
        Process a request before it is sent.

        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            params: Query parameters
            json: JSON payload
            data: Form data

        Returns:
            Tuple of (method, url, headers, params, json, data) - modified request
        """


class ResponsePlugin(ABC):
    """
    Base class for response processing plugins.

    Plugins can modify responses after they are received from the API.
    """

    @abstractmethod
    async def process_response(self, response: UnifiedResponse) -> UnifiedResponse:
        """
        Process a response after it is received.

        Args:
            response: Original response

        Returns:
            Modified response
        """


class PluginManager:
    """
    Manages request and response plugins.

    This class coordinates the execution of plugins in the correct order.
    """

    def __init__(self):
        self.request_plugins: list[RequestPlugin] = []
        self.response_plugins: list[ResponsePlugin] = []

    def add_request_plugin(self, plugin: RequestPlugin):
        """Add a request processing plugin."""
        self.request_plugins.append(plugin)

    def add_response_plugin(self, plugin: ResponsePlugin):
        """Add a response processing plugin."""
        self.response_plugins.append(plugin)

    def remove_request_plugin(self, plugin: RequestPlugin):
        """Remove a request processing plugin."""
        if plugin in self.request_plugins:
            self.request_plugins.remove(plugin)

    def remove_response_plugin(self, plugin: ResponsePlugin):
        """Remove a response processing plugin."""
        if plugin in self.response_plugins:
            self.response_plugins.remove(plugin)

    async def process_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
    ) -> tuple[str, str, Dict[str, str], Optional[Dict[str, Any]], Any, Any]:
        """
        Process request through all request plugins.
        """
        current_method = method
        current_url = url
        current_headers = headers.copy()
        current_params = params.copy() if params is not None else None
        current_json = json
        current_data = data

        for plugin in self.request_plugins:
            (
                current_method,
                current_url,
                current_headers,
                current_params,
                current_json,
                current_data,
            ) = await plugin.process_request(
                current_method,
                current_url,
                current_headers,
                current_params,
                current_json,
                current_data,
            )

        return (
            current_method,
            current_url,
            current_headers,
            current_params,
            current_json,
            current_data,
        )

    async def process_response(self, response: UnifiedResponse) -> UnifiedResponse:
        """
        Process response through all response plugins.
        """
        current_response = response

        for plugin in self.response_plugins:
            current_response = await plugin.process_response(current_response)

        return current_response
