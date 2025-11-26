# WHMCS Client Documentation

## Overview

The `WhmcsClient` is a robust Python client for interacting with the WHMCS API. It provides:

- **Authentication**: Secure API authentication with identifier and secret
- **Caching**: 5-minute TTL in-memory caching to reduce redundant API calls
- **Retry Logic**: Automatic retry with exponential backoff for transient failures
- **Error Handling**: Descriptive exceptions for different error scenarios
- **Response Normalization**: Consistent data structures from API responses

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from src import WhmcsClient

# Initialize the client
client = WhmcsClient(
    api_url='https://your-domain.com/includes/api.php',
    api_identifier='your_api_identifier',
    api_secret='your_api_secret'
)

# Test connection
client.test_connection()

# Fetch products
products = client.get_products()

# Get specific product inventory
inventory = client.get_product_inventory(product_id=1)

# Close the client
client.close()
```

## Features

### 1. Authentication

The client authenticates automatically with every request using your API credentials:

```python
client = WhmcsClient(
    api_url='https://your-domain.com/includes/api.php',
    api_identifier='your_api_identifier',
    api_secret='your_api_secret'
)
```

### 2. Caching with TTL

The client implements a 5-minute (configurable) TTL cache to avoid redundant API calls:

```python
# Default 5-minute cache
client = WhmcsClient(..., cache_ttl=300)

# First call hits the API
products = client.get_products()

# Second call uses cache (no API request)
products = client.get_products()

# Bypass cache if needed
products = client.get_products(use_cache=False)

# Clear cache manually
client.clear_cache()
```

### 3. Retry Logic with Exponential Backoff

The client automatically retries failed requests (up to 3 attempts) with exponential backoff:

- **Retried errors**: `WhmcsConnectionError`, `WhmcsTimeoutError`
- **Not retried**: `WhmcsAuthenticationError`, `WhmcsAPIError` (permanent errors)
- **Backoff**: 1s, 2s, 4s, 8s (max 10s)

```python
# Retry happens automatically
try:
    products = client.get_products()
except WhmcsConnectionError:
    # This exception is raised only after all retries are exhausted
    print("Connection failed after 3 retries")
```

### 4. Error Handling

The client provides descriptive exceptions for different error scenarios:

```python
from src import (
    WhmcsAuthenticationError,  # Authentication failures
    WhmcsAPIError,              # API errors
    WhmcsConnectionError,       # Connection failures
    WhmcsTimeoutError,          # Request timeouts
    WhmcsValidationError        # Invalid input
)

try:
    products = client.get_products()
except WhmcsAuthenticationError as e:
    print(f"Auth failed: {e}")
except WhmcsAPIError as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Response: {e.response_data}")
except WhmcsConnectionError as e:
    print(f"Connection failed: {e}")
```

### 5. Response Normalization

API responses are normalized into consistent Python dictionaries:

```python
products = client.get_products()

# Normalized product structure
product = products[0]
print(product['id'])              # int: Product ID
print(product['name'])            # str: Product name
print(product['description'])     # str: Product description
print(product['stock_control'])   # bool: Whether stock control is enabled
print(product['quantity'])        # int: Available quantity
print(product['available'])       # bool: Whether product is available
print(product['pricing'])         # dict: Pricing information
```

## API Reference

### Class: `WhmcsClient`

#### Constructor

```python
WhmcsClient(
    api_url: str,
    api_identifier: str,
    api_secret: str,
    timeout: int = 30,
    cache_ttl: int = 300
)
```

**Parameters:**
- `api_url`: Base URL of the WHMCS API (e.g., `https://example.com/includes/api.php`)
- `api_identifier`: API identifier for authentication
- `api_secret`: API secret for authentication
- `timeout`: Request timeout in seconds (default: 30)
- `cache_ttl`: Cache time-to-live in seconds (default: 300 = 5 minutes)

**Raises:**
- `WhmcsValidationError`: If required parameters are missing or invalid

#### Methods

##### `get_products(use_cache: bool = True, **filters) -> List[Dict[str, Any]]`

Fetch product list from WHMCS.

**Parameters:**
- `use_cache`: Whether to use cached data if available (default: True)
- `**filters`: Additional filters (e.g., `pid=1`, `gid=2`, `module='cpanel'`)

