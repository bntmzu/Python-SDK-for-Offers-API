"""
Integration tests for business-focused plugins.

These tests verify that plugins handle business logic correctly
without duplicating middleware functionality.
"""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from offers_sdk.plugins.examples import BusinessIntelligencePlugin
from offers_sdk.plugins.examples import BusinessMetricsPlugin
from offers_sdk.plugins.examples import CompliancePlugin
from offers_sdk.plugins.examples import DataTransformationPlugin
from offers_sdk.plugins.examples import DataValidationPlugin
from offers_sdk.plugins.examples import ResponseEnrichmentPlugin
from offers_sdk.transport.base import UnifiedResponse


class TestDataValidationPlugin:
    """Test data validation plugin functionality."""

    @pytest.fixture
    def plugin(self):
        return DataValidationPlugin(strict_validation=True)

    @pytest.mark.asyncio
    async def test_validates_product_name(self, plugin):
        """Test that plugin validates product name."""
        json_data = {"name": "   ", "description": "Test"}

        with pytest.raises(ValueError, match="Product name cannot be empty"):
            await plugin.process_request(
                "POST", "/api/v1/products/register", {}, None, json_data, None
            )

    @pytest.mark.asyncio
    async def test_sanitizes_product_name(self, plugin):
        """Test that plugin sanitizes product name."""
        json_data = {"name": "  Test Product  ", "description": "Test"}

        method, url, headers, params, json_result, data = await plugin.process_request(
            "POST", "/api/v1/products/register", {}, None, json_data, None
        )

        assert json_result["name"] == "Test Product"

    @pytest.mark.asyncio
    async def test_truncates_long_description(self, plugin):
        """Test that plugin truncates long descriptions."""
        long_description = "A" * 1500
        json_data = {"name": "Test", "description": long_description}

        method, url, headers, params, json_result, data = await plugin.process_request(
            "POST", "/api/v1/products/register", {}, None, json_data, None
        )

        assert len(json_result["description"]) <= 1003  # 1000 + "..."
        assert json_result["description"].endswith("...")


class TestResponseEnrichmentPlugin:
    """Test response enrichment plugin functionality."""

    @pytest.fixture
    def plugin(self):
        return ResponseEnrichmentPlugin()

    @pytest.mark.asyncio
    async def test_enriches_offers_with_formatted_price(self, plugin):
        """Test that plugin adds formatted price to offers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value=[{"price": 100, "currency": "USD", "seller": "Test Seller"}]
        )

        response = UnifiedResponse(mock_response)
        enriched_response = await plugin.process_response(response)

        # Verify enrichment happened
        assert hasattr(enriched_response, "_enriched_data")
        enriched_offer = enriched_response._enriched_data[0]
        assert enriched_offer["price_formatted"] == "100 USD"

    @pytest.mark.asyncio
    async def test_adds_availability_status(self, plugin):
        """Test that plugin adds availability status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value=[
                {"stock": 5, "price": 100},
                {"stock": 0, "price": 200},
                {"price": 300},  # No stock field
            ]
        )

        response = UnifiedResponse(mock_response)
        enriched_response = await plugin.process_response(response)

        enriched_offers = enriched_response._enriched_data
        assert enriched_offers[0]["availability"] == "in_stock"
        assert enriched_offers[1]["availability"] == "out_of_stock"
        assert enriched_offers[2]["availability"] == "unknown"


class TestBusinessIntelligencePlugin:
    """Test business intelligence plugin functionality."""

    @pytest.fixture
    def plugin(self):
        return BusinessIntelligencePlugin()

    @pytest.mark.asyncio
    async def test_analyzes_offers_for_business_insights(self, plugin):
        """Test that plugin analyzes offers for business insights."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value=[
                {"price": 100, "seller": "Seller1"},
                {"price": 200, "seller": "Seller2"},
                {"price": 150, "seller": "Seller1"},
            ]
        )

        response = UnifiedResponse(mock_response)
        enriched_response = await plugin.process_response(response)

        assert hasattr(enriched_response, "_business_insights")
        insights = enriched_response._business_insights
        assert insights["total_offers"] == 3
        assert insights["unique_sellers"] == 2
        assert insights["average_price"] == 150.0
        assert "recommendations" in insights

    @pytest.mark.asyncio
    async def test_analyzes_product_registration(self, plugin):
        """Test that plugin analyzes product registration for business insights."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value={"id": "test-product-id", "name": "Test Product"}
        )

        response = UnifiedResponse(mock_response)
        enriched_response = await plugin.process_response(response)

        assert hasattr(enriched_response, "_business_insights")
        insights = enriched_response._business_insights
        assert insights["registration_success"] is True
        assert insights["product_id"] == "test-product-id"
        assert "recommendations" in insights


