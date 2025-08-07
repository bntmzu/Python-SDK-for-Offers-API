"""
Synchronous wrapper for OffersClient.

This module provides a synchronous interface on top of the async OffersClient
to support users who need sync operations.
"""

import asyncio

from .client import OffersClient
from .config import OffersAPISettings
from .generated.models import OfferResponse
from .generated.models import RegisterProductRequest
from .generated.models import RegisterProductResponse


class OffersClientSync:
    """
    Synchronous wrapper for OffersClient.

    This class provides a synchronous interface on top of the async OffersClient,
    allowing users to use the SDK in synchronous contexts.

    Example:
        client = OffersClientSync(settings)
        offers = client.get_offers("product-id")
        result = client.register_product(product)
    """

    def __init__(
        self,
        settings: OffersAPISettings,
        transport_name: str | None = None,
        retry_attempts: int = 3,
        offers_cache_ttl: int | None = None,
    ):
        """
        Initialize the synchronous client.

        Args:
            settings: API configuration settings
            transport_name: HTTP transport to use (httpx, aiohttp, requests)
            retry_attempts: Number of retry attempts for failed requests
            offers_cache_ttl: Cache TTL for offers in seconds
        """
        self._async_client = OffersClient(
            settings=settings,
            transport_name=transport_name,
            retry_attempts=retry_attempts,
            offers_cache_ttl=offers_cache_ttl,
        )

    def register_product(
        self, product: RegisterProductRequest
    ) -> RegisterProductResponse:
        """
        Synchronous product registration.

        Args:
            product: Product to register

        Returns:
            RegisterProductResponse: Registration result

        Raises:
            OffersAPIError: On API error
        """
        return asyncio.run(self._async_client.register_product(product))

    def get_offers(self, product_id: str) -> list[OfferResponse]:
        """
        Synchronous offers retrieval.

        Args:
            product_id: Product ID to get offers for

        Returns:
            List[OfferResponse]: List of available offers

        Raises:
            OffersAPIError: On API error
        """
        return asyncio.run(self._async_client.get_offers(product_id))

    def get_offers_cached(self, product_id: str) -> list[OfferResponse]:
        """
        Synchronous cached offers retrieval.

        Args:
            product_id: Product ID to get offers for

        Returns:
            List[OfferResponse]: Cached or fresh offers

        Raises:
            OffersAPIError: On API error
        """
        return asyncio.run(self._async_client.get_offers_cached(product_id))

    def close(self):
        """
        Synchronous cleanup of client resources.
        """
        asyncio.run(self._async_client.aclose())

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
