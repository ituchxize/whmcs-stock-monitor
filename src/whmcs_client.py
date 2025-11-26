import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from .exceptions import (
    WhmcsAuthenticationError,
    WhmcsAPIError,
    WhmcsConnectionError,
    WhmcsTimeoutError,
    WhmcsValidationError
)

logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a cached entry with expiration time."""
    def __init__(self, data: Any, ttl_seconds: int):
        self.data = data
        self.expiry = datetime.now() + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return datetime.now() > self.expiry


class WhmcsClient:
    """
    A client for interacting with the WHMCS API.
    
    Provides authentication, product inventory fetching, response normalization,
    caching with TTL, and retry logic with exponential backoff.
    """
    
    DEFAULT_TIMEOUT = 30
    DEFAULT_CACHE_TTL = 300  # 5 minutes
    MAX_RETRIES = 3
    
    def __init__(
        self,
        api_url: str,
        api_identifier: str,
        api_secret: str,
        timeout: int = DEFAULT_TIMEOUT,
        cache_ttl: int = DEFAULT_CACHE_TTL
    ):
        """
        Initialize the WHMCS client.
        
        Args:
            api_url: Base URL of the WHMCS API (e.g., https://example.com/includes/api.php)
            api_identifier: API identifier for authentication
            api_secret: API secret for authentication
            timeout: Request timeout in seconds
            cache_ttl: Cache time-to-live in seconds (default: 300 = 5 minutes)
        
        Raises:
            WhmcsValidationError: If required parameters are missing or invalid
        """
        if not api_url:
            raise WhmcsValidationError("API URL is required")
        if not api_identifier:
            raise WhmcsValidationError("API identifier is required")
        if not api_secret:
            raise WhmcsValidationError("API secret is required")
        
        self.api_url = api_url.rstrip('/')
        self.api_identifier = api_identifier
        self.api_secret = api_secret
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        
        self._cache: Dict[str, CacheEntry] = {}
        self._session = requests.Session()
    
    def _get_cache_key(self, action: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate a cache key based on action and parameters."""
        if params:
            sorted_params = sorted(params.items())
            params_str = str(sorted_params)
            return f"{action}:{params_str}"
        return action
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Retrieve data from cache if available and not expired."""
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired():
                logger.debug(f"Cache hit for key: {cache_key}")
                return entry.data
            else:
                logger.debug(f"Cache expired for key: {cache_key}")
                del self._cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, data: Any) -> None:
        """Store data in cache with TTL."""
        self._cache[cache_key] = CacheEntry(data, self.cache_ttl)
        logger.debug(f"Cached data for key: {cache_key}")
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def _build_request_data(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build request data with authentication credentials."""
        data = {
            'identifier': self.api_identifier,
            'secret': self.api_secret,
            'action': action,
            'responsetype': 'json'
        }
        if params:
            data.update(params)
        return data
    
    @retry(
        retry=retry_if_exception_type((WhmcsConnectionError, WhmcsTimeoutError)),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _make_request(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the WHMCS API with retry logic.
        
        Args:
            action: WHMCS API action to perform
            params: Additional parameters for the request
        
        Returns:
            API response as a dictionary
        
        Raises:
            WhmcsAuthenticationError: If authentication fails
            WhmcsAPIError: If API returns an error
            WhmcsConnectionError: If connection fails
            WhmcsTimeoutError: If request times out
        """
        request_data = self._build_request_data(action, params)
        
        try:
            logger.debug(f"Making WHMCS API request: action={action}")
            response = self._session.post(
                self.api_url,
                data=request_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            response_json = response.json()
            
            # Check for WHMCS API errors
            if response_json.get('result') == 'error':
                error_message = response_json.get('message', 'Unknown error')
                
                # Check for authentication errors
                if 'authentication' in error_message.lower() or 'invalid identifier' in error_message.lower():
                    raise WhmcsAuthenticationError(f"Authentication failed: {error_message}")
                
                raise WhmcsAPIError(
                    f"WHMCS API error: {error_message}",
                    status_code=response.status_code,
                    response_data=response_json
                )
            
            return response_json
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout for action {action}: {e}")
            raise WhmcsTimeoutError(f"Request timed out after {self.timeout} seconds") from e
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for action {action}: {e}")
            raise WhmcsConnectionError(f"Failed to connect to WHMCS API: {e}") from e
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for action {action}: {e}")
            raise WhmcsAPIError(
                f"HTTP error: {e}",
                status_code=e.response.status_code if e.response else None
            ) from e
        
        except ValueError as e:
            logger.error(f"Invalid JSON response for action {action}: {e}")
            raise WhmcsAPIError(f"Invalid JSON response: {e}") from e
    
    def get_products(self, use_cache: bool = True, **filters) -> List[Dict[str, Any]]:
        """
        Fetch product list from WHMCS.
        
        Args:
            use_cache: Whether to use cached data if available
            **filters: Additional filters (e.g., pid, gid, module)
        
        Returns:
            List of normalized product dictionaries
        
        Raises:
            WhmcsAuthenticationError: If authentication fails
            WhmcsAPIError: If API returns an error
            WhmcsConnectionError: If connection fails (after retries)
            WhmcsTimeoutError: If request times out (after retries)
        """
        cache_key = self._get_cache_key('GetProducts', filters)
        
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        response = self._make_request('GetProducts', filters)
        products = self._normalize_products_response(response)
        
        if use_cache:
            self._set_cache(cache_key, products)
        
        return products
    
    def get_product(self, product_id: int, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific product by ID.
        
        Args:
            product_id: The product ID to fetch
            use_cache: Whether to use cached data if available
        
        Returns:
            Normalized product dictionary or None if not found
        
        Raises:
            WhmcsAuthenticationError: If authentication fails
            WhmcsAPIError: If API returns an error
            WhmcsConnectionError: If connection fails (after retries)
            WhmcsTimeoutError: If request times out (after retries)
        """
        products = self.get_products(use_cache=use_cache, pid=product_id)
        return products[0] if products else None
    
    def get_product_inventory(self, product_id: int, use_cache: bool = True) -> Dict[str, Any]:
        """
        Fetch product inventory information.
        
        Args:
            product_id: The product ID to fetch inventory for
            use_cache: Whether to use cached data if available
        
        Returns:
            Normalized inventory dictionary with stock information
        
        Raises:
            WhmcsAuthenticationError: If authentication fails
            WhmcsAPIError: If API returns an error
            WhmcsConnectionError: If connection fails (after retries)
            WhmcsTimeoutError: If request times out (after retries)
        """
        product = self.get_product(product_id, use_cache=use_cache)
        
        if not product:
            raise WhmcsAPIError(f"Product with ID {product_id} not found")
        
        return {
            'product_id': product_id,
            'name': product.get('name'),
            'stock_control': product.get('stock_control', False),
            'quantity': product.get('quantity', 0),
            'available': product.get('available', True),
            'last_updated': datetime.now().isoformat()
        }
    
    def _normalize_products_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalize the products response from WHMCS API.
        
        Args:
            response: Raw API response
        
        Returns:
            List of normalized product dictionaries
        """
        products_data = response.get('products', {})
        
        # Handle both dict and list responses
        if isinstance(products_data, dict):
            if 'product' in products_data:
                products_list = products_data['product']
                if isinstance(products_list, dict):
                    products_list = [products_list]
            else:
                products_list = list(products_data.values()) if products_data else []
        elif isinstance(products_data, list):
            products_list = products_data
        else:
            products_list = []
        
        normalized_products = []
        for product in products_list:
            if not isinstance(product, dict):
                continue
            
            normalized = {
                'id': int(product.get('pid', 0)),
                'name': product.get('name', ''),
                'description': product.get('description', ''),
                'group_id': int(product.get('gid', 0)),
                'module': product.get('module', ''),
                'stock_control': product.get('stockcontrol', '0') == '1',
                'quantity': int(product.get('qty', 0)),
                'available': product.get('retired', '0') == '0',
                'pricing': self._normalize_pricing(product.get('pricing', {})),
                'order': int(product.get('order', 0))
            }
            normalized_products.append(normalized)
        
        return normalized_products
    
    def _normalize_pricing(self, pricing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize pricing information.
        
        Args:
            pricing: Raw pricing data from API
        
        Returns:
            Normalized pricing dictionary
        """
        if not pricing:
            return {}
        
        normalized = {}
        for currency, periods in pricing.items():
            if isinstance(periods, dict):
                normalized[currency] = {}
                for period, price_info in periods.items():
                    if isinstance(price_info, dict):
                        normalized[currency][period] = {
                            'price': float(price_info.get('price', 0)),
                            'setup': float(price_info.get('setup', 0))
                        }
        
        return normalized
    
    def test_connection(self) -> bool:
        """
        Test the connection and authentication to WHMCS API.
        
        Returns:
            True if connection and authentication are successful
        
        Raises:
            WhmcsAuthenticationError: If authentication fails
            WhmcsConnectionError: If connection fails
            WhmcsTimeoutError: If request times out
        """
        try:
            # Try a simple API call to verify connection
            self._make_request('GetProducts', {'limitnum': 1})
            logger.info("WHMCS connection test successful")
            return True
        except WhmcsAuthenticationError:
            logger.error("WHMCS authentication failed")
            raise
        except (WhmcsConnectionError, WhmcsTimeoutError):
            logger.error("WHMCS connection test failed")
            raise
    
    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()
        logger.debug("WHMCS client session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
