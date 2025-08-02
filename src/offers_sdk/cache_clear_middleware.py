"""
Middleware to invalidate cached offers after product registration.
Used in OffersClient middleware chain.

When a product is successfully registered (201 Created),
this middleware deletes the cached offers for that product_id.
"""

import logging
from http import HTTPStatus
from aiocache import caches
from offers_sdk.generated.types import Response

logger = logging.getLogger("offers_sdk.middleware.cache")

class CacheClearMiddleware:
    """
    Middleware that clears the offers cache after successful product registration.

    This works together with the client's get_offers_cached() logic,
    which stores offer data in cache using the key: 'offers:<product_id>'.
    """

    async def on_request(
        self,
        method: str,
        url: str,
        headers: dict,
        params,
        json,
        data,
    ) -> None:
        # No action needed before request
        pass

    async def on_response(self, response: Response) -> None:
        """
        Called after receiving HTTP response.

        If the response is from register_product and was successful (201),
        it clears the cache for the newly registered product_id.
        """
        if response.status_code == HTTPStatus.CREATED and response.parsed:
            product_id = getattr(response.parsed, "id", None)
            if product_id:
                key = f"offers:{product_id}"
                try:
                    await caches.get("default").delete(key)
                except Exception as e:
                    logger.error(f"Failed to delete cache for {key}: {e}")
                logger.info(f"Cache invalidated for key: {key}")
