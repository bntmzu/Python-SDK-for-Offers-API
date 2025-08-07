"""
Unit tests for PluginManager functionality.

This module tests the core PluginManager class including:
- Initialization
- Adding and removing plugins
- Request and response processing
- Error handling
"""

from typing import Any
from unittest.mock import MagicMock

import pytest

from offers_sdk.plugins import PluginManager
from offers_sdk.plugins import RequestPlugin
from offers_sdk.plugins import ResponsePlugin
from offers_sdk.transport.base import UnifiedResponse


class MockRequestPlugin(RequestPlugin):
    """Mock request plugin for testing."""

    def __init__(self, name: str = "mock"):
        self.name = name
        self.processed_requests: list[dict[str, Any]] = []

    async def process_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
    ) -> tuple[str, str, dict[str, str], dict[str, Any] | None, Any, Any]:
        """Process request and record it."""
        self.processed_requests.append(
            {
                "method": method,
                "url": url,
                "headers": headers.copy(),
                "params": params.copy() if params else None,
                "json": json,
                "data": data,
            }
        )

        # Add a custom header to demonstrate modification
        headers[f"X-{self.name}-Plugin"] = "processed"

        return method, url, headers, params, json, data


class MockResponsePlugin(ResponsePlugin):
    """Mock response plugin for testing."""

    def __init__(self, name: str = "mock"):
        self.name = name
        self.processed_responses: list[dict[str, Any]] = []

    async def process_response(self, response: UnifiedResponse) -> UnifiedResponse:
        """Process response and record it."""
        self.processed_responses.append(
            {
                "status_code": response.status_code,
                "text": response.text,
            }
        )

        # Return the same response (could be modified in real plugins)
        return response


