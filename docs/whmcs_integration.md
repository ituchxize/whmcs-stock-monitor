# WHMCS Integration Guide

## Overview

This guide explains how to integrate the WHMCS Stock Monitor with your WHMCS installation.

## Prerequisites

- WHMCS installation (version 7.0 or higher recommended)
- API access enabled in WHMCS
- Admin access to create API credentials

## Creating API Credentials

1. Log into your WHMCS admin panel
2. Navigate to **Setup > Staff Management > Manage API Credentials**
3. Click **Generate New API Credential**
4. Configure the following settings:
   - **IP Restriction**: Add your monitor server IP (or leave blank for testing)
   - **Role**: Admin (or custom role with product read access)
5. Save and note down the **API Identifier** and **API Secret**

## Configuring the Monitor

Add your WHMCS API credentials to the `.env` file:

```env
WHMCS_API_URL=https://your-whmcs-domain.com/includes/api.php
WHMCS_API_IDENTIFIER=your_api_identifier
WHMCS_API_SECRET=your_api_secret
```

## WHMCS API Endpoints Used

The monitor uses the following WHMCS API actions:

### GetProducts

Retrieves product information and stock levels.

```json
{
  "action": "GetProducts",
  "identifier": "API_IDENTIFIER",
  "secret": "API_SECRET",
  "responsetype": "json"
}
```

### GetProductDetails

Retrieves detailed information about a specific product.

```json
{
  "action": "GetProductDetails",
  "identifier": "API_IDENTIFIER",
  "secret": "API_SECRET",
  "productid": 123,
  "responsetype": "json"
}
```

## Stock Control in WHMCS

To enable stock monitoring:

1. Navigate to **Setup > Products/Services > Products/Services**
2. Edit the product you want to monitor
3. Go to the **Module Settings** tab
4. Enable **Stock Control**
5. Set the **Stock Quantity**

## Product Configuration Options

For products with configurable options (e.g., server plans with different RAM/CPU):

1. Each configuration option can be monitored separately
2. The monitor will track stock levels for each option combination
3. Configure option-specific monitoring in the monitor configuration

## Testing the Integration

After configuration, test the integration:

```bash
# This will be implemented in future iterations
python scripts/test_whmcs_connection.py
```

## Troubleshooting

### Authentication Errors

- Verify API credentials are correct
- Check IP restrictions in WHMCS
- Ensure API access is enabled

### Product Not Found

- Verify product ID exists in WHMCS
- Check product is not archived
- Ensure API credentials have access to product data

### Stock Data Not Updating

- Verify stock control is enabled for the product
- Check monitoring interval configuration
- Review application logs for errors

## Security Considerations

1. **API Credentials**: Store securely in `.env` file, never commit to version control
2. **IP Restrictions**: Use IP restrictions in production
3. **HTTPS**: Always use HTTPS for WHMCS API endpoint
4. **Monitoring**: Regularly audit API access logs in WHMCS

## Rate Limiting

WHMCS has default rate limiting on API calls:

- Respect WHMCS rate limits
- Configure appropriate monitoring intervals
- Implement exponential backoff for failed requests

## Future Enhancements

- Automatic product discovery
- Bulk configuration import
- Real-time webhook integration
- Multi-WHMCS instance support
