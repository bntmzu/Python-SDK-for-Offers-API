# token_store.py

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("offers_sdk.token_store")


class TokenStore:
    """Abstract interface for token storage."""

    async def load(self) -> dict | None:
        raise NotImplementedError

    async def save(self, access_token: str, expires_at: float):
        raise NotImplementedError

    async def clear(self):
        """Clears the token cache"""
        raise NotImplementedError


class FileTokenStore(TokenStore):
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    async def load(self) -> dict | None:
        logger.debug(f"Attempting to load token from: {self.path}")
        if not self.path.exists():
            logger.debug("Token cache file does not exist")
            return None
        try:
            data: dict = json.loads(self.path.read_text())
            if "access_token" in data and "expires_at" in data:
                if time.time() < data["expires_at"]:
                    logger.debug("Valid cached token found")
                    return data
                else:
                    logger.debug("Cached token is expired")
            else:
                logger.debug("Cached token data is invalid")
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"Failed to load token cache: {e}")
            return None
        return None

    async def save(self, access_token: str, expires_at: float):
        data = {"access_token": access_token, "expires_at": expires_at}
        try:
            logger.debug(f"Saving token to: {self.path}")
            self.path.write_text(json.dumps(data))
            logger.debug("Token saved successfully")
        except OSError as e:
            logger.warning(f"Failed to save token: {e}")

    async def clear(self):
        """Clears the token cache"""
        try:
            if self.path.exists():
                self.path.unlink()
                logger.debug("Token cache cleared")
        except OSError as e:
            logger.warning(f"Failed to clear token cache: {e}")
