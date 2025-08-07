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

from .auth import AuthError
from .auth import AuthManager
from .client import OffersClient
from .client_sync import OffersClientSync
from .config import OffersAPISettings
from .exceptions import OffersAPIError
from .middleware import Middleware
from .plugins import PluginManager
from .plugins import RequestPlugin
from .plugins import ResponsePlugin
from .token_store import FileTokenStore
from .token_store import TokenStore

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
