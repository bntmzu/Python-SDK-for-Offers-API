"""

Async OffersClient for the Offers API SDK.
Handles auth, transport selection, and all main operations (register product, get offers).
"""
import logging
from typing import Any
from offers_sdk.middleware import Middleware
from offers_sdk.auth import AuthManager
from offers_sdk.config import OffersAPISettings
from offers_sdk.transport import get_transport
from offers_sdk.transport.httpx import HttpxTransport
from offers_sdk.generated.models import (
    RegisterProductRequest,
    RegisterProductResponse,
    OfferResponse,
    HTTPValidationError,
)
from offers_sdk.generated.api.default import (
    register_product_api_v1_products_register_post,
    get_offers_api_v1_products_product_id_offers_get,
)
from offers_sdk.generated.client import AuthenticatedClient
from aiocache import Cache
from aiocache.serializers import PickleSerializer
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger("offers_sdk.cache")

class OffersAPIError(Exception):
    """Base SDK exception for Offers API errors."""

    def __init__(self, message: str, details: Any = None):
        super().__init__(message)
        self.details = details


class OffersClient:
    """
    Async client for Offers API.
    Handles authentication, pluggable transports, middleware hooks, and transparent caching for offer data.

    Args:
        settings (OffersAPISettings): SDK configuration (supports env/.env).
        transport_name (str | None): 'httpx' | 'aiohttp' | 'requests'. If None, uses settings.transport.
        retry_attempts (int): Max number of retries for transient network failures (default: 3).
        middlewares (list[Middleware] | None): Optional list of Middleware hooks (on_request/on_response).
        offers_cache_ttl (int | None): TTL for offers cache in seconds (default: from settings or 60).
    """

    def __init__(
        self,
        settings: OffersAPISettings,
        transport_name: str | None = None,
        retry_attempts: int = 3,
        middlewares: list[Middleware] | None = None,
        offers_cache_ttl: int | None = None,
    ):
        self.settings = settings
        self.auth = AuthManager(settings, retry_attempts=retry_attempts)
        transport = transport_name or settings.transport
        self.transport = get_transport(transport, timeout=settings.timeout)
        self._retry_attempts = retry_attempts
        self.middlewares = middlewares or []
        self._offers_cache = Cache(
            Cache.MEMORY,
            serializer=PickleSerializer()
        )
        self.offers_cache_ttl = offers_cache_ttl or settings.offers_cache_ttl

    async def register_product(
        self,
        product: RegisterProductRequest,
    ) -> RegisterProductResponse:
        """
        Registers a new product via the Offers API.
        Args:
            product (RegisterProductRequest): The product to register.
        Returns:
            RegisterProductResponse: The registered product data.
        Raises:
            OffersAPIError: On API error (401, 409, 422, network issues, etc).
        """
        access_token = await self.auth.get_access_token()
        url = f"{self.settings.base_url}/api/v1/products/register"
        headers = {"Authorization": f"Bearer {access_token}"}

        # === MIDDLEWARE: before request ===
        for mw in self.middlewares:
            await mw.on_request(
                method="POST",
                url=url,
                headers=headers,
                params=None,
                json=product.to_dict(),
                data=None,
            )

        # Retry logic for network/transient errors
        async for _ in AsyncRetrying(
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(multiplier=0.5, min=1, max=5),
            retry=retry_if_exception_type(Exception),
        ):
            client = AuthenticatedClient(
                base_url=self.settings.base_url,
                token=access_token,
            )
            response = (
                await register_product_api_v1_products_register_post.asyncio_detailed(
                    client=client,
                    body=product,
                    bearer=access_token,
                )
            )

            # === MIDDLEWARE: after response ===
            for mw in self.middlewares:
                await mw.on_response(response)

            if response.status_code == 201:
                return response.parsed
            elif response.status_code == 401:
                # Access token expired, refresh and retry
                await self.auth.refresh_access_token()
                continue
            elif response.status_code == 409:
                raise OffersAPIError("Product ID already registered.")
            elif response.status_code == 422:
                # Parse validation error
                err: HTTPValidationError = response.parsed
                raise OffersAPIError(
                    f"Validation error: {err.detail}", details=err.detail
                )
            else:
                raise OffersAPIError(
                    f"Failed to register product: {response.status_code} {response.content}"
                )
        raise OffersAPIError("Failed to register product after retries.")

    async def get_offers(
        self,
        product_id: str,
    ) -> list[OfferResponse]:
        """
        Returns available offers for a given product ID.
        Args:
            product_id (str): The UUID of the product.
        Returns:
            list[OfferResponse]: List of available offers.
        Raises:
            OffersAPIError: On API/network error.
        """
        access_token = await self.auth.get_access_token()
        url = f"{self.settings.base_url}/api/v1/products/{product_id}/offers"
        headers = {"Authorization": f"Bearer {access_token}"}

        for mw in self.middlewares:
            await mw.on_request(
                method="GET",
                url=url,
                headers=headers,
                params=None,
                json=None,
                data=None,
            )

        async for _ in AsyncRetrying(
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(multiplier=0.5, min=1, max=5),
            retry=retry_if_exception_type(Exception),
        ):
            client = AuthenticatedClient(
                base_url=self.settings.base_url,
                token=access_token,
            )
            response = (
                await get_offers_api_v1_products_product_id_offers_get.asyncio_detailed(
                    client=client,
                    product_id=product_id,
                    bearer=access_token,
                )
            )

            for mw in self.middlewares:
                await mw.on_response(response)

            if response.status_code == 200:
                return response.parsed
            elif response.status_code == 401:
                await self.auth.refresh_access_token()
                continue
            elif response.status_code == 404:
                raise OffersAPIError("Product ID not registered.")
            elif response.status_code == 422:
                err: HTTPValidationError = response.parsed
                raise OffersAPIError(
                    f"Validation error: {err.detail}", details=err.detail
                )
            else:
                raise OffersAPIError(
                    f"Failed to get offers: {response.status_code} {response.content}",
                    details=response.content,
                )
        raise OffersAPIError("Failed to get offers after retries.")

    async def get_offers_cached(self, product_id: str) -> list[OfferResponse]:
        """
        Returns offers for a product ID, using in-memory cache with TTL.

        Args:
            product_id (str): The product's UUID.
        Returns:
            list[OfferResponse]: Cached or fresh offers.
        """
        key = f"offers:{product_id}"

        try:
            cached = await self._offers_cache.get(key)
            if cached is not None:
                logger.info(f"Cache HIT for {key}")
                return cached
        except Exception as e:
            logger.warning(f"Failed to read cache for {key}: {e}")

        logger.info(f"Cache MISS for {key} – fetching from API")
        result = await self.get_offers(product_id)

        try:
            await self._offers_cache.set(key, result, ttl=self.offers_cache_ttl)
        except Exception as e:
            logger.error(f"Failed to write to cache for {key}: {e}")

        return result

    async def aclose(self):
        """
        Gracefully close transport clients if needed (e.g., httpx or aiohttp sessions).
        Should be called when shutting down your application.
        """
        if isinstance(self.transport, HttpxTransport):
            await self.transport.close()
        # Other transports (aiohttp, requests) implement close() themselves or sync close
