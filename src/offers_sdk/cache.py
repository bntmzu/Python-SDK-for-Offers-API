"""
Cache utilities for async functions (used outside OffersClient).

This module defines `async_ttl_cache`, a lightweight decorator that provides
in-memory caching with TTL for asynchronous functions.

❗ Note: This is not used inside `OffersClient`, which manages its own cache via `self._offers_cache`.

You can use this decorator in:
- CLI tools
- testing scripts
- fast prototypes
"""

from aiocache import Cache


def async_ttl_cache(ttl: int):
    """
    Async cache decorator with fixed TTL for external use.

    Example:
        @async_ttl_cache(ttl=60)
        async def get_data(key: str): ...

    Args:
        ttl (int): Time to live for the cache in seconds.
    """

    def decorator(fn):
        async def wrapper(*args, **kwargs):
            cache = Cache(Cache.MEMORY)
            key = f"{fn.__name__}:{args[1]}"  # args[1] is typically product_id (self at args[0])
            result = await cache.get(key)
            if result is not None:
                return result
            result = await fn(*args, **kwargs)
            await cache.set(key, result, ttl=ttl)
            return result

        return wrapper

    return decorator
