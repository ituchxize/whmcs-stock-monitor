# WHMCS Stock Monitor

A third-party monitoring system for WHMCS product inventory with real-time notifications.

## Features
- **Multi-Website Support**: Monitor multiple WHMCS installations from a single instance
- Monitor multiple products and configurations per website
- Detect stock changes (restocking & purchases)
- Threshold-based alerts for low/high stock levels
- Real-time event notifications
- RESTful API for configuration management
- Comprehensive history and logging with SQLModel + Alembic migrations

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment variables (see `.env.example`)
3. Initialize database: `python -m scripts.init_db --sample-data`
4. Run database migrations: `alembic upgrade head`
5. Run the service: `python -m src.main`

## Documentation
- [Multi-Website Schema](./docs/MULTI_WEBSITE_SCHEMA.md)
- [WHMCS Client](./docs/WHMCS_CLIENT.md)
- [Monitoring Engine](./docs/MONITORING_ENGINE.md)
- [Alembic Migrations](./alembic/README)
