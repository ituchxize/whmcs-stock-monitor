# Monitoring Engine Documentation

## Overview

The Monitoring Engine is an APScheduler-based background worker that periodically scans active product monitors, fetches stock data from WHMCS, detects changes, and emits structured events for downstream handlers.

## Architecture

### Components

#### 1. MonitoringEngine (`src/monitoring_engine.py`)
The core engine responsible for:
- Scanning active `MonitorConfig` entries
- Fetching product inventory from WHMCS API
- Comparing current stock with historical `StockRecord` entries
- Detecting changes and threshold breaches
- Persisting new stock records
- Emitting structured events

#### 2. MonitorScheduler (`src/scheduler.py`)
APScheduler wrapper that:
- Manages the monitoring job lifecycle
- Provides configurable scheduling intervals
- Handles graceful startup and shutdown
- Integrates with FastAPI app lifecycle

#### 3. EventBus (`src/events.py`)
Event system for handling stock changes:
- Publishes structured `StockEvent` objects
- Supports multiple event subscribers
- Event types: stock changes, threshold breaches, errors

#### 4. Database Models (`src/models.py`)
- **MonitorConfig**: Configuration for products to monitor
- **StockRecord**: Historical stock data with deltas

## Configuration

Set via environment variables or `.env` file:

```bash
# Monitoring schedule (seconds between checks)
MONITOR_INTERVAL_SECONDS=300

# Timezone for scheduler
MONITOR_TIMEZONE=UTC

# WHMCS API credentials
WHMCS_API_URL=https://your-whmcs.com/includes/api.php
WHMCS_API_IDENTIFIER=your_identifier
WHMCS_API_SECRET=your_secret
```

## Usage

### Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the FastAPI app (starts scheduler automatically)
python -m src.main
```

### API Endpoints

#### Health Check
```
GET /health
```
Returns scheduler status and next job run times.

#### Trigger Manual Scan
```
POST /monitoring/run-now
```
Immediately triggers a monitoring cycle outside the schedule.

#### Pause/Resume Scheduler
```
POST /scheduler/pause
POST /scheduler/resume
```

## Monitoring Cycle

1. **Fetch Active Monitors**: Query database for `MonitorConfig` entries where `is_active=True`

2. **For Each Monitor**:
   - Fetch current stock from WHMCS API (no cache)
   - Retrieve latest `StockRecord` for comparison
   - Calculate delta (current - previous quantity)
   - Detect change type (restock, purchase, unchanged)
   - Check threshold breaches (low/high)
   - Create new `StockRecord` with delta and metadata
   - Emit appropriate events

3. **Event Emission**:
   - `STOCK_INCREASED`: Stock quantity increased (restock)
   - `STOCK_DECREASED`: Stock quantity decreased (purchase)
   - `THRESHOLD_BREACH_LOW`: Quantity below low threshold
   - `THRESHOLD_BREACH_HIGH`: Quantity above high threshold
   - `MONITOR_ERROR`: Error during monitoring
   - `MONITOR_STARTED/COMPLETED`: Cycle lifecycle

## Change Detection Algorithm

### Delta Calculation
```python
delta = current_quantity - previous_quantity
```

### Change Type Detection
- **initial**: First record for a monitor (no previous data)
- **restock**: Delta > 0 (quantity increased)
- **purchase**: Delta < 0 (quantity decreased)
- **unchanged**: Delta == 0 (no change)

### Threshold Breach Detection
- **Low Threshold**: `current_quantity <= threshold_low`
- **High Threshold**: `current_quantity >= threshold_high`

## Event Handling

Subscribe to events via the EventBus:

```python
from src.events import event_bus, EventType

def my_handler(event: StockEvent):
    print(f"Stock changed: {event.product_name} - Delta: {event.delta}")

event_bus.subscribe(EventType.STOCK_INCREASED, my_handler)
```

Or subscribe to all events:

```python
event_bus.subscribe_all(my_handler)
```

## Database Schema

### MonitorConfig
- `product_id`: WHMCS product ID (unique)
- `is_active`: Enable/disable monitoring
- `threshold_low`: Low stock alert threshold
- `threshold_high`: High stock alert threshold
- `notify_on_restock`: Enable restock notifications
- `notify_on_purchase`: Enable purchase notifications
- `notify_on_threshold`: Enable threshold breach notifications

### StockRecord
- `monitor_config_id`: Foreign key to MonitorConfig
- `quantity`: Current stock quantity
- `delta`: Change from previous record
- `change_type`: Type of change (restock/purchase/unchanged)
- `threshold_breached`: Boolean flag
- `threshold_type`: Which threshold was breached (low/high)
- `created_at`: Timestamp of record

## Graceful Shutdown

The scheduler integrates with FastAPI's lifespan context manager:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown(wait=True)  # Wait for current job to complete
```

This ensures:
- Database is initialized before scheduler starts
- Scheduler shuts down gracefully when app stops
- No orphaned background jobs

## Testing

Run tests with pytest:

```bash
pytest tests/test_monitoring_engine.py -v
pytest tests/test_scheduler.py -v
pytest tests/test_events.py -v
pytest tests/test_models.py -v
```

## Error Handling

- WHMCS API errors are caught per-monitor and logged
- Failed monitors don't stop the cycle from completing
- `MONITOR_ERROR` events are emitted with error details
- Database transactions are rolled back on error

## Performance Considerations

- **Caching**: Monitoring cycle bypasses cache (`use_cache=False`) for accurate data
- **Concurrency**: Scheduler configured with `max_instances=1` to prevent overlap
- **Coalescing**: Missed runs are coalesced to prevent backlog
- **Database**: Indexes on `is_active`, `product_id`, and `created_at` for efficient queries
