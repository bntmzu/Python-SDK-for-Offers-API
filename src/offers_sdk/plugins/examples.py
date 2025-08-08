"""
Example plugins for the Offers SDK.

This module provides example plugins that demonstrate how to extend
the SDK's functionality with business logic.
"""

import logging
import time
from typing import Any

from ..transport.base import UnifiedResponse
from . import RequestPlugin
from . import ResponsePlugin

logger = logging.getLogger(__name__)


class DataValidationPlugin(RequestPlugin):
    """
    Plugin that validates and sanitizes request data before sending.

    This plugin focuses on business logic validation rather than
    HTTP-level concerns that middleware handles.
    """

    def __init__(self, strict_validation: bool = True):
        self.strict_validation = strict_validation

    async def process_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
    ) -> tuple[str, str, dict[str, str], dict[str, Any] | None, Any, Any]:
        """Validate and sanitize request data."""
        if json and isinstance(json, dict):
            # Validate product registration data
            if "name" in json:
                if not json["name"].strip():
                    raise ValueError("Product name cannot be empty")
                json["name"] = json["name"].strip()

            if "description" in json:
                if len(json["description"]) > 1000:
                    json["description"] = json["description"][:1000] + "..."

        return method, url, headers, params, json, data


class ResponseEnrichmentPlugin(ResponsePlugin):
    """
    Plugin that enriches response data with additional business context.

    This plugin adds computed fields and metadata to responses
    based on business rules.
    """

    def __init__(self):
        self._offer_count = 0
        self._total_value = 0.0

    async def process_response(self, response: UnifiedResponse) -> UnifiedResponse:
        """Enrich response with business metrics and metadata."""
        if response.status_code == 200:
            try:
                data = await response.json()
                if isinstance(data, list):  # Offers response
                    # Add business metrics
                    enriched_data = []
                    for offer in data:
                        enriched_offer = offer.copy()

                        # Add computed fields
                        if "price" in offer and "currency" in offer:
                            enriched_offer["price_formatted"] = (
                                f"{offer['price']} {offer['currency']}"
                            )

                        # Add availability status
                        if "stock" in offer:
                            if offer["stock"] > 0:
                                enriched_offer["availability"] = "in_stock"
                            elif offer["stock"] == 0:
                                enriched_offer["availability"] = "out_of_stock"
                            else:
                                enriched_offer["availability"] = "unknown"
                        else:
                            enriched_offer["availability"] = "unknown"

                        enriched_data.append(enriched_offer)

                    # Create new response with enriched data
                    from ..transport.base import UnifiedResponse

                    enriched_response = UnifiedResponse(response._response)
                    enriched_response._enriched_data = enriched_data
                    return enriched_response

            except Exception as e:
                logger.warning(f"Failed to enrich response: {e}")

        return response


class BusinessIntelligencePlugin(ResponsePlugin):
    """
    Plugin that provides business intelligence and analytics from responses.

    This plugin analyzes response content to provide business insights
    rather than handling HTTP-level caching concerns.
    """

    def __init__(self):
        self._business_rules = {
            "offers": {"max_price_threshold": 1000, "min_offers_count": 5},
            "products": {"registration_success_rate": 0.95},
        }

    async def process_response(self, response: UnifiedResponse) -> UnifiedResponse:
        """Analyze response for business intelligence."""
        if response.status_code == 200:
            try:
                data = await response.json()

                # Analyze business patterns
                if isinstance(data, list) and data and "price" in data[0]:
                    # This is an offers response - analyze pricing patterns
                    business_insights = self._analyze_offers(data)

                    # Add business intelligence metadata to response
                    response._business_insights = business_insights

                elif isinstance(data, dict) and "id" in data:
                    # This is a product registration response - analyze success patterns
                    business_insights = self._analyze_product_registration(data)

                    response._business_insights = business_insights

            except Exception as e:
                logger.warning(f"Failed to analyze business intelligence: {e}")

        return response

    def _analyze_offers(self, offers: list[dict]) -> dict[str, Any]:
        """Analyze offers for business insights."""
        if not offers:
            return {"status": "no_offers", "recommendation": "No offers available"}

        prices = [offer.get("price", 0) for offer in offers if "price" in offer]
        sellers = [
            offer.get("seller", "unknown") for offer in offers if "seller" in offer
        ]

        insights: dict[str, Any] = {
            "total_offers": len(offers),
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
            },
            "unique_sellers": len(set(sellers)),
            "average_price": sum(prices) / len(prices) if prices else 0,
            "recommendations": [],
        }

        # Business recommendations
        if (
            insights["average_price"]
            > self._business_rules["offers"]["max_price_threshold"]
        ):
            insights["recommendations"].append(
                "Consider negotiating prices - average is high"
            )

        if len(offers) < self._business_rules["offers"]["min_offers_count"]:
            insights["recommendations"].append(
                "Limited competition - consider expanding supplier base"
            )

        return insights

    def _analyze_product_registration(self, product_data: dict) -> dict[str, Any]:
        """Analyze product registration for business insights."""
        insights: dict[str, Any] = {
            "registration_success": True,
            "product_id": product_data.get("id"),
            "recommendations": [],
        }

        # Business recommendations for product registration
        insights["recommendations"].append(
            "Product successfully registered - ready for offers"
        )

        return insights


