"""
Async-first Offers API SDK Client.

This module provides the main OffersClient class that handles all interactions with the Offers API.
Features include:

- Async-first design with async/await for all API operations
- Automatic token refresh with persistent token storage
- Multiple HTTP transport backends (httpx, aiohttp, requests)
- Pluggable middleware system for request/response processing
- Plugin architecture for extensible request/response handling
- Configurable caching with TTL for offer data
- Retry logic with exponential backoff for transient failures
- Comprehensive error handling with meaningful exceptions
- Full type hints throughout the codebase

Example usage:
    from offers_sdk import OffersClient, OffersAPISettings

    settings = OffersAPISettings(refresh_token="your-token")
    client = OffersClient(settings)

    # Register a product
    product = RegisterProductRequest(name="Test", description="Description")
    result = await client.register_product(product)

    # Get offers with caching
    offers = await client.get_offers_cached("product-id")

    await client.aclose()
"""

import logging

from tenacity import AsyncRetrying
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from offers_sdk.auth import AuthManager
from offers_sdk.config import OffersAPISettings
from offers_sdk.exceptions import OffersAPIError
from offers_sdk.generated.models import OfferResponse
from offers_sdk.generated.models import RegisterProductRequest
from offers_sdk.generated.models import RegisterProductResponse
from offers_sdk.middleware import Middleware
from offers_sdk.token_store import FileTokenStore
from offers_sdk.transport import get_transport
from offers_sdk.transport.httpx import HttpxTransport

logger = logging.getLogger("offers_sdk.cache")