class TestBusinessMetricsPlugin:
    """Test business metrics plugin functionality."""

    @pytest.fixture
    def plugin(self):
        return BusinessMetricsPlugin()

    @pytest.mark.asyncio
    async def test_collects_offer_metrics(self, plugin):
        """Test that plugin collects business metrics from offers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value=[
                {"price": 100, "seller": "Seller1", "currency": "USD"},
                {"price": 200, "seller": "Seller2", "currency": "EUR"},
                {"price": 150, "seller": "Seller1", "currency": "USD"},
            ]
        )

        response = UnifiedResponse(mock_response)
        await plugin.process_response(response)

        metrics = plugin.metrics
        assert metrics["total_offers_retrieved"] == 3
        assert metrics["average_offer_price"] == 150.0
        assert metrics["price_range"]["min"] == 100
        assert metrics["price_range"]["max"] == 200
        assert metrics["seller_distribution"]["Seller1"] == 2
        assert metrics["seller_distribution"]["Seller2"] == 1
        assert metrics["currency_distribution"]["USD"] == 2
        assert metrics["currency_distribution"]["EUR"] == 1


class TestDataTransformationPlugin:
    """Test data transformation plugin functionality."""

    @pytest.fixture
    def plugin(self):
        return DataTransformationPlugin()

    @pytest.mark.asyncio
    async def test_transforms_request_data(self, plugin):
        """Test that plugin transforms request data."""
        json_data = {"productName": "Test", "productDescription": "Description"}

        method, url, headers, params, json_result, data = await plugin.process_request(
            "POST", "/api/v1/products/register", {}, None, json_data, None
        )

        assert "productname" in json_result
        assert "productdescription" in json_result
        assert "_metadata" in json_result

    @pytest.mark.asyncio
    async def test_transforms_response_data(self, plugin):
        """Test that plugin transforms response data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value=[{"offer_price": 100, "seller_name": "Test Seller"}]
        )

        response = UnifiedResponse(mock_response)
        transformed_response = await plugin.process_response(response)

        assert hasattr(transformed_response, "_transformed_data")
        transformed_item = transformed_response._transformed_data[0]
        assert "offerPrice" in transformed_item
        assert "sellerName" in transformed_item


class TestCompliancePlugin:
    """Test compliance plugin functionality."""

    @pytest.fixture
    def plugin(self):
        return CompliancePlugin(
            {
                "max_price": 1000.0,
                "required_fields": ["price", "seller"],
                "forbidden_sellers": ["blacklisted_seller"],
            }
        )

    @pytest.mark.asyncio
    async def test_filters_non_compliant_offers(self, plugin):
        """Test that plugin filters non-compliant offers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value=[
                {"price": 500, "seller": "good_seller"},  # Compliant
                {"price": 1500, "seller": "good_seller"},  # Too expensive
                {"price": 500, "seller": "blacklisted_seller"},  # Forbidden seller
                {"seller": "good_seller"},  # Missing price
            ]
        )

        response = UnifiedResponse(mock_response)
        compliant_response = await plugin.process_response(response)

        assert hasattr(compliant_response, "_compliant_data")
        compliant_offers = compliant_response._compliant_data
        assert len(compliant_offers) == 1
        assert compliant_offers[0]["seller"] == "good_seller"
        assert compliant_offers[0]["price"] == 500

    @pytest.mark.asyncio
    async def test_handles_empty_response(self, plugin):
        """Test that plugin handles empty responses gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value=[])

        response = UnifiedResponse(mock_response)
        compliant_response = await plugin.process_response(response)

        assert hasattr(compliant_response, "_compliant_data")
        assert compliant_response._compliant_data == []


class TestPluginIntegration:
    """Test plugin integration with the client."""

    @pytest.mark.asyncio
    async def test_plugins_dont_duplicate_middleware(self):
        """Test that plugins focus on business logic, not HTTP concerns."""
        # This test ensures plugins don't duplicate middleware functionality
        validation_plugin = DataValidationPlugin()
        enrichment_plugin = ResponseEnrichmentPlugin()

        # Plugins should focus on data content, not HTTP headers/timing
        assert hasattr(validation_plugin, "process_request")
        assert hasattr(enrichment_plugin, "process_response")

        # Verify plugins don't handle HTTP-level concerns
        # (those should be handled by middleware)
        assert not hasattr(validation_plugin, "on_request")  # Middleware method
        assert not hasattr(enrichment_plugin, "on_response")  # Middleware method

    @pytest.mark.asyncio
    async def test_plugin_business_focus(self):
        """Test that plugins focus on business domain concerns."""
        metrics_plugin = BusinessMetricsPlugin()
        compliance_plugin = CompliancePlugin()

        # These plugins should have business-specific attributes
        assert hasattr(metrics_plugin, "metrics")
        assert hasattr(compliance_plugin, "compliance_rules")

        # Business metrics should track domain concepts
        assert "total_offers_retrieved" in metrics_plugin.metrics
        assert "average_offer_price" in metrics_plugin.metrics
        assert "seller_distribution" in metrics_plugin.metrics
