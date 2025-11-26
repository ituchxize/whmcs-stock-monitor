#!/usr/bin/env python3
"""
Example usage of the WhmcsClient.

This demonstrates basic functionality including authentication,
product fetching, inventory checking, and error handling.
"""

import logging
from src import WhmcsClient, WhmcsAuthenticationError, WhmcsAPIError

logging.basicConfig(level=logging.INFO)


def main():
    # Initialize the client
    client = WhmcsClient(
        api_url='https://your-domain.com/includes/api.php',
        api_identifier='your_api_identifier',
        api_secret='your_api_secret',
        cache_ttl=300  # 5 minutes cache
    )
    
    try:
        # Test connection
        print("Testing connection to WHMCS API...")
        if client.test_connection():
            print("✓ Connection successful!")
        
        # Fetch all products (will be cached)
        print("\nFetching all products...")
        products = client.get_products()
        print(f"Found {len(products)} products")
        
        for product in products[:5]:  # Show first 5
            print(f"  - {product['name']} (ID: {product['id']})")
            print(f"    Stock Control: {product['stock_control']}")
            print(f"    Quantity: {product['quantity']}")
        
        # Fetch a specific product
        if products:
            product_id = products[0]['id']
            print(f"\nFetching product {product_id}...")
            product = client.get_product(product_id)
            print(f"Product: {product['name']}")
        
        # Get product inventory
        if products:
            product_id = products[0]['id']
            print(f"\nFetching inventory for product {product_id}...")
            inventory = client.get_product_inventory(product_id)
            print(f"Inventory: {inventory}")
        
        # Second call will use cache (no API request)
        print("\nFetching products again (from cache)...")
        products = client.get_products()
        print(f"Found {len(products)} products (from cache)")
        
        # Clear cache
        print("\nClearing cache...")
        client.clear_cache()
        print("Cache cleared")
        
    except WhmcsAuthenticationError as e:
        print(f"✗ Authentication failed: {e}")
    except WhmcsAPIError as e:
        print(f"✗ API error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    finally:
        client.close()


def context_manager_example():
    """Example using context manager."""
    
    with WhmcsClient(
        api_url='https://your-domain.com/includes/api.php',
        api_identifier='your_api_identifier',
        api_secret='your_api_secret'
    ) as client:
        products = client.get_products()
        print(f"Found {len(products)} products")
    # Client is automatically closed


if __name__ == '__main__':
    main()
