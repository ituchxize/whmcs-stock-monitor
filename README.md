# WHMCS Stock Monitor

A third-party monitoring system for WHMCS product inventory with Telegram notifications.

## Features
- Monitor multiple products and configurations
- Detect stock changes (restocking & purchases)
- Real-time Telegram notifications
- RESTful API for configuration management
- Comprehensive history and logging

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment variables (see SETUP.md)
3. Initialize database: `python scripts/init_db.py`
4. Run the service: `python -m src.main`

## Documentation
- [Setup Guide](./SETUP.md)
- [API Documentation](./docs/API.md)
- [WHMCS Integration](./docs/whmcs_integration.md)
- [Telegram Setup](./docs/telegram_setup.md)
