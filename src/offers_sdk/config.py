"""
Configuration management for Offers SDK.

This module provides OffersAPISettings class that handles all SDK configuration
with support for environment variables, .env files, and sensible defaults.

Environment variables are automatically loaded with OFFERS_API_ prefix.
Example: OFFERS_API_REFRESH_TOKEN=your_token
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class OffersAPISettings(BaseSettings):
    """
    Configuration settings for Offers SDK with environment variable support.

    This class automatically loads configuration from:
    - Environment variables (with OFFERS_API_ prefix)
    - .env files
    - Default values for optional settings

    Example:
        # From environment
        export OFFERS_API_REFRESH_TOKEN=your_token
        export OFFERS_API_TIMEOUT=60.0

        # In code
        settings = OffersAPISettings()
    """

    refresh_token: str = Field(..., description="Refresh token for authentication")
    base_url: str = "https://python.exercise.applifting.cz"
    timeout: float = 30.0
    transport: str = "httpx"  # default, can be 'aiohttp' or 'requests'
    offers_cache_ttl: int = 60
    token_cache_path: Path = Field(
        default=Path.home() / ".offers_sdk" / "token_cache.json"
    )

    model_config = SettingsConfigDict(
        env_prefix="OFFERS_API_", env_file=".env", extra="ignore"
    )