class BusinessMetricsPlugin(ResponsePlugin):
    """
    Plugin that collects business-specific metrics from responses.

    This plugin tracks business KPIs rather than technical metrics
    that middleware might handle.
    """

    def __init__(self):
        self.metrics = {
            "total_offers_retrieved": 0,
            "average_offer_price": 0.0,
            "price_range": {"min": float("inf"), "max": 0.0},
            "seller_distribution": {},
            "currency_distribution": {},
        }

    async def process_response(self, response: UnifiedResponse) -> UnifiedResponse:
        """Collect business metrics from response."""
        if response.status_code == 200:
            try:
                data = await response.json()
                if isinstance(data, list):  # Offers response
                    self._update_offer_metrics(data)

            except Exception as e:
                logger.warning(f"Failed to collect business metrics: {e}")

        return response

    def _update_offer_metrics(self, offers: list[dict]) -> None:
        """Update business metrics based on offers data."""
        if not offers:
            return

        self.metrics["total_offers_retrieved"] += len(offers)

        prices = []
        for offer in offers:
            if "price" in offer and isinstance(offer["price"], int | float):
                prices.append(offer["price"])

            if "seller" in offer:
                seller = offer["seller"]
                self.metrics["seller_distribution"][seller] = (
                    self.metrics["seller_distribution"].get(seller, 0) + 1
                )

            if "currency" in offer:
                currency = offer["currency"]
                self.metrics["currency_distribution"][currency] = (
                    self.metrics["currency_distribution"].get(currency, 0) + 1
                )

        if prices:
            self.metrics["average_offer_price"] = sum(prices) / len(prices)
            self.metrics["price_range"]["min"] = min(
                self.metrics["price_range"]["min"], min(prices)
            )
            self.metrics["price_range"]["max"] = max(
                self.metrics["price_range"]["max"], max(prices)
            )


class DataTransformationPlugin(RequestPlugin, ResponsePlugin):
    """
    Plugin that transforms data between different formats and standards.

    This plugin handles data format conversions and standardization
    rather than HTTP-level concerns.
    """

    def __init__(self, input_format: str = "json", output_format: str = "json"):
        self.input_format = input_format
        self.output_format = output_format

    async def process_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
    ) -> tuple[str, str, dict[str, str], dict[str, Any] | None, Any, Any]:
        """Transform request data to standard format."""
        if json and isinstance(json, dict):
            # Standardize field names
            transformed_json = {}
            for key, value in json.items():
                # Convert camelCase to snake_case for consistency
                standardized_key = key.lower().replace(" ", "_")
                transformed_json[standardized_key] = value

            # Add metadata
            transformed_json["_metadata"] = {
                "transformed_at": time.time(),
                "original_format": self.input_format,
                "target_format": self.output_format,
            }

            return method, url, headers, params, transformed_json, data

        return method, url, headers, params, json, data

    async def process_response(self, response: UnifiedResponse) -> UnifiedResponse:
        """Transform response data to standard format."""
        if response.status_code == 200:
            try:
                data = await response.json()
                if isinstance(data, list):
                    # Standardize offer data structure
                    transformed_data = []
                    for item in data:
                        transformed_item = {}
                        for key, value in item.items():
                            # Convert snake_case to camelCase for API consistency
                            camel_key = "".join(
                                word.capitalize() if i > 0 else word
                                for i, word in enumerate(key.split("_"))
                            )
                            transformed_item[camel_key] = value

                        transformed_data.append(transformed_item)

                    # Create new response with transformed data
                    from ..transport.base import UnifiedResponse

                    transformed_response = UnifiedResponse(response._response)
                    transformed_response._transformed_data = transformed_data
                    return transformed_response

            except Exception as e:
                logger.warning(f"Failed to transform response: {e}")

        return response


class CompliancePlugin(ResponsePlugin):
    """
    Plugin that ensures responses comply with business rules and regulations.

    This plugin validates responses against business compliance requirements
    rather than technical HTTP concerns.
    """

    def __init__(self, compliance_rules: dict[str, Any] | None = None):
        self.compliance_rules = compliance_rules or {
            "max_price": 10000.0,
            "required_fields": ["price", "seller", "currency"],
            "forbidden_sellers": ["blacklisted_seller"],
            "price_precision": 2,
        }

    async def process_response(self, response: UnifiedResponse) -> UnifiedResponse:
        """Validate response compliance with business rules."""
        if response.status_code == 200:
            try:
                data = await response.json()
                if isinstance(data, list):  # Offers response
                    compliant_data = []
                    for offer in data:
                        if self._is_compliant(offer):
                            compliant_data.append(offer)
                        else:
                            logger.warning(
                                f"Non-compliant offer filtered: {offer.get('id', 'unknown')}"
                            )

                    # Create new response with compliant data only
                    from ..transport.base import UnifiedResponse

                    compliant_response = UnifiedResponse(response._response)
                    compliant_response._compliant_data = compliant_data
                    return compliant_response

            except Exception as e:
                logger.warning(f"Failed to validate compliance: {e}")

        return response

    def _is_compliant(self, offer: dict[str, Any]) -> bool:
        """Check if an offer complies with business rules."""
        # Check required fields
        for field in self.compliance_rules["required_fields"]:
            if field not in offer or offer[field] is None:
                return False

        # Check price limits
        if "price" in offer:
            price = float(offer["price"])
            if price > self.compliance_rules["max_price"]:
                return False

        # Check forbidden sellers
        if "seller" in offer:
            if offer["seller"] in self.compliance_rules["forbidden_sellers"]:
                return False

        return True
