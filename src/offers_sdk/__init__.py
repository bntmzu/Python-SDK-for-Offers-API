"""
Offers SDK - Async-first SDK for Offers API.

This SDK provides:
- Async client for Offers API
- Synchronous wrapper for sync operations
- Plugin architecture for extensibility
- Multiple HTTP transport support
- Token management with caching
- Middleware support
"""

from .client import OffersClient
from .client_sync import OffersClientSync
from .config import OffersAPISettings
from .auth import AuthManager, AuthError
from .exceptions import OffersAPIError
from .middleware import Middleware
from .plugins import PluginManager, RequestPlugin, ResponsePlugin
from .token_store import TokenStore, FileTokenStore

__version__ = "1.0.0"

__all__ = [
    "OffersClient",
    "OffersClientSync",
    "OffersAPISettings",
    "AuthManager",
    "AuthError",
    "OffersAPIError",
    "Middleware",
    "PluginManager",
    "RequestPlugin",
    "ResponsePlugin",
    "TokenStore",
    "FileTokenStore",
]
