"""
Transport layer for Offers SDK.

This module provides a unified transport interface that abstracts different HTTP clients.
The SDK supports multiple transport backends for flexibility:

- httpx: Modern async HTTP client (default, recommended)
- aiohttp: Async HTTP client with advanced features
- requests: Sync HTTP client wrapped in async interface

All transports implement the same interface, making them interchangeable.
"""

from .httpx import HttpxTransport


def get_transport(name: str, timeout: float = 10.0):
    """
    Get transport instance by name.

    Available transports:
    - httpx: Async HTTP client (default)
    - aiohttp: Async HTTP client
    - requests: Sync HTTP client (wrapped in async interface)

    Note: This SDK supports both async and sync transports for flexibility.
    """
    name = name.lower()
    if name == "httpx":
        return HttpxTransport(timeout)
    elif name == "aiohttp":
        try:
            from .aiohttp import AiohttpTransport

            return AiohttpTransport(timeout)
        except ImportError as err:
            raise ImportError(
                "aiohttp transport requires aiohttp package. Install with: poetry install --extras aiohttp"
            ) from err
    elif name == "requests":
        try:
            from .requests import RequestsTransport

            return RequestsTransport(timeout)
        except ImportError as err:
            raise ImportError(
                "requests transport requires requests package. Install with: poetry install --extras requests"
            ) from err
    else:
        raise ValueError(
            f"Unknown transport: {name}. Available: httpx, aiohttp, requests"
        )
