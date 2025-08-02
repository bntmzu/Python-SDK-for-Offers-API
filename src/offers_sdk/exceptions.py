"""
Custom exceptions for the Offers SDK.
Provides meaningful error classes for client consumers.
"""

from typing import Any, Optional


class OffersAPIError(Exception):
    """
    Base exception for all SDK-level API failures.

    Args:
        message (str): Short explanation of the error.
        details (Any | None): Optional structured details (e.g., validation errors).
    """

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.details = details
