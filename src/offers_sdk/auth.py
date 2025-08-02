"""
This module provides an asynchronous AuthManager class responsible for:
- securely handling OAuth2 token refresh
- retrying transient failures (with exponential backoff)
- managing token expiration and reuse.

Although it uses a generated OpenAPI client under the hood, this logic wraps it in a robust, SDK-friendly way.
"""

import logging

logger = logging.getLogger("offers_sdk.auth")
logger.setLevel(logging.DEBUG)

import time
import httpx
from offers_sdk.config import OffersAPISettings
from offers_sdk.token_store import TokenStore
from typing import Optional
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# settings = OffersAPISettings()


class AuthError(Exception):
    """Custom exception for authentication errors."""

    pass


class AuthManager:
    """
    Manages automatic retrieval and refreshing of access tokens using a refresh token.

    This class is intended to be used as a singleton per user/session and provides
    access to a valid OAuth2 access token, handling token expiration and automatic
    refresh with exponential backoff and retries.

    Attributes:
        settings (OffersAPISettings): Configuration with base_url and refresh_token.
        refresh_token (str): The OAuth2 refresh token.
        base_url (str): The API base URL.
        _access_token (Optional[str]): The currently active access token.
        _token_expiry (float): UNIX timestamp when the current access token expires.
        _retry_attempts (int): Maximum number of retry attempts on auth failure.
    """

    def __init__(
        self,
        settings: OffersAPISettings,
        retry_attempts: int = 3,
        token_store: Optional[TokenStore] = None,
    ):
        """
        Initializes the AuthManager.

        Args:
            settings (OffersAPISettings): Configuration instance with refresh_token and base_url.
            retry_attempts (int, optional): How many times to retry auth requests. Defaults to 3.
        """
        self.settings = settings
        self.refresh_token = settings.refresh_token
        self.base_url = settings.base_url
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0
        self._retry_attempts = retry_attempts
        self.token_store = token_store

    @property
    def access_token(self) -> str:
        """
        Returns the current access token if valid.

        Returns:
            str: The current access token.

        Raises:
            AuthError: If no valid access token is available.
        """
        if not self._access_token or self.is_token_expired():
            raise AuthError(
                "No valid access token. Call 'await get_access_token()' first."
            )
        return self._access_token

    def is_token_expired(self) -> bool:
        """
        Checks if the current access token is expired or about to expire.

        Returns:
            bool: True if the token is missing or expired.
        """
        # Add a buffer of 10 seconds before expiry to avoid using a stale token
        return not self._access_token or (time.time() > self._token_expiry - 10)

    async def get_access_token(self) -> str:
        """
        Returns a valid access token. Refreshes it only if it's expired or missing.
        """
        # First try to load from cache
        if not self._access_token and self.token_store:
            logger.debug("Attempting to load token from cache...")
            token_data = await self.token_store.load()
            if token_data:
                logger.debug(
                    f"Loaded cached token (exp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(token_data['expires_at']))})"
                )
                self._access_token = token_data["access_token"]
                self._token_expiry = token_data["expires_at"]

        # Check if we have a valid token
        if self._access_token and not self.is_token_expired():
            logger.debug("Using valid token from memory")
            return self._access_token

        # Only if token is missing or expired, get a new one
        logger.debug("No valid token. Refreshing...")
        return await self._refresh_access_token_unconditionally()

    async def _refresh_access_token_unconditionally(self) -> str:
        if not self.refresh_token or not self.refresh_token.strip():
            raise AuthError("Refresh token is missing or empty")

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(multiplier=0.5, min=1, max=5),
            retry=retry_if_exception_type(Exception),
        ):
            with attempt:
                async with httpx.AsyncClient(
                    base_url=self.base_url, timeout=30.0
                ) as async_client:
                    response = await async_client.post(
                        "/api/v1/auth",
                        headers={"Bearer": self.refresh_token},
                    )

                    if response.status_code == 201:
                        data = await response.json()
                        self._access_token = data["access_token"]
                        self._token_expiry = time.time() + 5 * 60
                        logger.debug(
                            f"New access token acquired (expires in 5 minutes)"
                        )
                        if self.token_store:
                            try:
                                await self.token_store.save(
                                    self._access_token, self._token_expiry
                                )
                                logger.debug("💾 Token saved to cache.")
                            except Exception as e:
                                logger.warning(f"Failed to save token: {e}")
                        return self._access_token
                    elif response.status_code == 401:
                        logger.error("Refresh token is invalid.")
                        raise AuthError("Bad refresh token")
                    else:
                        logger.error(
                            f"Auth error: {response.status_code} — {response.text}"
                        )
                        raise AuthError(
                            f"Auth error: {response.status_code}: {response.text}"
                        )

                raise AuthError("Failed to get access token after retries")
