"""
auth_manager.py

Provides an asynchronous AuthManager for handling OAuth token refresh with retry logic,
suitable for use with the Offers API SDK. Automatically obtains and refreshes access tokens
using a provided refresh token and manages their expiration.

Requirements:
    - tenacity for retry logic
    - offers_sdk (generated OpenAPI client)
    - OffersAPISettings (configuration class)
"""

import time
from offers_sdk.config import OffersAPISettings
from typing import Optional
from offers_sdk.generated.models import AuthResponse
from offers_sdk.generated.api.default import auth_api_v1_auth_post
from offers_sdk.generated.client import AuthenticatedClient
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
        Ensures a valid access token is available and returns it.

        If the current token is missing or expired, a new token will be fetched.

        Returns:
            str: The valid access token.

        Raises:
            AuthError: If unable to refresh the token.
        """
        if not self._access_token or self.is_token_expired():
            await self.refresh_access_token()
        return self._access_token

    async def refresh_access_token(self):
        """
        Fetches a new access token using the refresh token.

        Uses exponential backoff and retries for transient errors.

        Raises:
            AuthError: If the refresh token is invalid or all retries fail.
        """
        # Use tenacity for retrying transient failures
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(multiplier=0.5, min=1, max=5),
            retry=retry_if_exception_type(Exception),
        ):
            client = AuthenticatedClient(
                base_url=self.base_url,
            )
            # The following call must be compatible with the OpenAPI async client
            response = await auth_api_v1_auth_post.asyncio_detailed(
                client=client, bearer=self.refresh_token
            )
            if response.status_code == 201:
                data: AuthResponse = response.parsed
                self._access_token = data.access_token
                self._token_expiry = (
                    time.time() + 5 * 60
                )  # Token is valid for 5 minutes
                return
            elif response.status_code == 401:
                raise AuthError("Bad refresh token")
            else:
                raise AuthError(f"Auth error: {response.status_code}")
        # If all attempts fail, raise an AuthError
        raise AuthError("Failed to get access token after retries")
