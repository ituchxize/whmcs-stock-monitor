# Multi-Website Schema Documentation

## Overview

The WHMCS Stock Monitor now supports monitoring multiple WHMCS websites from a single instance. This document describes the database schema and how to work with multiple websites.

## Database Schema

### Websites Table

The `websites` table stores configuration for each WHMCS instance to be monitored.

**Columns:**
- `id` (INTEGER, PRIMARY KEY): Unique identifier for the website
- `name` (VARCHAR(255), INDEXED): Human-readable name for the website
- `website_url` (VARCHAR(500)): Base URL of the WHMCS installation
- `api_identifier` (VARCHAR(255)): WHMCS API identifier for authentication
- `api_secret` (VARCHAR(500)): WHMCS API secret for authentication
- `region` (VARCHAR(100), NULLABLE): Optional region designation (e.g., "US-East", "EU-West")
- `is_active` (BOOLEAN, INDEXED): Whether this website is currently being monitored
- `created_at` (DATETIME): Timestamp when the website was added
- `updated_at` (DATETIME): Timestamp of last update

**Relationships:**
- One-to-many with `monitor_configs`

### Monitor Configs Table

The `monitor_configs` table stores configuration for monitoring specific products on specific websites.

**Columns:**
- `id` (INTEGER, PRIMARY KEY): Unique identifier for the monitor configuration
- `website_id` (INTEGER, FOREIGN KEY, INDEXED): Reference to the website this monitor belongs to
- `product_id` (INTEGER, INDEXED): WHMCS product ID to monitor
- `product_name` (VARCHAR(255), NULLABLE): Cached product name
- `is_active` (BOOLEAN, INDEXED): Whether this monitor is currently active
- `status` (VARCHAR(50)): Current status (e.g., "active", "paused", "error")
- `threshold_low` (INTEGER, NULLABLE): Alert when stock falls below this value
- `threshold_high` (INTEGER, NULLABLE): Alert when stock rises above this value
- `notify_on_restock` (BOOLEAN): Send notifications on stock increases
- `notify_on_purchase` (BOOLEAN): Send notifications on stock decreases
- `notify_on_threshold` (BOOLEAN): Send notifications on threshold breaches
- `purchase_link` (VARCHAR(500), NULLABLE): Custom URL for purchasing this product
- `created_at` (DATETIME): Timestamp when the monitor was created
- `updated_at` (DATETIME): Timestamp of last update
- `last_checked_at` (DATETIME, NULLABLE): Timestamp of last stock check

**Relationships:**
- Many-to-one with `websites`
- One-to-many with `stock_records`
- One-to-many with `monitor_histories`

**Constraints:**
- A combination of `website_id` and `product_id` should be unique (enforced at application level)

### Stock Records Table

The `stock_records` table maintains a historical record of stock levels for each monitored product.

**Columns:**
- `id` (INTEGER, PRIMARY KEY): Unique identifier for the stock record
- `monitor_config_id` (INTEGER, FOREIGN KEY, INDEXED): Reference to the monitor configuration
- `quantity` (INTEGER): Current stock quantity
- `delta` (INTEGER): Change from previous quantity
- `stock_control_enabled` (BOOLEAN): Whether stock control is enabled in WHMCS
- `available` (BOOLEAN): Whether the product is currently available
- `change_type` (VARCHAR(50), NULLABLE): Type of change (e.g., "initial", "restock", "purchase", "unchanged")
- `threshold_breached` (BOOLEAN): Whether a threshold was breached
- `threshold_type` (VARCHAR(20), NULLABLE): Type of threshold breach (e.g., "low", "high")
- `metadata_json` (TEXT, NULLABLE): Additional metadata in JSON format
- `created_at` (DATETIME, INDEXED): Timestamp when the record was created

**Relationships:**
- Many-to-one with `monitor_configs`

**Indexes:**
- Composite index on `(monitor_config_id, created_at)` for efficient historical queries

### Monitor Histories Table

The `monitor_histories` table records significant events and transitions for monitoring activities.

**Columns:**
- `id` (INTEGER, PRIMARY KEY): Unique identifier for the history entry
- `monitor_config_id` (INTEGER, FOREIGN KEY, INDEXED): Reference to the monitor configuration
- `event_type` (VARCHAR(50), INDEXED): Type of event (e.g., "stock_increased", "stock_decreased", "threshold_breach_low")
- `from_quantity` (INTEGER, NULLABLE): Previous quantity before the event
- `to_quantity` (INTEGER): New quantity after the event
- `delta` (INTEGER): Change in quantity
- `change_type` (VARCHAR(50), NULLABLE): Type of change
- `threshold_breached` (BOOLEAN): Whether a threshold was breached
- `threshold_type` (VARCHAR(20), NULLABLE): Type of threshold breach
- `threshold_value` (INTEGER, NULLABLE): The threshold value that was breached
- `message` (VARCHAR(500), NULLABLE): Human-readable message about the event
- `metadata_json` (TEXT, NULLABLE): Additional metadata in JSON format
- `created_at` (DATETIME, INDEXED): Timestamp when the event occurred

**Relationships:**
- Many-to-one with `monitor_configs`

**Indexes:**
- Composite index on `(monitor_config_id, created_at)` for efficient historical queries
- Composite index on `(event_type, created_at)` for filtering by event type

## Multi-Website Workflow

### 1. Adding a Website