**Returns:** List of normalized product dictionaries

**Raises:**
- `WhmcsAuthenticationError`: If authentication fails
- `WhmcsAPIError`: If API returns an error
- `WhmcsConnectionError`: If connection fails (after retries)
- `WhmcsTimeoutError`: If request times out (after retries)

##### `get_product(product_id: int, use_cache: bool = True) -> Optional[Dict[str, Any]]`

Fetch a specific product by ID.

**Parameters:**
- `product_id`: The product ID to fetch
- `use_cache`: Whether to use cached data if available (default: True)

**Returns:** Normalized product dictionary or None if not found

##### `get_product_inventory(product_id: int, use_cache: bool = True) -> Dict[str, Any]`

Fetch product inventory information.

**Parameters:**
- `product_id`: The product ID to fetch inventory for
- `use_cache`: Whether to use cached data if available (default: True)

**Returns:** Normalized inventory dictionary with stock information

**Raises:**
- `WhmcsAPIError`: If product is not found

##### `test_connection() -> bool`

Test the connection and authentication to WHMCS API.

**Returns:** True if connection and authentication are successful

**Raises:**
- `WhmcsAuthenticationError`: If authentication fails
- `WhmcsConnectionError`: If connection fails
- `WhmcsTimeoutError`: If request times out

##### `clear_cache() -> None`

Clear all cached data.

##### `close() -> None`

Close the HTTP session. Should be called when done using the client.

#### Context Manager

The client can be used as a context manager for automatic cleanup:

```python
with WhmcsClient(...) as client:
    products = client.get_products()
# Client is automatically closed
```

## Exception Hierarchy

```
WhmcsClientError (base exception)
├── WhmcsAuthenticationError
├── WhmcsAPIError
├── WhmcsConnectionError
├── WhmcsTimeoutError
└── WhmcsValidationError
```

## Testing

The client includes comprehensive unit tests covering:
- Cache hits and misses
- Cache expiry
- Retry logic
- Error handling
- Response normalization
- Authentication failures
- Connection errors

Run tests:

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## Examples

### Basic Usage

```python
from src import WhmcsClient

client = WhmcsClient(
    api_url='https://example.com/includes/api.php',
    api_identifier='your_id',
    api_secret='your_secret'
)

# Fetch all products
products = client.get_products()

# Filter by group
products = client.get_products(gid=5)

# Get specific product
product = client.get_product(product_id=10)

# Get inventory
inventory = client.get_product_inventory(product_id=10)

client.close()
```

### With Context Manager

```python
from src import WhmcsClient

with WhmcsClient(...) as client:
    products = client.get_products()
    for product in products:
        print(f"{product['name']}: {product['quantity']} in stock")
```

### Error Handling

```python
from src import (
    WhmcsClient,
    WhmcsAuthenticationError,
    WhmcsConnectionError
)

client = WhmcsClient(...)

try:
    client.test_connection()
    products = client.get_products()
except WhmcsAuthenticationError:
    print("Invalid credentials")
except WhmcsConnectionError:
    print("Cannot connect to WHMCS")
finally:
    client.close()
```

### Custom Cache TTL

```python
# 10-minute cache
client = WhmcsClient(..., cache_ttl=600)

# Disable cache for specific call
products = client.get_products(use_cache=False)

# Clear cache manually
client.clear_cache()
```

## Performance Considerations

1. **Caching**: The 5-minute cache significantly reduces API calls. Adjust `cache_ttl` based on your needs.
2. **Retry Logic**: Failed requests are automatically retried with exponential backoff. Maximum 3 attempts.
3. **Connection Pooling**: The client uses a `requests.Session` for connection pooling and better performance.
4. **Timeouts**: Default 30-second timeout prevents hanging requests. Adjust if needed.

## Best Practices

1. **Use Context Manager**: Always use the context manager or call `close()` when done
2. **Handle Exceptions**: Catch and handle specific exceptions for better error recovery
3. **Cache Management**: Use caching for read-heavy operations, bypass for real-time data
4. **Test Connection**: Call `test_connection()` during initialization to validate credentials
5. **Logging**: Enable logging to debug issues and monitor retry attempts

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('src.whmcs_client')
```
