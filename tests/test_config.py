import os
import pytest
from offers_sdk.config import OffersAPISettings


def test_offers_api_settings_env(monkeypatch):
    # Set environment variables to test values
    monkeypatch.setenv("OFFERS_API_REFRESH_TOKEN", "test-refresh-token")
    monkeypatch.setenv("OFFERS_API_BASE_URL", "https://test-api.appflifting.com")
    monkeypatch.setenv("OFFERS_API_TIMEOUT", "15")

    settings = OffersAPISettings()
    assert settings.refresh_token == "test-refresh-token"
    assert settings.base_url == "https://test-api.appflifting.com"
    assert settings.timeout == 15
