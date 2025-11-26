# Setup Guide

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- PostgreSQL (optional, SQLite is used by default)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd whmcs-stock-monitor
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./whmcs_monitor.db
# For PostgreSQL use:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/whmcs_monitor

# WHMCS API Configuration
WHMCS_API_URL=https://your-whmcs-domain.com/includes/api.php
WHMCS_API_IDENTIFIER=your_api_identifier
WHMCS_API_SECRET=your_api_secret

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### 5. Initialize the database

Run the Alembic migrations to create the database schema:

```bash
alembic upgrade head
```

Alternatively, you can use the initialization script:

```bash
python scripts/init_db.py
```

### 6. Run the application

```bash
python -m src.main
```

The API will be available at `http://localhost:8000`

## Database Migrations

This project uses Alembic for database migrations.

### Create a new migration

After modifying models in `src/persistence/models.py`:

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback migrations

```bash
alembic downgrade -1  # Rollback one migration
alembic downgrade <revision_id>  # Rollback to specific revision
```

## API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Health Check

Test the application is running correctly:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "app_name": "WHMCS Stock Monitor",
  "version": "1.0.0",
  "database": "connected"
}
```

## Project Structure

```
.
├── alembic/                 # Database migrations
│   ├── versions/            # Migration scripts
│   └── env.py              # Alembic configuration
├── src/                     # Application source code
│   ├── api/                # API endpoints
│   │   └── health.py       # Health check endpoint
│   ├── core/               # Core configuration
│   │   └── config.py       # Pydantic Settings
│   ├── persistence/        # Database layer
│   │   ├── database.py     # Database setup and session management
│   │   └── models.py       # SQLAlchemy models
│   ├── services/           # Business logic layer
│   └── main.py            # Application entry point
├── scripts/                # Utility scripts
│   └── init_db.py         # Database initialization script
├── alembic.ini            # Alembic configuration file
├── requirements.txt       # Python dependencies
└── .env.example          # Example environment configuration
```

## Database Schema

### MonitorConfig
Stores configuration for products/services to monitor.

**Fields:**
- `id`: Primary key
- `product_id`: WHMCS product ID
- `product_name`: Product name
- `config_option_id`: Optional configuration option ID
- `config_option_name`: Optional configuration option name
- `is_active`: Whether monitoring is active
- `check_interval`: Check interval in seconds
- `notify_on_restock`: Enable restock notifications
- `notify_on_purchase`: Enable purchase notifications
- `notify_on_stock_low`: Enable low stock notifications
- `low_stock_threshold`: Threshold for low stock alerts
- `created_at`, `updated_at`: Timestamps

**Indexes:**
- `idx_product_config`: (product_id, config_option_id)
- `idx_active_configs`: (is_active, product_id)

### StockRecord
Historical record of stock levels.

**Fields:**
- `id`: Primary key
- `monitor_config_id`: Foreign key to MonitorConfig
- `stock_quantity`: Current stock quantity
- `price`: Current price
- `stock_control_enabled`: Whether stock control is enabled in WHMCS
- `is_available`: Product availability
- `change_detected`: Whether a change was detected
- `change_type`: Type of change (restock, purchase, etc.)
- `change_amount`: Amount of change
- `notes`: Additional notes
- `recorded_at`: When the record was created

**Indexes:**
- `idx_monitor_recorded`: (monitor_config_id, recorded_at)
- `idx_change_detection`: (change_detected, change_type)

### NotificationLog
Log of all notifications sent.

**Fields:**
- `id`: Primary key
- `monitor_config_id`: Foreign key to MonitorConfig
- `notification_type`: Type of notification
- `channel`: Notification channel (telegram, etc.)
- `message`: Notification message content
- `status`: Status (pending, sent, failed)
- `sent_at`: When the notification was sent
- `error_message`: Error message if failed
- `retry_count`: Number of retry attempts
- `created_at`: When the log entry was created

**Indexes:**
- `idx_notification_status`: (status, created_at)
- `idx_notification_type_status`: (notification_type, status)

## Development

### Running in debug mode

Set `DEBUG=true` in your `.env` file to enable debug logging and auto-reload.

### Using PostgreSQL

For production use, PostgreSQL is recommended:

1. Create a PostgreSQL database:
```bash
createdb whmcs_monitor
```

2. Update your `.env`:
```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/whmcs_monitor
```

3. Run migrations:
```bash
alembic upgrade head
```

## Troubleshooting

### Database connection errors

- Verify your `DATABASE_URL` in `.env` is correct
- For PostgreSQL, ensure the database exists and credentials are correct
- For SQLite, ensure the directory is writable

### Import errors

- Ensure you're in the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Migration errors

- Check Alembic is properly configured: `alembic current`
- View migration history: `alembic history`
- Reset database (CAUTION - destroys data):
  ```bash
  rm whmcs_monitor.db  # For SQLite
  alembic upgrade head
  ```