class OffersClient:
    """
    Async-first client for the Offers API with comprehensive features.

    This client provides a complete interface to the Offers API with advanced features
    including automatic authentication, multiple transport backends, middleware support,
    plugin architecture, caching, and retry logic.

    Key Features:
    - Async-first design with async/await for all operations
    - Automatic token refresh using persistent token storage
    - Multiple HTTP transport backends (httpx, aiohttp, requests)
    - Pluggable middleware system for cross-cutting concerns
    - Plugin architecture for extensible request/response processing
    - Configurable caching with TTL for offer data
    - Retry logic with exponential backoff for transient failures
    - Comprehensive error handling with meaningful exceptions
    - Full type hints throughout

    Args:
        settings (OffersAPISettings): SDK configuration with support for environment variables
        transport_name (str | None): Transport backend ('httpx', 'aiohttp', 'requests').
                                   Defaults to settings.transport
        retry_attempts (int): Maximum retry attempts for transient network failures (default: 3)
        middlewares (list[Middleware] | None): Optional list of middleware hooks for
                                             request/response processing
        offers_cache_ttl (int | None): TTL for offers cache in seconds
                                     (default: from settings or 60)
        plugins (list | None): Optional list of plugins for request/response processing

    Example:
        from offers_sdk import OffersClient, OffersAPISettings
        from offers_sdk.middleware import LoggingMiddleware

        settings = OffersAPISettings(refresh_token="your-token")
        client = OffersClient(
            settings=settings,
            transport_name="httpx",
            middlewares=[LoggingMiddleware()],
            retry_attempts=3
        )

        # Register a product
        product = RegisterProductRequest(name="Test", description="Description")
        result = await client.register_product(product)

        # Get offers with caching
        offers = await client.get_offers_cached("product-id")

        await client.aclose()
    """

    def __init__(
        self,
        settings: OffersAPISettings,
        transport_name: str | None = None,
        retry_attempts: int = 3,
        middlewares: list[Middleware] | None = None,
        offers_cache_ttl: int | None = None,
        plugins: list | None = None,
    ):
        self.settings = settings

        token_store = FileTokenStore(self.settings.token_cache_path)

        self.auth = AuthManager(
            settings=self.settings,
            retry_attempts=retry_attempts,
            token_store=token_store,
        )
        transport = transport_name or settings.transport
        self.transport = get_transport(transport, timeout=settings.timeout)
        self._retry_attempts = retry_attempts
        self.middlewares = middlewares or []

        # Initialize plugin manager
        from .plugins import PluginManager

        self.plugin_manager = PluginManager()
        if plugins:
            for plugin in plugins:
                if hasattr(plugin, "process_request"):
                    self.plugin_manager.add_request_plugin(plugin)
                if hasattr(plugin, "process_response"):
                    self.plugin_manager.add_response_plugin(plugin)

        # Use global aiocache for middleware compatibility
        from aiocache import caches

        self._offers_cache = caches.get("default")
        self.offers_cache_ttl = offers_cache_ttl or settings.offers_cache_ttl

    async def register_product(
        self,
        product: RegisterProductRequest,
    ) -> RegisterProductResponse:
        """
        Register a new product with the Offers API.

        This method handles the complete product registration process including:
        - Automatic authentication with token refresh
        - Middleware processing for request/response hooks
        - Plugin processing for extensible request/response handling
        - Retry logic with exponential backoff for transient failures
        - Comprehensive error handling with meaningful exceptions

        Args:
            product (RegisterProductRequest): Product data to register containing name and description

        Returns:
            RegisterProductResponse: Registration result with product ID and status

        Raises:
            OffersAPIError: On API errors (401, 409, 422, network issues, etc.)
                           with detailed error messages and context

        Example:
            from offers_sdk.generated.models import RegisterProductRequest

            product = RegisterProductRequest(
                name="My Product",
                description="Product description"
            )
            result = await client.register_product(product)
            print(f"Registered product ID: {result.id}")
        """
        retried = False
        access_token = await self.auth.get_access_token()
        url = f"{self.settings.base_url}/api/v1/products/register"
        headers = {"Bearer": access_token}
        json_data = product.to_dict()

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

        # === PLUGINS: process request ===
        (
            method,
            url,
            headers,
            params,
            json_data,
            data,
        ) = await self.plugin_manager.process_request(
            "POST",
            url,
            headers,
            None,
            json_data,
            None,
        )

        # Retry logic for network/transient errors
        async for _ in AsyncRetrying(
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(multiplier=0.5, min=1, max=5),
            retry=retry_if_exception_type(Exception),
        ):
            response = await self.transport.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
            )

            # === PLUGINS: process response ===
            response = await self.plugin_manager.process_response(response)

            # === MIDDLEWARE: after response ===
            for mw in self.middlewares:
                await mw.on_response(response)

            if response.status_code == 201:
                return RegisterProductResponse(**await response.json())

            if response.status_code == 401 and not retried:
                retried = True
                access_token = await self.auth.get_access_token()
                headers["Bearer"] = access_token
                continue
            if response.status_code == 401:
                raise OffersAPIError("Unauthorized: invalid or expired token.")

            if response.status_code == 409:
                raise OffersAPIError("Product ID already registered.")

            if response.status_code == 422:
                error_data = await response.json()
                raise OffersAPIError(
                    f"Validation error: {error_data.get('detail', 'Unspecified error')}",
                    details=error_data,
                )

            raise OffersAPIError(
                f"Failed to register product: {response.status_code} {response.text}"
            )

        raise OffersAPIError("Failed to register product after retries.")

    async def get_offers(
        self,
        product_id: str,
    ) -> list[OfferResponse]:
        """
        Retrieve available offers for a given product ID.

        This method fetches offers directly from the API with full feature support:
        - Automatic authentication with token refresh on 401 errors
        - Middleware processing for request/response hooks
        - Plugin processing for extensible request/response handling
        - Retry logic with exponential backoff for transient failures
        - Comprehensive error handling with detailed status codes

        Args:
            product_id (str): The UUID of the product to get offers for

        Returns:
            list[OfferResponse]: List of available offers with pricing and availability data

        Raises:
            OffersAPIError: On API errors with specific error messages:
                - 401: Unauthorized (invalid or expired token)
                - 404: Product not found or not registered
                - 422: Validation error with details
                - Network errors: Transient failures with retry logic

        Example:
            offers = await client.get_offers("eb92ac34-7023-4b04-891c-562d95d7e804")
            for offer in offers:
                print(f"Offer: {offer.price} from {offer.seller}")
        """
        retried = False

        access_token = await self.auth.get_access_token()
        url = f"{self.settings.base_url}/api/v1/products/{product_id}/offers"
        headers = {"Bearer": access_token}

        for mw in self.middlewares:
            await mw.on_request(
                method="GET",
                url=url,
                headers=headers,
                params=None,
                json=None,
                data=None,
            )

        # === PLUGINS: process request ===
        (
            method,
            url,
            headers,
            params,
            json_data,
            data,
        ) = await self.plugin_manager.process_request(
            "GET",
            url,
            headers,
            None,
            None,
            None,
        )

        async for _ in AsyncRetrying(
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(multiplier=0.5, min=1, max=5),
            retry=retry_if_exception_type(Exception),
        ):
            response = await self.transport.request(
                method=method,
                url=url,
                headers=headers,
            )

            # === PLUGINS: process response ===
            response = await self.plugin_manager.process_response(response)

            for mw in self.middlewares:
                await mw.on_response(response)

            if response.status_code == 200:
                return [
                    OfferResponse.from_dict(offer) for offer in await response.json()
                ]
            if response.status_code == 401 and not retried:
                retried = True
                # Just get a new token (without manual clearing)
                access_token = await self.auth.get_access_token()
                headers["Bearer"] = access_token
                continue

            if response.status_code == 401:
                raise OffersAPIError("Unauthorized: invalid or expired token.")
            if response.status_code == 404:
                raise OffersAPIError("Product ID not registered.")
            if response.status_code == 422:
                raise OffersAPIError("Validation error", details=await response.json())
            else:
                raise OffersAPIError(
                    f"Unexpected status: {response.status_code}", details=response.text
                )

        raise OffersAPIError("Failed to get offers after retries.")

    async def get_offers_cached(self, product_id: str) -> list[OfferResponse]:
        """
        Retrieve offers for a product ID with intelligent caching.

        This method provides optimized offer retrieval with configurable caching:
        - In-memory cache with configurable TTL (default: 60 seconds)
        - Automatic cache invalidation on TTL expiration
        - Graceful fallback to live API calls on cache miss or failure
        - JSON serialization for reliable cache storage
        - Comprehensive logging for cache hits/misses

        The caching layer is transparent - if cache is empty or fails,
        the method automatically falls back to the live API call.

        Args:
            product_id (str): The UUID of the product to get offers for

        Returns:
            list[OfferResponse]: Cached offers (if available) or fresh offers from API

        Raises:
            OffersAPIError: If both cache and API retrieval fail after retries

        Example:
            # First call: fetches from API and caches
            offers = await client.get_offers_cached("product-id")

            # Subsequent calls within TTL: returns cached data
            cached_offers = await client.get_offers_cached("product-id")

        Note:
            Cache TTL is configurable via settings.offers_cache_ttl or
            the offers_cache_ttl parameter in client initialization.
        """
        key = f"offers:{product_id}"

        try:
            cached = await self._offers_cache.get(key)
            if cached is not None:
                logger.info(f"Cache HIT for {key}")
                # aiocache serializes objects to strings, so we need to handle this
                if isinstance(cached, str):
                    # Try to parse the serialized string back to objects
                    import json

                    try:
                        # Parse the JSON string representation
                        parsed_data = json.loads(cached)
                        if isinstance(parsed_data, list):
                            return [
                                OfferResponse.from_dict(offer) for offer in parsed_data
                            ]
                    except (json.JSONDecodeError, ValueError):
                        logger.warning(f"Failed to parse cached data for {key}")
                        # Fall through to API call
                elif isinstance(cached, list):
                    # If it's already a list of objects, return as is
                    return cached
                else:
                    logger.warning(
                        f"Unexpected cached data type for {key}: {type(cached)}"
                    )
        except Exception as e:
            logger.warning(f"Failed to read cache for {key}: {e}")

        logger.info(f"Cache MISS for {key} – fetching from API")

        # fallback to normal get_offers with retry
        offers = await self.get_offers(product_id)

        try:
            # Store as JSON string to avoid serialization issues
            import json

            offers_json = json.dumps([offer.to_dict() for offer in offers])
            await self._offers_cache.set(key, offers_json, ttl=self.offers_cache_ttl)
        except Exception as e:
            logger.error(f"Failed to write to cache for {key}: {e}")

        return offers

    async def aclose(self):
        """
        Gracefully close client resources and transport connections.

        This method should be called when shutting down your application to ensure
        proper cleanup of resources:
        - Close HTTP transport sessions (httpx, aiohttp)
        - Release connection pools and file descriptors
        - Clean up any pending async operations

        It's recommended to use this method in a context manager pattern or
        explicitly call it before application shutdown.

        Example:
            # Using as context manager
            async with OffersClient(settings) as client:
                offers = await client.get_offers("product-id")

            # Or explicit cleanup
            client = OffersClient(settings)
            try:
                offers = await client.get_offers("product-id")
            finally:
                await client.aclose()
        """
        if isinstance(self.transport, HttpxTransport):
            await self.transport.close()
        # Other transports (aiohttp, requests) implement close() themselves or sync close
