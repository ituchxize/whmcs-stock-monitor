import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import requests
import responses

from src.whmcs_client import WhmcsClient, CacheEntry
from src.exceptions import (
    WhmcsAuthenticationError,
    WhmcsAPIError,
    WhmcsConnectionError,
    WhmcsTimeoutError,
    WhmcsValidationError
)


class TestCacheEntry:
    """Test the CacheEntry class."""
    
    def test_cache_entry_creation(self):
        data = {'test': 'value'}
        entry = CacheEntry(data, 300)
        
        assert entry.data == data
        assert isinstance(entry.expiry, datetime)
        assert not entry.is_expired()
    
    def test_cache_entry_expiry(self):
        data = {'test': 'value'}
        entry = CacheEntry(data, 0)
        time.sleep(0.1)
        
        assert entry.is_expired()
    
    def test_cache_entry_not_expired(self):
        data = {'test': 'value'}
        entry = CacheEntry(data, 300)
        
        assert not entry.is_expired()


class TestWhmcsClientInitialization:
    """Test WHMCS client initialization."""
    
    def test_successful_initialization(self):
        client = WhmcsClient(
            api_url='https://example.com/api.php',
            api_identifier='test_id',
            api_secret='test_secret'
        )
        
        assert client.api_url == 'https://example.com/api.php'
        assert client.api_identifier == 'test_id'
        assert client.api_secret == 'test_secret'
        assert client.timeout == WhmcsClient.DEFAULT_TIMEOUT
        assert client.cache_ttl == WhmcsClient.DEFAULT_CACHE_TTL
        assert isinstance(client._cache, dict)
    
    def test_initialization_with_custom_values(self):
        client = WhmcsClient(
            api_url='https://example.com/api.php',
            api_identifier='test_id',
            api_secret='test_secret',
            timeout=60,
            cache_ttl=600
        )
        
        assert client.timeout == 60
        assert client.cache_ttl == 600
    
    def test_initialization_strips_trailing_slash(self):
        client = WhmcsClient(
            api_url='https://example.com/api.php/',
            api_identifier='test_id',
            api_secret='test_secret'
        )
        
        assert client.api_url == 'https://example.com/api.php'
    
    def test_initialization_missing_api_url(self):
        with pytest.raises(WhmcsValidationError, match="API URL is required"):
            WhmcsClient(
                api_url='',
                api_identifier='test_id',
                api_secret='test_secret'
            )
    
    def test_initialization_missing_api_identifier(self):
        with pytest.raises(WhmcsValidationError, match="API identifier is required"):
            WhmcsClient(
                api_url='https://example.com/api.php',
                api_identifier='',
                api_secret='test_secret'
            )
    
    def test_initialization_missing_api_secret(self):
        with pytest.raises(WhmcsValidationError, match="API secret is required"):
            WhmcsClient(
                api_url='https://example.com/api.php',
                api_identifier='test_id',
                api_secret=''
            )