```python
from src.services import WebsiteService
from src.database import get_db_context

with get_db_context() as db:
    service = WebsiteService(db)
    website = service.create_website(
        name="Main WHMCS Site",
        website_url="https://billing.example.com",
        api_identifier="YOUR_API_IDENTIFIER",
        api_secret="YOUR_API_SECRET",
        region="US-East"
    )
    print(f"Created website with ID: {website.id}")
```

### 2. Adding Monitor Configurations

```python
from src.services import MonitorConfigService
from src.database import get_db_context

with get_db_context() as db:
    service = MonitorConfigService(db)
    monitor = service.create_monitor(
        website_id=1,  # ID of the website
        product_id=123,  # WHMCS product ID
        product_name="VPS Hosting",
        threshold_low=5,
        threshold_high=50,
        purchase_link="https://billing.example.com/cart.php?a=add&pid=123"
    )
    print(f"Created monitor with ID: {monitor.id}")
```

### 3. Monitoring Multiple Websites

The monitoring engine automatically discovers and monitors all active configurations across all active websites:

```python
from src.monitoring_engine import MonitoringEngine

engine = MonitoringEngine()
results = engine.run_monitoring_cycle()
print(f"Checked {results['monitors_checked']} monitors")
```

### 4. Querying History

```python
from src.services import MonitoringService
from src.database import get_db_context

with get_db_context() as db:
    service = MonitoringService(db)
    
    # Get status summary for a specific monitor
    summary = service.get_status_summary(monitor_id=1)
    print(f"Current quantity: {summary['current_quantity']}")
    
    # Get recent stock history
    history = service.get_stock_history(monitor_id=1, limit=10)
    for record in history:
        print(f"{record.created_at}: Quantity={record.quantity}, Delta={record.delta}")
    
    # Get monitor event history
    events = service.get_monitor_history(monitor_id=1, limit=10)
    for event in events:
        print(f"{event.created_at}: {event.event_type} - {event.message}")
```

## Migration Guide

### From Single Website to Multi-Website

If you're upgrading from a previous version that only supported a single website:

1. **Backup your database** before proceeding

2. **Run the Alembic migration:**
   ```bash
   alembic upgrade head
   ```

3. **Create a website entry** for your existing configuration:
   ```python
   from src.services import WebsiteService
   from src.database import get_db_context
   from src.config import settings
   
   with get_db_context() as db:
       service = WebsiteService(db)
       website = service.create_website(
           name="Main Site",
           website_url=settings.whmcs_api_url,
           api_identifier=settings.whmcs_api_identifier,
           api_secret=settings.whmcs_api_secret
       )
       print(f"Migrated existing site to website ID: {website.id}")
   ```

4. **Update existing monitor configs** to reference the new website:
   ```python
   from src.repositories import MonitorConfigRepository
   from src.database import get_db_context
   
   with get_db_context() as db:
       repo = MonitorConfigRepository(db)
       monitors = repo.get_all_active()
       for monitor in monitors:
           monitor.website_id = 1  # Use the ID from step 3
           repo.update(monitor)
   ```

## Database Management

### Initialize Database

```bash
python -m scripts.init_db
```

### Initialize with Sample Data

```bash
python -m scripts.init_db --sample-data
```

### Reset Database (Drop and Recreate)

```bash
python -m scripts.init_db --drop-existing --sample-data
```

### Create New Migration

After modifying models:

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback Migration

```bash
alembic downgrade -1
```

## API Credentials Security

### Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for sensitive data
3. **Rotate credentials regularly**
4. **Use read-only API credentials** where possible
5. **Monitor API usage** for unusual activity

### Environment Variables

For each website, you can store credentials in `.env`:

```bash
# Main site
WEBSITE_1_NAME="Main Site"
WEBSITE_1_URL="https://billing1.example.com"
WEBSITE_1_API_ID="identifier1"
WEBSITE_1_API_SECRET="secret1"

# Secondary site
WEBSITE_2_NAME="Secondary Site"
WEBSITE_2_URL="https://billing2.example.com"
WEBSITE_2_API_ID="identifier2"
WEBSITE_2_API_SECRET="secret2"
```

## Performance Considerations

### Indexes

The schema includes several indexes for optimal query performance:

- `ix_websites_name`: Quick lookup by website name
- `ix_websites_is_active`: Filter active websites
- `ix_monitor_configs_website_id`: Find monitors by website
- `ix_monitor_configs_product_id`: Find monitors by product
- `idx_stock_records_monitor_created`: Efficient historical queries
- `idx_monitor_histories_config_created`: Efficient event history queries
- `idx_monitor_histories_event_type`: Filter by event type

### Query Optimization

- Use `get_active_by_website()` to fetch only active monitors for a specific website
- Limit historical queries using the `limit` parameter
- Consider archiving old stock records periodically

## Troubleshooting

### Monitor Not Running

1. Check if the website is active: `website.is_active == True`
2. Check if the monitor is active: `monitor.is_active == True`
3. Verify API credentials are correct
4. Check logs for authentication errors

### Missing Historical Data

- The `monitor_histories` table is only populated if you integrate the monitoring engine with the event system
- Ensure events are being captured and written to the database

### Foreign Key Violations

- Always create a `Website` before creating `MonitorConfig` entries
- Use the services layer to ensure proper validation

## Additional Resources

- [WHMCS API Documentation](https://developers.whmcs.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
