"""
Middleware to invalidate cached offers after product registration.
Used in OffersClient middleware chain.

When a product is successfully registered (201 Created),
this middleware deletes the cached offers for that product_id.
"""

import logging
from http import HTTPStatus

from aiocache import caches

from offers_sdk.transport.base import UnifiedResponse

logger = logging.getLogger("offers_sdk.middleware.cache")


class CacheClearMiddleware:
    """
    Middleware that clears offers cache when a product is successfully registered.

    This middleware listens for successful product registration responses (201 Created)
    and clears the corresponding offers cache entry to ensure fresh data is fetched
    on subsequent get_offers calls.
    """

    def __init__(self):
        self._cache = caches.get("default")

    async def on_request(
        self,
        method: str,
        url: str,
        headers: dict,
        params,
        json,
        data,
    ):
        # No action needed on request
        pass

    async def on_response(self, response: UnifiedResponse):
        """
        Clear offers cache when a product is successfully registered.

        Only acts on POST /api/v1/products/register with 201 status.
        Extracts product_id from response and clears the corresponding cache entry.
        """
        if response.status_code == HTTPStatus.CREATED:
            try:
                response_data = await response.json()
                product_id = response_data.get("id")

                if product_id:
                    cache_key = f"offers:{product_id}"
                    try:
                        await self._cache.delete(cache_key)
                        logger.info(f"Cleared cache for product {product_id}")
                    except Exception as e:
                        logger.error(f"Failed to delete cache for {product_id}: {e}")
                else:
                    logger.warning("No product ID found in registration response")
            except Exception as e:
                logger.error(f"Failed to parse registration response: {e}")
