"""A client library for accessing Python exercise"""

from .client import AuthenticatedClient
from .client import Client

__all__ = (
    "AuthenticatedClient",
    "Client",
)
