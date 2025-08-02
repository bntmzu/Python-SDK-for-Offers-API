from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from pydantic import Field


class OffersAPISettings(BaseSettings):
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
