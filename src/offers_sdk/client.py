"""
client.py

Async OffersClient for the Offers API SDK.
Handles auth, transport selection, and all main operations (register product, get offers).
"""

from typing import Any
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
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


class OffersAPIError(Exception):
    """Base SDK exception for Offers API errors."""
    def __init__(self, message: str, details: Any = None):
        super().__init__(message)
        self.details = details


class OffersClient:
    """
    Async client for Offers API.
    Handles auth, transport, and exposes high-level API methods.

    Args:
        settings (OffersAPISettings): SDK configuration (refresh_token, base_url, etc.).
        transport_name (str, optional): Transport backend to use ('httpx', 'aiohttp', 'requests').
            Defaults to value from settings.transport.
        retry_attempts (int, optional): Number of retry attempts for transient failures. Defaults to 3.
    """

    def __init__(
        self,
        settings: OffersAPISettings,
        transport_name: str = None,
        retry_attempts: int = 3,
    ):
        self.settings = settings
        self.auth = AuthManager(settings, retry_attempts=retry_attempts)
        transport = transport_name or settings.transport
        self.transport = get_transport(transport, timeout=settings.timeout)
        self._retry_attempts = retry_attempts

    async def register_product(
        self,
        product: RegisterProductRequest,
    ) -> RegisterProductResponse:
        """
        Registers a new product.
        """
        access_token = await self.auth.get_access_token()

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
            if response.status_code == 201:
                return response.parsed
            elif response.status_code == 401:
                # Access token протух? Обновим и повторим.
                await self.auth.refresh_access_token()
                continue
            elif response.status_code == 409:
                raise OffersAPIError("Product ID already registered.")
            elif response.status_code == 422:
                # Parse validation error
                err: HTTPValidationError = response.parsed
                raise OffersAPIError(
                    f"Validation error: {err.detail}",
                    details=err.detail
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
        Returns offers for a given product ID.
        """
        access_token = await self.auth.get_access_token()

        async for _ in AsyncRetrying(
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(multiplier=0.5, min=1, max=5),
            retry=retry_if_exception_type(Exception),
        ):
            client = AuthenticatedClient(
                base_url=self.settings.base_url,
                token=access_token,
            )
            response = await get_offers_api_v1_products_product_id_offers_get.asyncio_detailed(
                client=client,
                product_id=product_id,
                bearer=access_token,
            )
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
                    f"Validation error: {err.detail}",
                    details=err.detail
                )
            else:
                raise OffersAPIError(
                    f"Failed to get offers: {response.status_code} {response.content}",
                    details=response.content
                )
        raise OffersAPIError("Failed to get offers after retries.")

    async def aclose(self):
        """Gracefully close transport clients if needed (e.g., httpx or aiohttp sessions)."""
        # Close httpx transport if used
        if isinstance(self.transport, HttpxTransport):
            await self.transport.close()
        # Other transports (aiohttp, requests) implement close() themselves or sync close
