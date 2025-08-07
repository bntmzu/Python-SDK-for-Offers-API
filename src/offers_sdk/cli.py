"""
Command-line interface for Offers SDK.

This module provides a comprehensive CLI for testing and managing the Offers SDK.
All commands use async operations under the hood and provide detailed logging.

Available commands:
- register: Register a single product
- register-batch: Register multiple products from JSON file
- get-offers: Retrieve offers for a product
- get-offers-cached: Retrieve offers with caching
- clear-cache: Clear the token cache
- debug-token: Diagnose current access token
- test-auth: Test authentication with cache
- test-auth-no-cache: Test authentication without cache
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

import click

from offers_sdk.cache_clear_middleware import CacheClearMiddleware
from offers_sdk.client import OffersClient
from offers_sdk.config import OffersAPISettings
from offers_sdk.generated.models import RegisterProductRequest
from offers_sdk.logging_middleware import LoggingMiddleware
from offers_sdk.token_store import FileTokenStore

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
logger = logging.getLogger("offers_sdk.cli")


@click.group()
def cli():
    """Offers SDK CLI"""
    pass


@cli.command()
@click.option("--product-id", required=True, help="UUID of the product")
@click.option("--name", required=True, help="Product name")
@click.option("--description", required=True, help="Product description")
def register(product_id, name, description):
    """Register a new product in the Offers system."""

    async def _run():
        settings = OffersAPISettings()
        settings.timeout = 30.0

        middlewares = [LoggingMiddleware(), CacheClearMiddleware()]
        client = OffersClient(settings, middlewares=middlewares)

        request = RegisterProductRequest(
            id=product_id, name=name, description=description
        )

        try:
            result = await client.register_product(request)
            logger.info("Product registered successfully: %s", result.id)
        except Exception as exc:
            logger.exception("Failed to register product: %s", exc)
        finally:
            await client.aclose()

    asyncio.run(_run())


@cli.command()
@click.option("--file", required=True, help="Path to JSON file with product list")
def register_batch(file):
    """Register multiple products from a JSON file."""

    async def _run():
        settings = OffersAPISettings()
        settings.timeout = 30.0

        middlewares = [LoggingMiddleware(), CacheClearMiddleware()]
        client = OffersClient(settings, middlewares=middlewares)
        file_path = Path(file)

        try:
            with file_path.open("r", encoding="utf-8") as f:
                products_raw = json.load(f)

            for entry in products_raw:
                product = RegisterProductRequest(**entry)
                try:
                    result = await client.register_product(product)
                    logger.info("Registered: %s", result.id)
                except Exception as exc:
                    logger.error("Failed to register product %s: %s", product.id, exc)
        finally:
            await client.aclose()

    asyncio.run(_run())


@cli.command()
@click.option("--product-id", required=True, help="Product UUID")
def get_offers(product_id):
    """Retrieve offers for a registered product."""

    async def _run():
        settings = OffersAPISettings()
        settings.timeout = 30.0

        middlewares = [LoggingMiddleware()]
        client = OffersClient(settings, middlewares=middlewares)

        try:
            offers = await client.get_offers(product_id)
            logger.info("Retrieved %d offers for product %s", len(offers), product_id)
            for offer in offers:
                logger.info("Offer: %s", offer.id)
        except Exception as exc:
            logger.exception("Failed to get offers: %s", exc)
        finally:
            await client.aclose()

    asyncio.run(_run())


@cli.command()
@click.option("--product-id", required=True, help="Product UUID")
def get_offers_cached(product_id):
    """Retrieve offers for a registered product using cache."""

    async def _run():
        settings = OffersAPISettings()
        settings.timeout = 30.0

        middlewares = [LoggingMiddleware()]
        client = OffersClient(settings, middlewares=middlewares)

        try:
            offers = await client.get_offers_cached(product_id)
            logger.info(
                "Retrieved %d cached offers for product %s", len(offers), product_id
            )
            for offer in offers:
                logger.info("Offer: %s", offer.id)
        except Exception as exc:
            logger.exception("Failed to get cached offers: %s", exc)
        finally:
            await client.aclose()

    asyncio.run(_run())


@cli.command()
def clear_cache():
    """Clear the token cache."""

    async def _run():
        settings = OffersAPISettings()
        token_store = FileTokenStore(settings.token_cache_path)

        try:
            await token_store.clear()
            click.echo("Token cache cleared successfully")
        except Exception as exc:
            click.echo(f"Failed to clear cache: {exc}")

    asyncio.run(_run())


@cli.command()
def debug_token():
    """Diagnose the current access token (from cache file)."""
    import json
    from datetime import datetime

    from offers_sdk.config import OffersAPISettings

    settings = OffersAPISettings()
    path = settings.token_cache_path
    click.echo(f"Checking token at: {path}")

    if not path.exists():
        click.echo("Token file does not exist.")
        sys.exit(1)

    try:
        token_data = json.loads(path.read_text())
        token = token_data.get("access_token")
        exp = token_data.get("expires_at")

        if not token or not exp:
            click.echo("Missing 'access_token' or 'expires_at'")
            sys.exit(1)

        exp_dt = datetime.fromtimestamp(exp)
        now = datetime.now()
        remaining = exp_dt - now

        if remaining.total_seconds() <= 0:
            click.echo(f"Token expired at {exp_dt}")
        else:
            click.echo(f"Token valid until {exp_dt} ({remaining})")
            click.echo(f"Token prefix: {token[:10]}...")
    except Exception as e:
        click.echo(f"Failed to read token: {e}")
        sys.exit(1)


@cli.command()
def test_auth():
    """Test authentication directly."""

    async def _run():
        settings = OffersAPISettings()
        client = OffersClient(settings)

        try:
            token = await client.auth.get_access_token()
            click.echo(f"Successfully got token: {token[:20]}...")
        except Exception as exc:
            click.echo(f"Failed to get token: {exc}")
        finally:
            await client.aclose()

    asyncio.run(_run())


@cli.command()
def test_auth_no_cache():
    """Test authentication without cache."""

    async def _run():
        settings = OffersAPISettings()
        settings.token_cache_path = Path("/dev/null")
        client = OffersClient(settings)

        try:
            token = await client.auth.get_access_token()
            click.echo(f"Successfully got token: {token[:20]}...")
        except Exception as exc:
            click.echo(f"Failed to get token: {exc}")
        finally:
            await client.aclose()

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