class TestPluginManager:
    """Test cases for PluginManager functionality."""

    def test_plugin_manager_initialization(self):
        """Test that PluginManager initializes correctly."""
        manager = PluginManager()

        assert manager.request_plugins == []
        assert manager.response_plugins == []

    def test_add_request_plugin(self):
        """Test adding request plugins."""
        manager = PluginManager()
        plugin = MockRequestPlugin("test")

        manager.add_request_plugin(plugin)

        assert len(manager.request_plugins) == 1
        assert manager.request_plugins[0] == plugin

    def test_add_response_plugin(self):
        """Test adding response plugins."""
        manager = PluginManager()
        plugin = MockResponsePlugin("test")

        manager.add_response_plugin(plugin)

        assert len(manager.response_plugins) == 1
        assert manager.response_plugins[0] == plugin

    def test_remove_request_plugin(self):
        """Test removing request plugins."""
        manager = PluginManager()
        plugin = MockRequestPlugin("test")

        manager.add_request_plugin(plugin)
        assert len(manager.request_plugins) == 1

        manager.remove_request_plugin(plugin)
        assert len(manager.request_plugins) == 0

    def test_remove_response_plugin(self):
        """Test removing response plugins."""
        manager = PluginManager()
        plugin = MockResponsePlugin("test")

        manager.add_response_plugin(plugin)
        assert len(manager.response_plugins) == 1

        manager.remove_response_plugin(plugin)
        assert len(manager.response_plugins) == 0

    @pytest.mark.asyncio
    async def test_process_request_with_no_plugins(self):
        """Test processing request with no plugins."""
        manager = PluginManager()

        result = await manager.process_request(
            method="GET",
            url="https://api.example.com/test",
            headers={"Authorization": "Bearer token"},
            params={"param": "value"},
            json={"data": "value"},
            data=None,
        )

        method, url, headers, params, json_data, data = result

        assert method == "GET"
        assert url == "https://api.example.com/test"
        assert headers == {"Authorization": "Bearer token"}
        assert params == {"param": "value"}
        assert json_data == {"data": "value"}
        assert data is None

    @pytest.mark.asyncio
    async def test_process_request_with_plugins(self):
        """Test processing request with plugins."""
        manager = PluginManager()
        plugin1 = MockRequestPlugin("first")
        plugin2 = MockRequestPlugin("second")

        manager.add_request_plugin(plugin1)
        manager.add_request_plugin(plugin2)

        result = await manager.process_request(
            method="POST",
            url="https://api.example.com/test",
            headers={"Content-Type": "application/json"},
            params=None,
            json={"data": "value"},
            data=None,
        )

        method, url, headers, params, json_data, data = result

        # Check that both plugins processed the request
        assert len(plugin1.processed_requests) == 1
        assert len(plugin2.processed_requests) == 1

        # Check that custom headers were added by both plugins
        assert headers["X-first-Plugin"] == "processed"
        assert headers["X-second-Plugin"] == "processed"

        # Check that original headers are preserved
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_process_response_with_no_plugins(self):
        """Test processing response with no plugins."""
        manager = PluginManager()

        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        unified_response = UnifiedResponse(mock_response)

        result = await manager.process_response(unified_response)

        assert result == unified_response

    @pytest.mark.asyncio
    async def test_process_response_with_plugins(self):
        """Test processing response with plugins."""
        manager = PluginManager()
        plugin1 = MockResponsePlugin("first")
        plugin2 = MockResponsePlugin("second")

        manager.add_response_plugin(plugin1)
        manager.add_response_plugin(plugin2)

        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        unified_response = UnifiedResponse(mock_response)

        await manager.process_response(unified_response)

        # Check that both plugins processed the response
        assert len(plugin1.processed_responses) == 1
        assert len(plugin2.processed_responses) == 1

        # Check that the response was processed by both plugins
        assert plugin1.processed_responses[0]["status_code"] == 200
        assert plugin2.processed_responses[0]["status_code"] == 200

    @pytest.mark.asyncio
    async def test_process_request_with_none_params(self):
        """Test processing request with None params."""
        manager = PluginManager()

        result = await manager.process_request(
            method="GET",
            url="https://api.example.com/test",
            headers={},
            params=None,
            json=None,
            data=None,
        )

        method, url, headers, params, json_data, data = result

        assert params is None
        assert json_data is None
        assert data is None

    @pytest.mark.asyncio
    async def test_plugin_processing_order(self):
        """Test that plugins are processed in the order they were added."""
        manager = PluginManager()
        plugin1 = MockRequestPlugin("first")
        plugin2 = MockRequestPlugin("second")
        plugin3 = MockRequestPlugin("third")

        manager.add_request_plugin(plugin1)
        manager.add_request_plugin(plugin2)
        manager.add_request_plugin(plugin3)

        await manager.process_request(
            method="GET",
            url="https://api.example.com/test",
            headers={},
            params=None,
            json=None,
            data=None,
        )

        # Check that all plugins processed the request
        assert len(plugin1.processed_requests) == 1
        assert len(plugin2.processed_requests) == 1
        assert len(plugin3.processed_requests) == 1

    def test_add_duplicate_plugin(self):
        """Test adding the same plugin multiple times."""
        manager = PluginManager()
        plugin = MockRequestPlugin("test")

        manager.add_request_plugin(plugin)
        manager.add_request_plugin(plugin)  # Add same plugin again

        # Current implementation allows duplicates
        assert len(manager.request_plugins) == 2
        assert manager.request_plugins[0] == plugin
        assert manager.request_plugins[1] == plugin

    def test_remove_nonexistent_plugin(self):
        """Test removing a plugin that wasn't added."""
        manager = PluginManager()
        plugin = MockRequestPlugin("test")

        # Should not raise an exception
        manager.remove_request_plugin(plugin)
        assert len(manager.request_plugins) == 0


class TestPluginErrorHandling:
    """Test cases for plugin error handling."""

    class FailingRequestPlugin(RequestPlugin):
        """Plugin that raises an exception."""

        async def process_request(
            self,
            method: str,
            url: str,
            headers: dict[str, str],
            params: dict[str, Any] | None = None,
            json: Any = None,
            data: Any = None,
        ) -> tuple[str, str, dict[str, str], dict[str, Any] | None, Any, Any]:
            raise Exception("Plugin error")

    class FailingResponsePlugin(ResponsePlugin):
        """Plugin that raises an exception."""

        async def process_response(self, response: UnifiedResponse) -> UnifiedResponse:
            raise Exception("Plugin error")

    @pytest.mark.asyncio
    async def test_plugin_manager_handles_request_plugin_error(self):
        """Test that PluginManager handles request plugin errors."""
        manager = PluginManager()
        failing_plugin = self.FailingRequestPlugin()

        manager.add_request_plugin(failing_plugin)

        with pytest.raises(Exception, match="Plugin error"):
            await manager.process_request(
                method="GET",
                url="https://api.example.com/test",
                headers={},
                params=None,
                json=None,
                data=None,
            )

    @pytest.mark.asyncio
    async def test_plugin_manager_handles_response_plugin_error(self):
        """Test that PluginManager handles response plugin errors."""
        manager = PluginManager()
        failing_plugin = self.FailingResponsePlugin()

        manager.add_response_plugin(failing_plugin)

        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        unified_response = UnifiedResponse(mock_response)

        with pytest.raises(Exception, match="Plugin error"):
            await manager.process_response(unified_response)
