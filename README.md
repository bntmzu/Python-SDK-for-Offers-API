# Offers SDK

Async-first Python SDK for the Offers API with comprehensive features including automatic authentication, multiple HTTP transports, middleware support, plugin architecture, and caching.

## Features

- **Async-first design** with async/await for all API operations
- **Automatic token refresh** using persistent token storage
- **Multiple HTTP transports** (httpx, aiohttp, requests) with configurable backends
- **Plugin architecture** for extensible request/response processing
- **Middleware system** for cross-cutting concerns (logging, caching, etc.)
- **Caching layer** with configurable TTL for offer data
- **Retry logic** with exponential backoff for transient failures
- **Synchronous wrapper** for sync contexts
- **CLI companion tool** for testing and management
- **Docker support** with multi-service setup
- **Comprehensive error handling** with meaningful exceptions
- **Full type hints** throughout the codebase
- **Modern development tools**: ruff, isort, black, mypy
- **Pre-commit hooks** for automatic code quality checks

## Quick Start

### Installation

```bash
# Using Poetry (recommended)
poetry install --all-extras

# Install with development tools
poetry install --with dev --all-extras

# Note: This package is not yet published to PyPI
# For production use, install from source or use Docker
```

### Basic Usage

```python
import asyncio
from offers_sdk import OffersClient, OffersAPISettings

async def main():
    # Configure settings
    settings = OffersAPISettings(
        refresh_token="your_refresh_token_here"
    )
    
    # Create client
    client = OffersClient(settings)
    
    # Register a product
    from offers_sdk.generated.models import RegisterProductRequest
    product = RegisterProductRequest(
        id="product-123",
        name="Sample Product",
        description="A sample product description"
    )
    
    result = await client.register_product(product)
    print(f"Product registered: {result.id}")
    
    # Get offers for the product
    offers = await client.get_offers("product-123")
    print(f"Found {len(offers)} offers")
    
    # Clean up
    await client.aclose()

# Run the example
asyncio.run(main())
```

### Synchronous Usage

```python
from offers_sdk import OffersClientSync, OffersAPISettings

# Create sync client
settings = OffersAPISettings(refresh_token="your_refresh_token_here")
client = OffersClientSync(settings)

# Use synchronously
offers = client.get_offers("product-123")
print(f"Found {len(offers)} offers")

# Context manager for cleanup
with OffersClientSync(settings) as client:
    offers = client.get_offers("product-123")
```

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required
OFFERS_API_REFRESH_TOKEN=your_refresh_token_here

# Optional
OFFERS_API_BASE_URL=https://python.exercise.applifting.cz
OFFERS_API_TIMEOUT=30.0
OFFERS_API_TRANSPORT=httpx  # httpx, aiohttp, or requests
OFFERS_API_OFFERS_CACHE_TTL=60
```

### Programmatic Configuration

```python
from offers_sdk import OffersAPISettings

settings = OffersAPISettings(
    refresh_token="your_token",
    base_url="https://api.example.com",
    timeout=30.0,
    transport="httpx",
    offers_cache_ttl=60
)
```

## Advanced Features

### Middleware

```python
from offers_sdk import OffersClient, OffersAPISettings
from offers_sdk.logging_middleware import LoggingMiddleware
from offers_sdk.cache_clear_middleware import CacheClearMiddleware

settings = OffersAPISettings(refresh_token="your_token")
middlewares = [
    LoggingMiddleware(),
    CacheClearMiddleware()
]

client = OffersClient(settings, middlewares=middlewares)
```

### Plugin System

```python
from offers_sdk import OffersClient, OffersAPISettings
from offers_sdk.plugins import PluginManager, LoggingPlugin, RetryPlugin

# Create plugin manager
plugin_manager = PluginManager()
plugin_manager.add_plugin(LoggingPlugin())
plugin_manager.add_plugin(RetryPlugin(max_retries=3))

# Use with client
client = OffersClient(
    settings=OffersAPISettings(refresh_token="your_token"),
    plugins=plugin_manager
)
```

### Multiple HTTP Transports

```python
# Using httpx (default)
client = OffersClient(settings, transport_name="httpx")

# Using aiohttp
client = OffersClient(settings, transport_name="aiohttp")

# Using requests (sync wrapper)
client = OffersClient(settings, transport_name="requests")
```

### Caching

```python
# Enable caching with custom TTL
client = OffersClient(
    settings,
    offers_cache_ttl=300  # 5 minutes
)

