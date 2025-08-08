"""
Example usage of business-focused plugins in Offers SDK.

This example demonstrates how to use plugins for business logic
instead of duplicating middleware functionality.
"""

import asyncio
import logging

from offers_sdk import OffersAPISettings
from offers_sdk import OffersClient
from offers_sdk.cache_clear_middleware import CacheClearMiddleware
from offers_sdk.generated.models import RegisterProductRequest
from offers_sdk.logging_middleware import LoggingMiddleware
from offers_sdk.plugins.examples import BusinessIntelligencePlugin
from offers_sdk.plugins.examples import BusinessMetricsPlugin
from offers_sdk.plugins.examples import CompliancePlugin
from offers_sdk.plugins.examples import DataValidationPlugin
from offers_sdk.plugins.examples import ResponseEnrichmentPlugin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_business_plugins():
    """
    Demonstrate how business plugins complement middleware functionality.
    """

    # Configure settings
    settings = OffersAPISettings(
        refresh_token="your-refresh-token",
        base_url="https://api.example.com",
        transport="httpx",
    )

    # Technical concerns handled by middleware
    middlewares = [
        LoggingMiddleware(),  # HTTP request/response logging
        CacheClearMiddleware(),  # Cache invalidation
    ]

    # Business logic handled by plugins
    plugins = [
        DataValidationPlugin(strict_validation=True),  # Data validation
        ResponseEnrichmentPlugin(),  # Add computed fields
        BusinessMetricsPlugin(),  # Collect business KPIs
        CompliancePlugin(
            {
                "max_price": 5000.0,
                "required_fields": ["price", "seller", "currency"],
                "forbidden_sellers": ["blacklisted_seller"],
            }
        ),
        BusinessIntelligencePlugin(),  # Business intelligence
    ]

    # Create client with both middleware and plugins
    client = OffersClient(
        settings=settings,
        middlewares=middlewares,
        plugins=plugins,
        retry_attempts=3,
    )

    try:
        # Register a product (plugins will validate and transform data)
        product = RegisterProductRequest(
            name="  Premium Widget  ",  # Will be sanitized by DataValidationPlugin
            description="A high-quality widget with advanced features"
            * 50,  # Will be truncated
        )

        logger.info("Registering product with business validation...")
        result = await client.register_product(product)
        logger.info(f"Product registered with ID: {result.id}")

        # Get offers (plugins will enrich and filter data)
        logger.info("Retrieving offers with business enrichment...")
        offers = await client.get_offers(result.id)

        # Demonstrate plugin effects
        logger.info(f"Retrieved {len(offers)} offers")

        # Business metrics are collected automatically
        metrics_plugin = next(
            p for p in plugins if isinstance(p, BusinessMetricsPlugin)
        )
        logger.info(f"Business metrics: {metrics_plugin.metrics}")

        # Show enriched offer data (if available)
        if offers:
            first_offer = offers[0]
            logger.info(f"First offer: {first_offer}")

            # Note: In a real implementation, the enriched data would be available
            # through the plugin system. This is a simplified example.

    except Exception as e:
        logger.error(f"Error during demonstration: {e}")

    finally:
        await client.aclose()


async def demonstrate_plugin_vs_middleware_separation():
    """
    Demonstrate the clear separation between middleware and plugin concerns.
    """

    logger.info("\n=== Middleware vs Plugin Separation ===")

    # Middleware focuses on HTTP-level concerns
    logger.info("Middleware handles:")
    logger.info("- HTTP request/response logging")
    logger.info("- Authentication headers")
    logger.info("- Cache invalidation")
    logger.info("- Rate limiting")
    logger.info("- Request timing")

    # Plugins focus on business logic
    logger.info("\nPlugins handle:")
    logger.info("- Data validation and sanitization")
    logger.info("- Business rule enforcement")
    logger.info("- Response enrichment with computed fields")
    logger.info("- Business metrics collection")
    logger.info("- Compliance checking")
    logger.info("- Data format transformation")

    logger.info("\nThis separation ensures:")
    logger.info("- Technical concerns are handled consistently")
    logger.info("- Business logic can be customized per use case")
    logger.info("- Code is more maintainable and testable")
    logger.info("- Responsibilities are clearly separated")


def show_plugin_benefits():
    """
    Show the benefits of using business-focused plugins.
    """

    logger.info("\n=== Plugin Benefits ===")

    benefits = [
        "No duplication with middleware functionality",
        "Focus on business domain concerns",
        "Customizable business rules",
        "Data transformation and enrichment",
        "Business metrics collection",
        "Compliance and validation",
        "Intelligent caching strategies",
    ]

    for i, benefit in enumerate(benefits, 1):
        logger.info(f"{i}. {benefit}")

    logger.info("\nExample plugin use cases:")
    logger.info("- Validate product data before registration")
    logger.info("- Add computed fields to offer responses")
    logger.info("- Filter offers based on business rules")
    logger.info("- Collect business KPIs automatically")
    logger.info("- Transform data between different formats")
    logger.info("- Implement intelligent caching strategies")


async def main():
    """
    Main demonstration function.
    """
    logger.info("=== Offers SDK Business Plugins Demonstration ===")

    # Show the benefits and separation
    show_plugin_benefits()
    await demonstrate_plugin_vs_middleware_separation()

    # Note: The actual API calls are commented out since we don't have real credentials
    # Uncomment the following line to run the full demonstration:
    # await demonstrate_business_plugins()

    logger.info("\n=== Demonstration Complete ===")
    logger.info("This example shows how plugins focus on business logic")
    logger.info("while middleware handles technical concerns.")


if __name__ == "__main__":
    asyncio.run(main())