class TestWhmcsClientCaching:
    """Test caching functionality."""
    
    @pytest.fixture
    def client(self):
        return WhmcsClient(
            api_url='https://example.com/api.php',
            api_identifier='test_id',
            api_secret='test_secret',
            cache_ttl=1
        )
    
    def test_cache_key_generation_without_params(self, client):
        key = client._get_cache_key('GetProducts')
        assert key == 'GetProducts'
    
    def test_cache_key_generation_with_params(self, client):
        key = client._get_cache_key('GetProducts', {'pid': 1, 'gid': 2})
        assert 'GetProducts:' in key
        assert 'pid' in key
        assert 'gid' in key
    
    def test_cache_key_generation_consistent_ordering(self, client):
        key1 = client._get_cache_key('GetProducts', {'pid': 1, 'gid': 2})
        key2 = client._get_cache_key('GetProducts', {'gid': 2, 'pid': 1})
        assert key1 == key2
    
    def test_cache_miss(self, client):
        result = client._get_from_cache('nonexistent_key')
        assert result is None
    
    def test_cache_hit(self, client):
        data = {'test': 'value'}
        cache_key = 'test_key'
        
        client._set_cache(cache_key, data)
        result = client._get_from_cache(cache_key)
        
        assert result == data
    
    def test_cache_expiry(self, client):
        data = {'test': 'value'}
        cache_key = 'test_key'
        
        client._set_cache(cache_key, data)
        time.sleep(1.1)
        result = client._get_from_cache(cache_key)
        
        assert result is None
        assert cache_key not in client._cache
    
    def test_clear_cache(self, client):
        client._set_cache('key1', {'data': 1})
        client._set_cache('key2', {'data': 2})
        
        assert len(client._cache) == 2
        
        client.clear_cache()
        
        assert len(client._cache) == 0
    
    @responses.activate
    def test_cache_used_on_second_request(self, client):
        mock_response = {
            'result': 'success',
            'products': {
                'product': [
                    {
                        'pid': '1',
                        'name': 'Test Product',
                        'gid': '1',
                        'module': 'test',
                        'stockcontrol': '1',
                        'qty': '10',
                        'retired': '0',
                        'order': '0'
                    }
                ]
            }
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        # First call - should hit API
        result1 = client.get_products()
        assert len(responses.calls) == 1
        
        # Second call - should use cache
        result2 = client.get_products()
        assert len(responses.calls) == 1  # No additional API call
        
        assert result1 == result2
    
    @responses.activate
    def test_cache_bypass_when_disabled(self, client):
        mock_response = {
            'result': 'success',
            'products': {
                'product': []
            }
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        # First call with cache
        client.get_products(use_cache=True)
        assert len(responses.calls) == 1
        
        # Second call without cache
        client.get_products(use_cache=False)
        assert len(responses.calls) == 2  # Additional API call made


class TestWhmcsClientRequests:
    """Test API request functionality."""
    
    @pytest.fixture
    def client(self):
        return WhmcsClient(
            api_url='https://example.com/api.php',
            api_identifier='test_id',
            api_secret='test_secret'
        )
    
    def test_build_request_data_basic(self, client):
        data = client._build_request_data('GetProducts')
        
        assert data['identifier'] == 'test_id'
        assert data['secret'] == 'test_secret'
        assert data['action'] == 'GetProducts'
        assert data['responsetype'] == 'json'
    
    def test_build_request_data_with_params(self, client):
        data = client._build_request_data('GetProducts', {'pid': 1, 'gid': 2})
        
        assert data['identifier'] == 'test_id'
        assert data['secret'] == 'test_secret'
        assert data['action'] == 'GetProducts'
        assert data['responsetype'] == 'json'
        assert data['pid'] == 1
        assert data['gid'] == 2
    
    @responses.activate
    def test_successful_request(self, client):
        mock_response = {
            'result': 'success',
            'data': 'test'
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        result = client._make_request('GetProducts')
        
        assert result == mock_response
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_authentication_error(self, client):
        mock_response = {
            'result': 'error',
            'message': 'Authentication Failed: Invalid identifier'
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        with pytest.raises(WhmcsAuthenticationError, match="Authentication failed"):
            client._make_request('GetProducts')
    
    @responses.activate
    def test_api_error(self, client):
        mock_response = {
            'result': 'error',
            'message': 'Product not found'
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        with pytest.raises(WhmcsAPIError, match="WHMCS API error: Product not found"):
            client._make_request('GetProducts')
    
    @responses.activate
    def test_connection_error(self, client):
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            body=requests.exceptions.ConnectionError()
        )
        
        with pytest.raises(WhmcsConnectionError, match="Failed to connect"):
            client._make_request('GetProducts')
    
    @responses.activate
    def test_timeout_error(self, client):
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            body=requests.exceptions.Timeout()
        )
        
        with pytest.raises(WhmcsTimeoutError, match="timed out"):
            client._make_request('GetProducts')
    
    @responses.activate
    def test_http_error(self, client):
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json={'error': 'Server error'},
            status=500
        )
        
        with pytest.raises(WhmcsAPIError, match="HTTP error"):
            client._make_request('GetProducts')
    
    @responses.activate
    def test_invalid_json_response(self, client):
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            body='Not valid JSON',
            status=200
        )
        
        with pytest.raises(WhmcsAPIError, match="Invalid JSON response"):
            client._make_request('GetProducts')


class TestWhmcsClientRetryLogic:
    """Test retry logic with exponential backoff."""
    
    @pytest.fixture
    def client(self):
        return WhmcsClient(
            api_url='https://example.com/api.php',
            api_identifier='test_id',
            api_secret='test_secret',
            timeout=5
        )
    
    @responses.activate
    def test_retry_on_connection_error(self, client):
        # First two attempts fail, third succeeds
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            body=requests.exceptions.ConnectionError()
        )
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            body=requests.exceptions.ConnectionError()
        )
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json={'result': 'success', 'data': 'test'},
            status=200
        )
        
        result = client._make_request('GetProducts')
        
        assert result == {'result': 'success', 'data': 'test'}
        assert len(responses.calls) == 3
    
    @responses.activate
    def test_retry_on_timeout_error(self, client):
        # First attempt fails, second succeeds
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            body=requests.exceptions.Timeout()
        )
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json={'result': 'success', 'data': 'test'},
            status=200
        )
        
        result = client._make_request('GetProducts')
        
        assert result == {'result': 'success', 'data': 'test'}
        assert len(responses.calls) == 2
    
    @responses.activate
    def test_no_retry_on_authentication_error(self, client):
        # Authentication errors should not be retried
        mock_response = {
            'result': 'error',
            'message': 'Authentication Failed: Invalid identifier'
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        with pytest.raises(WhmcsAuthenticationError):
            client._make_request('GetProducts')
        
        # Should only attempt once
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_max_retries_exceeded(self, client):
        # All attempts fail
        for _ in range(WhmcsClient.MAX_RETRIES + 1):
            responses.add(
                responses.POST,
                'https://example.com/api.php',
                body=requests.exceptions.ConnectionError()
            )
        
        with pytest.raises(WhmcsConnectionError):
            client._make_request('GetProducts')
        
        assert len(responses.calls) == WhmcsClient.MAX_RETRIES


class TestWhmcsClientProducts:
    """Test product fetching and normalization."""
    
    @pytest.fixture
    def client(self):
        return WhmcsClient(
            api_url='https://example.com/api.php',
            api_identifier='test_id',
            api_secret='test_secret'
        )
    
    @responses.activate
    def test_get_products_success(self, client):
        mock_response = {
            'result': 'success',
            'products': {
                'product': [
                    {
                        'pid': '1',
                        'name': 'Test Product',
                        'description': 'Test Description',
                        'gid': '1',
                        'module': 'test_module',
                        'stockcontrol': '1',
                        'qty': '10',
                        'retired': '0',
                        'order': '0',
                        'pricing': {
                            'USD': {
                                'monthly': {
                                    'price': '10.00',
                                    'setup': '5.00'
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        products = client.get_products()
        
        assert len(products) == 1
        assert products[0]['id'] == 1
        assert products[0]['name'] == 'Test Product'
        assert products[0]['stock_control'] is True
        assert products[0]['quantity'] == 10
        assert products[0]['available'] is True
    
    @responses.activate
    def test_get_products_with_filters(self, client):
        mock_response = {
            'result': 'success',
            'products': {
                'product': []
            }
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        client.get_products(pid=1, gid=2)
        
        # Verify the request included the filters
        request = responses.calls[0].request
        assert b'pid' in request.body
        assert b'gid' in request.body
    
    @responses.activate
    def test_get_products_empty_response(self, client):
        mock_response = {
            'result': 'success',
            'products': {}
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        products = client.get_products()
        
        assert products == []
    
    @responses.activate
    def test_get_product_by_id(self, client):
        mock_response = {
            'result': 'success',
            'products': {
                'product': [
                    {
                        'pid': '1',
                        'name': 'Test Product',
                        'gid': '1',
                        'module': 'test',
                        'stockcontrol': '0',
                        'qty': '0',
                        'retired': '0',
                        'order': '0'
                    }
                ]
            }
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        product = client.get_product(1)
        
        assert product is not None
        assert product['id'] == 1
        assert product['name'] == 'Test Product'
    
    @responses.activate
    def test_get_product_not_found(self, client):
        mock_response = {
            'result': 'success',
            'products': {
                'product': []
            }
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        product = client.get_product(999)
        
        assert product is None
    
    @responses.activate
    def test_get_product_inventory(self, client):
        mock_response = {
            'result': 'success',
            'products': {
                'product': [
                    {
                        'pid': '1',
                        'name': 'Test Product',
                        'gid': '1',
                        'module': 'test',
                        'stockcontrol': '1',
                        'qty': '25',
                        'retired': '0',
                        'order': '0'
                    }
                ]
            }
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        inventory = client.get_product_inventory(1)
        
        assert inventory['product_id'] == 1
        assert inventory['name'] == 'Test Product'
        assert inventory['stock_control'] is True
        assert inventory['quantity'] == 25
        assert inventory['available'] is True
        assert 'last_updated' in inventory
    
    @responses.activate
    def test_get_product_inventory_not_found(self, client):
        mock_response = {
            'result': 'success',
            'products': {
                'product': []
            }
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        with pytest.raises(WhmcsAPIError, match="Product with ID 999 not found"):
            client.get_product_inventory(999)


class TestWhmcsClientNormalization:
    """Test response normalization."""
    
    @pytest.fixture
    def client(self):
        return WhmcsClient(
            api_url='https://example.com/api.php',
            api_identifier='test_id',
            api_secret='test_secret'
        )
    
    def test_normalize_products_list_response(self, client):
        response = {
            'products': {
                'product': [
                    {
                        'pid': '1',
                        'name': 'Product 1',
                        'gid': '1',
                        'module': 'test',
                        'stockcontrol': '1',
                        'qty': '10',
                        'retired': '0',
                        'order': '1'
                    },
                    {
                        'pid': '2',
                        'name': 'Product 2',
                        'gid': '1',
                        'module': 'test',
                        'stockcontrol': '0',
                        'qty': '0',
                        'retired': '1',
                        'order': '2'
                    }
                ]
            }
        }
        
        products = client._normalize_products_response(response)
        
        assert len(products) == 2
        assert products[0]['id'] == 1
        assert products[0]['stock_control'] is True
        assert products[0]['available'] is True
        assert products[1]['id'] == 2
        assert products[1]['stock_control'] is False
        assert products[1]['available'] is False
    
    def test_normalize_products_single_product(self, client):
        response = {
            'products': {
                'product': {
                    'pid': '1',
                    'name': 'Product 1',
                    'gid': '1',
                    'module': 'test',
                    'stockcontrol': '1',
                    'qty': '10',
                    'retired': '0',
                    'order': '0'
                }
            }
        }
        
        products = client._normalize_products_response(response)
        
        assert len(products) == 1
        assert products[0]['id'] == 1
    
    def test_normalize_products_empty_response(self, client):
        response = {'products': {}}
        
        products = client._normalize_products_response(response)
        
        assert products == []
    
    def test_normalize_pricing(self, client):
        pricing_data = {
            'USD': {
                'monthly': {
                    'price': '10.00',
                    'setup': '5.00'
                },
                'annually': {
                    'price': '100.00',
                    'setup': '0.00'
                }
            },
            'EUR': {
                'monthly': {
                    'price': '9.00',
                    'setup': '4.50'
                }
            }
        }
        
        normalized = client._normalize_pricing(pricing_data)
        
        assert normalized['USD']['monthly']['price'] == 10.0
        assert normalized['USD']['monthly']['setup'] == 5.0
        assert normalized['USD']['annually']['price'] == 100.0
        assert normalized['EUR']['monthly']['price'] == 9.0
    
    def test_normalize_pricing_empty(self, client):
        normalized = client._normalize_pricing({})
        assert normalized == {}


class TestWhmcsClientConnection:
    """Test connection and context manager functionality."""
    
    @responses.activate
    def test_test_connection_success(self):
        client = WhmcsClient(
            api_url='https://example.com/api.php',
            api_identifier='test_id',
            api_secret='test_secret'
        )
        
        mock_response = {
            'result': 'success',
            'products': {}
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        assert client.test_connection() is True
    
    @responses.activate
    def test_test_connection_authentication_failure(self):
        client = WhmcsClient(
            api_url='https://example.com/api.php',
            api_identifier='test_id',
            api_secret='test_secret'
        )
        
        mock_response = {
            'result': 'error',
            'message': 'Authentication Failed'
        }
        
        responses.add(
            responses.POST,
            'https://example.com/api.php',
            json=mock_response,
            status=200
        )
        
        with pytest.raises(WhmcsAuthenticationError):
            client.test_connection()
    
    def test_context_manager(self):
        with WhmcsClient(
            api_url='https://example.com/api.php',
            api_identifier='test_id',
            api_secret='test_secret'
        ) as client:
            assert client is not None
            assert isinstance(client, WhmcsClient)
    
    def test_close_method(self):
        client = WhmcsClient(
            api_url='https://example.com/api.php',
            api_identifier='test_id',
            api_secret='test_secret'
        )
        
        # Should not raise an exception
        client.close()