# Get cached offers
offers = await client.get_offers_cached("product-123")
```

## CLI Tool

The SDK includes a command-line interface for testing and management:

```bash
# Register a product
offers-cli register --product-id "product-123" --name "Product Name" --description "Description"

# Get offers
offers-cli get-offers --product-id "product-123"

# Register multiple products from JSON file
offers-cli register-batch --file products.json

# Clear cache
offers-cli clear-cache

# Debug token
offers-cli debug-token

# Test authentication
offers-cli test-auth
```

## Docker Support

### Development Environment

```bash
# Start development environment
docker compose --profile dev up

# Run tests in development environment
docker compose --profile dev-test up

# Interactive development shell
docker compose --profile dev-shell up

# Run tests in production environment
docker compose --profile test up

# Use CLI in container
docker compose --profile cli up

# Production environment
docker compose --profile production up
```

### Production Build

```bash
# Build production image
docker build -t offers-sdk .

# Run production container
docker run -e OFFERS_API_REFRESH_TOKEN=your_token offers-sdk
```

### Dockerfile Differences

**Dockerfile** (Production):
- Minimal dependencies: `poetry install --all-extras`
- Includes CLI support
- Optimized for production use
- All optional extras installed (aiohttp, requests, aiocache, click)

**Dockerfile.dev** (Development):
- Full development environment: `poetry install --with dev --all-extras`
- Includes testing tools: pytest, mypy, black, ruff, isort, pre-commit
- Interactive development support

## API Reference

### OffersClient

Main async client for the Offers API.

```python
class OffersClient:
    def __init__(
        self,
        settings: OffersAPISettings,
        transport_name: Optional[str] = None,
        retry_attempts: int = 3,
        middlewares: List[Middleware] = None,
        offers_cache_ttl: Optional[int] = None,
        plugins: List = None
    )
```

**Methods:**
- `register_product(product: RegisterProductRequest) -> RegisterProductResponse`
- `get_offers(product_id: str) -> List[OfferResponse]`
- `get_offers_cached(product_id: str) -> List[OfferResponse]`
- `aclose() -> None`

### OffersClientSync

Synchronous wrapper for the async client.

```python
class OffersClientSync:
    def __init__(
        self,
        settings: OffersAPISettings,
        transport_name: Optional[str] = None,
        retry_attempts: int = 3,
        offers_cache_ttl: Optional[int] = None
    )
```

**Methods:**
- `register_product(product: RegisterProductRequest) -> RegisterProductResponse`
- `get_offers(product_id: str) -> List[OfferResponse]`
- `get_offers_cached(product_id: str) -> List[OfferResponse]`
- `close() -> None`

## Error Handling

The SDK provides comprehensive error handling:

```python
from offers_sdk import OffersAPIError, AuthError

try:
    offers = await client.get_offers("product-123")
except AuthError as e:
    print(f"Authentication failed: {e}")
except OffersAPIError as e:
    print(f"API error: {e}")
    print(f"Details: {e.details}")
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/your-username/offers-sdk.git
cd offers-sdk

# Install all dependencies (including optional extras)
poetry install --all-extras

# Install development dependencies
poetry install --with dev --all-extras

# Run tests
poetry run pytest

# Run linting (ruff replaces flake8)
poetry run ruff check src/ tests/

# Run import sorting
poetry run isort src/ tests/

# Run code formatting
poetry run black src/ tests/

# Run type checking
poetry run mypy src/

# Run pre-commit hooks (automatically runs on git commit)
poetry run pre-commit run --all-files

# Run type checking manually (excluded from pre-commit due to generated files)
poetry run mypy --config-file=mypy.ini src/
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_client.py

# Run with coverage
poetry run pytest --cov=offers_sdk

# Run in Docker
docker compose --profile test up
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

- **GitHub Issues**: Create an issue for bugs or feature requests
- **Documentation**: Check the examples and API reference
- **Tests**: Review test files for usage examples

## Development Status

- ✅ **All dependencies are actively used** - no dead code
- ✅ **82 tests passing** - comprehensive test coverage
- ✅ **Modern linting tools** - ruff, isort, black configured
- ✅ **Pre-commit hooks** - automatic code quality checks
- ✅ **Docker containers verified** - all services working
- ✅ **CLI tool functional** - all commands working
- ✅ **Type checking clean** - mypy passes
