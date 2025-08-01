from pydantic_settings import BaseSettings, SettingsConfigDict


class OffersAPISettings(BaseSettings):
    refresh_token: str
    base_url: str = "https://api.yourdomain.com"
    timeout: int = 10
    transport: str = "httpx"  # default, can be 'aiohttp' or 'requests'
    offers_cache_ttl: int = 60

    model_config = SettingsConfigDict(
        env_prefix="OFFERS_API_", env_file=".env", extra="ignore"
    )
